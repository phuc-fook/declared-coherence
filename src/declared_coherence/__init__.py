"""Neutral declared-coherence library API."""

from .implementation import validate
from .model import (
    AdapterOutcome, AdmissionDefect, AdmissionLocus, ArtifactRecord, InputUnit,
    InvalidInputUnitKey, InvalidInvocation, Lifecycle, NormalizedModel, RelationAssertion, ResultRecord,
    RevisionToken, StructuralPathSegment, ValidationOutcome,
)

__all__ = [
    "AdapterOutcome", "AdmissionDefect", "AdmissionLocus", "ArtifactRecord",
    "InputUnit", "InvalidInputUnitKey", "InvalidInvocation", "Lifecycle", "NormalizedModel",
    "RelationAssertion", "ResultRecord", "RevisionToken",
    "StructuralPathSegment", "ValidationOutcome", "validate",
]
