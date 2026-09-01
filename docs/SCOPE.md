# Scope and neighboring tools

Declared Coherence is a small static validator for a caller-supplied logical artifact-relation model. It is not a repository service, provenance interchange standard, software bill of materials, governance framework, or general graph platform.

ConformRepo is a separate sibling project concerned with repository structure, structured metadata/schema, and physical or local references. Declared Coherence consumes an explicit logical model instead. Neither project is a mandatory dependency of the other, and this library is not a successor or replacement for ConformRepo.

W3C PROV models interoperable provenance involving entities, activities, and agents. SPDX provides a broad software-package and element relationship vocabulary. S-RAMP and Artificer describe repository models, storage, discovery, querying, and extensibility. Cambium is a governance standard and toolset for maintained knowledge corpora. Declared Coherence does not implement or replace those broader scopes.

