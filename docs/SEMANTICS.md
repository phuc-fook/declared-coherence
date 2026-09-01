# Declared relation semantics

Declared Coherence validates a closed model with three relation kinds.

## `derived_from`

A directed derivation assertion may include the source revision observed when the declaring artifact was produced. If both observed and current target revision tokens exist, exact equality yields `FRESH` and inequality yields `STALE`. If either token is absent, the state is `UNKNOWN`.

`STALE` is not an invalidity judgment. `UNKNOWN` is not equivalent to `STALE`. Tokens are opaque exact pairs; the library does not parse version numbers or inspect content.

## `constrained_by`

A static declared applicability relationship. Reciprocal declarations are valid because this relation is not an authority DAG. The relationship does not demonstrate compliance with the referenced constraint.

## `evidences`

A static declared evidence-about relationship. It does not prove truth, sufficiency, independence, authenticity, or authority.

## Artifact identity and lifecycle

`artifact_id` is the stable logical identity. `repository_locator` is optional location information and is not identity. Moving a file therefore need not change `artifact_id`, and the library performs no filesystem lookup.

Lifecycle values (`draft`, `current`, `deprecated`, and `archived`) are descriptive annotations. The validator does not infer eligibility, authority, retention, or release policy from them.

