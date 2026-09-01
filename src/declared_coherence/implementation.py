"""Minimum implementation of the frozen three-component architecture."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from typing import Iterable

from .model import (
    AdapterOutcome, AdmissionDefect, AdmissionLocus, ArtifactRecord, InputUnit,
    InvalidInputUnitKey, InvalidInvocation, Lifecycle, NormalizedModel, RelationAssertion, ResultRecord,
    RevisionToken, StructuralPathSegment, ValidationOutcome,
)

LIFECYCLES = frozenset({"draft", "current", "deprecated", "archived"})
RELATIONS = ("constrained_by", "derived_from", "evidences")
RELATION_RANK = {value: rank for rank, value in enumerate(RELATIONS)}
ENDPOINT_RANK = {"RELATION_FROM": 0, "RELATION_TO": 1, "SUCCESSOR_TARGET": 2}
CLASS_RANK = {
    "INPUT_ADMISSION_FAILURE": 0, "MODEL_CONSTRAINT_FINDING": 1,
    "FRESHNESS_STATE": 2, "TOOL_IMPLEMENTATION_FAILURE": 3,
}
ADMISSION_RANK = {
    "DECLARATION_PARSE_FAILURE": 0, "DECLARATION_SHAPE_FAILURE": 1,
    "UNRESOLVED_LOGICAL_ENDPOINT": 2, "RELATION_ASSERTION_CONFLICT": 3,
}
MODEL_RANK = {
    "DUPLICATE_ARTIFACT_ID": 0, "DERIVED_FROM_CYCLE": 1,
    "SUCCESSOR_LINEAGE_CYCLE": 2,
}
FRESHNESS_RANK = {"FRESH": 0, "STALE": 1, "UNKNOWN": 2}


def _optional(value):
    return (0,) if value is None else (1, value)


def _token_key(value: RevisionToken | None):
    return (0, "", "") if value is None else (1, value.kind, value.value)


def _segment_key(segment: StructuralPathSegment):
    return (0, segment.value) if segment.kind == "FIELD" else (1, segment.value)


def locus_key(locus: AdmissionLocus):
    return (locus.input_unit_key, tuple(_segment_key(s) for s in locus.structural_path))


def defect_key(defect: AdmissionDefect):
    base = (tuple(locus_key(x) for x in defect.loci),)
    if defect.code in ("DECLARATION_PARSE_FAILURE", "DECLARATION_SHAPE_FAILURE"):
        return base
    if defect.code == "UNRESOLVED_LOGICAL_ENDPOINT":
        return base + (ENDPOINT_RANK[defect.endpoint_role], defect.referenced_artifact_id)
    return base + (RELATION_RANK[defect.relation_kind], defect.from_artifact, defect.to_artifact)


def _artifact_key(a: ArtifactRecord):
    return (
        a.artifact_id, a.lifecycle_state, _optional(a.repository_locator),
        _token_key(a.revision_token), _optional(a.successor_artifact),
    )


def _relation_key(r: RelationAssertion):
    return (RELATION_RANK[r.relation_kind], r.from_artifact, r.to_artifact, _token_key(r.observed_source_revision))


def _field(name: str):
    return StructuralPathSegment("FIELD", name)


def _index(index: int):
    return StructuralPathSegment("INDEX", index)


def _shape_defect(key: str, path: tuple[StructuralPathSegment, ...]):
    return AdmissionDefect("DECLARATION_SHAPE_FAILURE", (AdmissionLocus(key, path),))


def _valid_token_paths(value, prefix):
    if value is None:
        return []
    if not isinstance(value, dict):
        return [prefix]
    defects = []
    if not isinstance(value.get("kind"), str) or not value.get("kind"):
        defects.append(prefix + (_field("kind"),))
    if not isinstance(value.get("value"), str) or not value.get("value"):
        defects.append(prefix + (_field("value"),))
    for extra in set(value) - {"kind", "value"}:
        defects.append(prefix + (_field(str(extra)),))
    return defects


def _token(value):
    return None if value is None else RevisionToken(value["kind"], value["value"])


class IntakeNormalizer:
    """Stage-gated admission and immutable normalization only."""

    def normalize(self, input_units: Iterable[InputUnit]):
        units = tuple(input_units)
        keys = [unit.input_unit_key for unit in units]
        if any(not isinstance(key, str) or not key for key in keys):
            raise InvalidInputUnitKey("input_unit_key must be a non-empty exact string")
        if len(set(keys)) != len(keys):
            raise InvalidInputUnitKey("input_unit_key must be unique within one invocation")

        parse = []
        for unit in units:
            if unit.adapter_outcome.kind == "PARSE_ISSUE":
                locus = unit.adapter_outcome.issue_locus or AdmissionLocus(unit.input_unit_key)
                parse.append(AdmissionDefect("DECLARATION_PARSE_FAILURE", (locus,)))
        if parse:
            return self._rejected("PARSE", parse, ("SHAPE", "LOGICAL_ASSEMBLY", "NORMALIZE_AND_FREEZE"))

        shape = []
        for unit in units:
            outcome = unit.adapter_outcome
            if outcome.kind != "DECODED_SOURCE" or not isinstance(outcome.value, dict):
                shape.append(_shape_defect(unit.input_unit_key, ()))
                continue
            source = outcome.value
            for extra in set(source) - {"artifacts", "relations"}:
                shape.append(_shape_defect(unit.input_unit_key, (_field(str(extra)),)))
            for collection in ("artifacts", "relations"):
                if not isinstance(source.get(collection), list):
                    shape.append(_shape_defect(unit.input_unit_key, (_field(collection),)))
            if not isinstance(source.get("artifacts"), list) or not isinstance(source.get("relations"), list):
                continue
            for i, artifact in enumerate(source["artifacts"]):
                base = (_field("artifacts"), _index(i))
                if not isinstance(artifact, dict):
                    shape.append(_shape_defect(unit.input_unit_key, base)); continue
                artifact_fields = {"artifact_id", "repository_locator", "lifecycle_state", "revision_token", "successor_artifact"}
                for missing in artifact_fields - set(artifact):
                    shape.append(_shape_defect(unit.input_unit_key, base + (_field(missing),)))
                for extra in set(artifact) - artifact_fields:
                    shape.append(_shape_defect(unit.input_unit_key, base + (_field(str(extra)),)))
                checks = {
                    "artifact_id": isinstance(artifact.get("artifact_id"), str) and bool(artifact.get("artifact_id")),
                    "repository_locator": artifact.get("repository_locator") is None or isinstance(artifact.get("repository_locator"), str),
                    "lifecycle_state": isinstance(artifact.get("lifecycle_state"), str) and artifact.get("lifecycle_state") in LIFECYCLES,
                    "successor_artifact": artifact.get("successor_artifact") is None or (isinstance(artifact.get("successor_artifact"), str) and bool(artifact.get("successor_artifact"))),
                }
                for name, valid in checks.items():
                    if not valid: shape.append(_shape_defect(unit.input_unit_key, base + (_field(name),)))
                for path in _valid_token_paths(artifact.get("revision_token"), base + (_field("revision_token"),)):
                    shape.append(_shape_defect(unit.input_unit_key, path))
            for i, relation in enumerate(source["relations"]):
                base = (_field("relations"), _index(i))
                if not isinstance(relation, dict):
                    shape.append(_shape_defect(unit.input_unit_key, base)); continue
                relation_fields = {"relation_kind", "from_artifact", "to_artifact", "observed_source_revision"}
                for missing in relation_fields - set(relation):
                    shape.append(_shape_defect(unit.input_unit_key, base + (_field(missing),)))
                for extra in set(relation) - relation_fields:
                    shape.append(_shape_defect(unit.input_unit_key, base + (_field(str(extra)),)))
                checks = {
                    "relation_kind": relation.get("relation_kind") in RELATIONS,
                    "from_artifact": isinstance(relation.get("from_artifact"), str) and bool(relation.get("from_artifact")),
                    "to_artifact": isinstance(relation.get("to_artifact"), str) and bool(relation.get("to_artifact")),
                }
                for name, valid in checks.items():
                    if not valid: shape.append(_shape_defect(unit.input_unit_key, base + (_field(name),)))
                observed = relation.get("observed_source_revision")
                if relation.get("relation_kind") != "derived_from" and observed is not None:
                    shape.append(_shape_defect(unit.input_unit_key, base + (_field("observed_source_revision"),)))
                else:
                    for path in _valid_token_paths(observed, base + (_field("observed_source_revision"),)):
                        shape.append(_shape_defect(unit.input_unit_key, path))
        if shape:
            return self._rejected("SHAPE", shape, ("LOGICAL_ASSEMBLY", "NORMALIZE_AND_FREEZE"))

        artifacts_with_loci = []
        relations_with_loci = []
        for unit in units:
            source = unit.adapter_outcome.value
            for i, raw in enumerate(source["artifacts"]):
                artifact = ArtifactRecord(raw["artifact_id"], raw["repository_locator"], Lifecycle(raw["lifecycle_state"]), _token(raw["revision_token"]), raw["successor_artifact"])
                artifacts_with_loci.append((artifact, AdmissionLocus(unit.input_unit_key, (_field("artifacts"), _index(i)))))
            for i, raw in enumerate(source["relations"]):
                relation = RelationAssertion(raw["relation_kind"], raw["from_artifact"], raw["to_artifact"], _token(raw["observed_source_revision"]))
                relations_with_loci.append((relation, AdmissionLocus(unit.input_unit_key, (_field("relations"), _index(i)))))

        ids = {artifact.artifact_id for artifact, _ in artifacts_with_loci}
        logical = []
        for artifact, locus in artifacts_with_loci:
            if artifact.successor_artifact is not None and artifact.successor_artifact not in ids:
                logical.append(AdmissionDefect(
                    "UNRESOLVED_LOGICAL_ENDPOINT",
                    (replace(locus, structural_path=locus.structural_path + (_field("successor_artifact"),)),),
                    "SUCCESSOR_TARGET", artifact.successor_artifact,
                ))
        for relation, locus in relations_with_loci:
            for name, role, ref in (("from_artifact", "RELATION_FROM", relation.from_artifact), ("to_artifact", "RELATION_TO", relation.to_artifact)):
                if ref not in ids:
                    logical.append(AdmissionDefect(
                        "UNRESOLVED_LOGICAL_ENDPOINT",
                        (replace(locus, structural_path=locus.structural_path + (_field(name),)),),
                        role, ref, relation.relation_kind, relation.from_artifact, relation.to_artifact,
                    ))

        groups = defaultdict(list)
        for relation, locus in relations_with_loci:
            groups[(relation.relation_kind, relation.from_artifact, relation.to_artifact)].append((relation, locus))
        for (kind, source, target), entries in groups.items():
            if len({entry[0].observed_source_revision for entry in entries}) > 1:
                loci = tuple(sorted({entry[1] for entry in entries}, key=locus_key))
                logical.append(AdmissionDefect("RELATION_ASSERTION_CONFLICT", loci, relation_kind=kind, from_artifact=source, to_artifact=target))
        if logical:
            codes = {d.code for d in logical}
            return self._rejected("LOGICAL_ASSEMBLY", logical, ("NORMALIZE_AND_FREEZE",), codes)

        model = NormalizedModel(
            tuple(sorted((a for a, _ in artifacts_with_loci), key=_artifact_key)),
            tuple(sorted({r for r, _ in relations_with_loci}, key=_relation_key)),
        )
        return (model, (), "NORMALIZE_AND_FREEZE", "ADMITTED", ())

    @staticmethod
    def _rejected(stage, defects, suppressed, codes=None):
        ordered = tuple(sorted(set(defects), key=lambda d: (ADMISSION_RANK[d.code], defect_key(d))))
        return (None, ordered, stage, "REJECTED", suppressed)


def _strongly_connected(nodes, adjacency):
    """Iterative deterministic Kosaraju traversal with no recursion-depth coupling."""
    ordered_adjacency = {node: tuple(sorted(adjacency.get(node, ()))) for node in nodes}
    visited = set()
    finish_order = []
    for root in sorted(nodes):
        if root in visited:
            continue
        visited.add(root)
        stack = [(root, 0)]
        while stack:
            node, offset = stack[-1]
            neighbors = ordered_adjacency[node]
            if offset < len(neighbors):
                nxt = neighbors[offset]
                stack[-1] = (node, offset + 1)
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append((nxt, 0))
            else:
                finish_order.append(node)
                stack.pop()

    reverse = {node: [] for node in nodes}
    for source, targets in ordered_adjacency.items():
        for target in targets:
            reverse[target].append(source)
    for targets in reverse.values():
        targets.sort(reverse=True)

    visited.clear()
    result = []
    for root in reversed(finish_order):
        if root in visited:
            continue
        visited.add(root)
        component = []
        stack = [root]
        while stack:
            node = stack.pop()
            component.append(node)
            for nxt in reverse[node]:
                if nxt not in visited:
                    visited.add(nxt)
                    stack.append(nxt)
        result.append(tuple(sorted(component)))
    return result


def _canonical_cycle(component, adjacency):
    """Select the lexicographically smallest simple closed cycle without enumeration."""
    members = set(component)
    start = min(component)
    reverse = {node: set() for node in members}
    for source in members:
        for target in adjacency.get(source, ()):
            if target in members:
                reverse[target].add(source)

    path = [start]
    visited = {start}
    current = start
    while True:
        allowed = members - visited
        allowed.add(start)
        reachable = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for predecessor in reverse[node]:
                if predecessor in allowed and predecessor not in reachable:
                    reachable.add(predecessor)
                    stack.append(predecessor)
        feasible = [
            nxt for nxt in sorted(adjacency.get(current, ()))
            if nxt == start or (nxt not in visited and nxt in reachable)
        ]
        if not feasible:
            raise RuntimeError("cyclic SCC has no canonical closed witness")
        chosen = feasible[0]
        path.append(chosen)
        if chosen == start:
            return tuple(path)
        visited.add(chosen)
        current = chosen


def _validate_invocation(input_units):
    try:
        units = tuple(input_units)
    except TypeError as exc:
        raise InvalidInvocation("input_units must be an iterable of InputUnit values") from exc
    if any(not isinstance(unit, InputUnit) for unit in units):
        raise InvalidInvocation("every invocation member must be an InputUnit")
    keys = [unit.input_unit_key for unit in units]
    if any(not isinstance(key, str) or not key for key in keys):
        raise InvalidInputUnitKey("input_unit_key must be a non-empty exact string")
    if len(set(keys)) != len(keys):
        raise InvalidInputUnitKey("input_unit_key must be unique within one invocation")
    for unit in units:
        outcome = unit.adapter_outcome
        if not isinstance(outcome, AdapterOutcome):
            raise InvalidInvocation("adapter_outcome must be an AdapterOutcome")
        if outcome.kind not in {"DECODED_SOURCE", "PARSE_ISSUE"}:
            raise InvalidInvocation("AdapterOutcome.kind is outside the closed interface")
        if outcome.kind == "PARSE_ISSUE":
            if outcome.issue_code != "DECLARATION_PARSE_FAILURE" or not isinstance(outcome.issue_locus, AdmissionLocus):
                raise InvalidInvocation("PARSE_ISSUE requires its closed code and AdmissionLocus")
            locus = outcome.issue_locus
            if locus.input_unit_key != unit.input_unit_key or not isinstance(locus.structural_path, tuple):
                raise InvalidInvocation("PARSE_ISSUE locus must belong to its input unit")
            for segment in locus.structural_path:
                if not isinstance(segment, StructuralPathSegment):
                    raise InvalidInvocation("locus path members must be StructuralPathSegment values")
                if segment.kind == "FIELD":
                    valid = isinstance(segment.value, str)
                elif segment.kind == "INDEX":
                    valid = isinstance(segment.value, int) and not isinstance(segment.value, bool) and segment.value >= 0
                else:
                    valid = False
                if not valid:
                    raise InvalidInvocation("locus segment violates the closed FIELD/INDEX interface")
        elif outcome.issue_code is not None or outcome.issue_locus is not None:
            raise InvalidInvocation("DECODED_SOURCE cannot carry parse-issue fields")
    return units


class CoreEvaluator:
    """Evaluate only the four frozen graph-native responsibilities."""

    def evaluate(self, model: NormalizedModel):
        records = []
        counts = Counter(a.artifact_id for a in model.artifacts)
        for artifact_id in sorted(k for k, count in counts.items() if count > 1):
            records.append(ResultRecord("MODEL_CONSTRAINT_FINDING", "DUPLICATE_ARTIFACT_ID", (artifact_id,), occurrence_count=counts[artifact_id]))
        nodes = set(counts)
        self._cycles(records, nodes, ((r.from_artifact, r.to_artifact) for r in model.relations if r.relation_kind == "derived_from"), "DERIVED_FROM_CYCLE", "derived_from")
        self._cycles(records, nodes, ((a.artifact_id, a.successor_artifact) for a in model.artifacts if a.successor_artifact is not None), "SUCCESSOR_LINEAGE_CYCLE", None)
        by_id = defaultdict(list)
        for artifact in model.artifacts: by_id[artifact.artifact_id].append(artifact)
        for relation in model.relations:
            if relation.relation_kind != "derived_from" or len(by_id[relation.to_artifact]) != 1: continue
            current = by_id[relation.to_artifact][0].revision_token
            observed = relation.observed_source_revision
            state = "UNKNOWN" if observed is None or current is None else ("FRESH" if observed == current else "STALE")
            records.append(ResultRecord("FRESHNESS_STATE", "DERIVATION_FRESHNESS", (relation.from_artifact, relation.to_artifact), "derived_from", freshness_state=state, observed_revision=observed, current_revision=current))
        return tuple(records)

    @staticmethod
    def _cycles(records, nodes, edges, code, relation_kind):
        adjacency = defaultdict(set)
        for source, target in edges: adjacency[source].add(target)
        cyclic = [c for c in _strongly_connected(nodes, adjacency) if len(c) > 1 or c[0] in adjacency.get(c[0], ())]
        for component in sorted(cyclic, key=lambda c: c[0]):
            records.append(ResultRecord("MODEL_CONSTRAINT_FINDING", code, component, relation_kind, _canonical_cycle(component, adjacency)))


class DeterministicResultProjector:
    """Aggregate admission defects and apply the frozen total order."""

    def project(self, records: Iterable[ResultRecord] = (), defects: Iterable[AdmissionDefect] = ()):
        combined = list(records)
        grouped = defaultdict(set)
        for defect in defects: grouped[defect.code].add(defect)
        for code, values in grouped.items():
            ordered = tuple(sorted(values, key=defect_key))
            combined.append(ResultRecord("INPUT_ADMISSION_FAILURE", code, occurrence_count=len(ordered), admission_defects=ordered))
        return tuple(sorted(set(combined), key=self._key))

    @staticmethod
    def _key(record: ResultRecord):
        rank = CLASS_RANK[record.record_class]
        if record.record_class == "INPUT_ADMISSION_FAILURE":
            return (rank, ADMISSION_RANK[record.code], tuple(defect_key(d) for d in record.admission_defects), record.occurrence_count)
        if record.record_class == "MODEL_CONSTRAINT_FINDING":
            return (rank, MODEL_RANK[record.code], record.artifact_ids, _optional(record.relation_kind), record.witness_path, _optional(record.occurrence_count))
        if record.record_class == "FRESHNESS_STATE":
            return (rank, record.artifact_ids[0], record.artifact_ids[1], RELATION_RANK[record.relation_kind], FRESHNESS_RANK[record.freshness_state], _token_key(record.observed_revision), _token_key(record.current_revision))
        return (rank, record.code)


def validate(input_units: Iterable[InputUnit]) -> ValidationOutcome:
    """Validate one complete set of already-adapted input outcomes."""
    units = _validate_invocation(input_units)
    model, defects, stage, disposition, suppressed = IntakeNormalizer().normalize(units)
    raw = () if model is None else CoreEvaluator().evaluate(model)
    results = DeterministicResultProjector().project(raw, defects)
    return ValidationOutcome(stage, disposition, defects, model, results, suppressed)
