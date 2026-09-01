"""Closed immutable value model for declared coherence evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Lifecycle(str, Enum):
    DRAFT = "draft"
    CURRENT = "current"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class RevisionToken:
    kind: str
    value: str


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    repository_locator: str | None
    lifecycle_state: Lifecycle
    revision_token: RevisionToken | None
    successor_artifact: str | None


@dataclass(frozen=True)
class RelationAssertion:
    relation_kind: str
    from_artifact: str
    to_artifact: str
    observed_source_revision: RevisionToken | None


@dataclass(frozen=True)
class StructuralPathSegment:
    kind: str
    value: str | int


@dataclass(frozen=True)
class AdmissionLocus:
    input_unit_key: str
    structural_path: tuple[StructuralPathSegment, ...] = ()


@dataclass(frozen=True)
class AdmissionDefect:
    code: str
    loci: tuple[AdmissionLocus, ...]
    endpoint_role: str | None = None
    referenced_artifact_id: str | None = None
    relation_kind: str | None = None
    from_artifact: str | None = None
    to_artifact: str | None = None


@dataclass(frozen=True)
class AdapterOutcome:
    kind: str
    value: Any = None
    issue_code: str | None = None
    issue_locus: AdmissionLocus | None = None


@dataclass(frozen=True)
class InputUnit:
    input_unit_key: str
    adapter_outcome: AdapterOutcome


@dataclass(frozen=True)
class NormalizedModel:
    artifacts: tuple[ArtifactRecord, ...]
    relations: tuple[RelationAssertion, ...]


@dataclass(frozen=True)
class ResultRecord:
    record_class: str
    code: str
    artifact_ids: tuple[str, ...] = ()
    relation_kind: str | None = None
    witness_path: tuple[str, ...] = ()
    freshness_state: str | None = None
    observed_revision: RevisionToken | None = None
    current_revision: RevisionToken | None = None
    occurrence_count: int | None = None
    admission_defects: tuple[AdmissionDefect, ...] = ()


@dataclass(frozen=True)
class ValidationOutcome:
    admission_stage: str
    intake_disposition: str
    admission_defects: tuple[AdmissionDefect, ...]
    normalized_model: NormalizedModel | None
    result_records: tuple[ResultRecord, ...]
    suppressed_stages: tuple[str, ...]


class InvalidInputUnitKey(ValueError):
    """Raised outside ResultRecord projection for empty or duplicate keys."""


class InvalidInvocation(TypeError):
    """Raised for malformed programmatic objects at the library boundary."""
