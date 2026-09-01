# Public API

The minimum top-level API is the `declared_coherence.__all__` list. The validator's internal component classes are not part of that minimum surface.

## Constructing input

`validate()` accepts a complete iterable of `InputUnit` objects. Each unit contains a stable `input_unit_key` and an `AdapterOutcome`.

For decoded declarations, use `AdapterOutcome("DECODED_SOURCE", value)`, where `value` is a mapping with `artifacts` and `relations` lists. Every record uses the explicit fields shown in the README example, including explicit `None` for absent optional values.

For an adapter-level parse failure, use `AdapterOutcome("PARSE_ISSUE", issue_code="DECLARATION_PARSE_FAILURE", issue_locus=...)`. Parse loci identify decoded input units; they must not contain machine paths, usernames, timestamps, or generated presentation ordinals.

`input_unit_key` must be a non-empty string, unique within one invocation, and caller-stable across equivalent invocations. Empty or duplicate keys raise `InvalidInputUnitKey` before semantic evaluation. Other malformed Python invocation objects raise `InvalidInvocation`. Neither exception creates a semantic `ResultRecord`.

## Reading the outcome

`ValidationOutcome.intake_disposition` is `ADMITTED` or `REJECTED`. A rejected input has admission defects and no partial `NormalizedModel`. An admitted input has one immutable normalized model and ordered result records.

Result record classes are:

- `INPUT_ADMISSION_FAILURE`: the declaration could not be admitted.
- `MODEL_CONSTRAINT_FINDING`: duplicate identity or a graph cycle was found.
- `FRESHNESS_STATE`: a `derived_from` assertion was compared with its target revision.
- `TOOL_IMPLEMENTATION_FAILURE`: reserved terminal implementation failure representation.

Explanations and consumer policy are outside the result identity. Callers decide how findings affect their workflow.

## Minimum exports

`validate`, `AdapterOutcome`, `AdmissionDefect`, `AdmissionLocus`, `ArtifactRecord`, `InputUnit`, `InvalidInputUnitKey`, `InvalidInvocation`, `Lifecycle`, `NormalizedModel`, `RelationAssertion`, `ResultRecord`, `RevisionToken`, `StructuralPathSegment`, and `ValidationOutcome`.

