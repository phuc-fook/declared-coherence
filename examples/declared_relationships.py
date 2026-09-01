"""Five neutral examples using only the public API."""

from declared_coherence import AdapterOutcome, InputUnit, validate


def _artifact(artifact_id, *, revision=None, successor=None):
    return {
        "artifact_id": artifact_id,
        "repository_locator": None,
        "lifecycle_state": "current",
        "revision_token": revision,
        "successor_artifact": successor,
    }


def _relation(kind, source, target, *, observed=None):
    return {
        "relation_kind": kind,
        "from_artifact": source,
        "to_artifact": target,
        "observed_source_revision": observed,
    }


def _validate(artifacts, relations):
    decoded = {"artifacts": artifacts, "relations": relations}
    return validate((InputUnit("example", AdapterOutcome("DECODED_SOURCE", decoded)),))


def valid_derivation():
    revision = {"kind": "version", "value": "2"}
    return _validate(
        [_artifact("api-contract", revision=revision), _artifact("generated-client")],
        [_relation("derived_from", "generated-client", "api-contract", observed=revision)],
    )


def stale_derivation():
    return _validate(
        [_artifact("api-contract", revision={"kind": "version", "value": "2"}), _artifact("generated-client")],
        [_relation("derived_from", "generated-client", "api-contract", observed={"kind": "version", "value": "1"})],
    )


def derivation_cycle():
    return _validate(
        [_artifact("schema"), _artifact("generator"), _artifact("client")],
        [
            _relation("derived_from", "schema", "generator"),
            _relation("derived_from", "generator", "client"),
            _relation("derived_from", "client", "schema"),
        ],
    )


def successor_lineage():
    return _validate(
        [_artifact("contract-v1", successor="contract-v2"), _artifact("contract-v2", successor="contract-v3"), _artifact("contract-v3")],
        [],
    )


def reciprocal_constraints():
    return _validate(
        [_artifact("interface-a"), _artifact("interface-b")],
        [
            _relation("constrained_by", "interface-a", "interface-b"),
            _relation("constrained_by", "interface-b", "interface-a"),
        ],
    )


if __name__ == "__main__":
    for example in (valid_derivation, stale_derivation, derivation_cycle, successor_lineage, reciprocal_constraints):
        outcome = example()
        print(example.__name__, outcome.intake_disposition, [(record.code, record.freshness_state) for record in outcome.result_records])

