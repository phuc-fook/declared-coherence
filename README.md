# Declared Coherence

Declared Coherence is a deterministic Python library for validating explicitly supplied relationships among repository artifacts. It reports duplicate logical identities, derivation cycles, successor-lineage cycles, and declared derivation freshness without reading artifact content or imposing repository policy.

The library is intentionally small and programmatic. It does not crawl repositories, inspect files, parse project configuration, mutate data, assign severity, or decide whether CI should pass.

## Quick example

```python
from declared_coherence import AdapterOutcome, InputUnit, validate

declarations = {
    "artifacts": [
        {
            "artifact_id": "api-contract",
            "repository_locator": "contracts/api.md",
            "lifecycle_state": "current",
            "revision_token": {"kind": "version", "value": "2"},
            "successor_artifact": None,
        },
        {
            "artifact_id": "generated-client",
            "repository_locator": "clients/generated.py",
            "lifecycle_state": "current",
            "revision_token": None,
            "successor_artifact": None,
        },
    ],
    "relations": [
        {
            "relation_kind": "derived_from",
            "from_artifact": "generated-client",
            "to_artifact": "api-contract",
            "observed_source_revision": {"kind": "version", "value": "2"},
        }
    ],
}

outcome = validate((InputUnit("declarations", AdapterOutcome("DECODED_SOURCE", declarations)),))
assert outcome.intake_disposition == "ADMITTED"
assert outcome.result_records[0].freshness_state == "FRESH"
```

The mappings above are already-decoded programmatic input. They are not a YAML or JSON configuration contract.

## Semantics in one minute

- `derived_from` may produce freshness states. `STALE` means the declared observed revision differs from the target's current declared revision; it does not mean the artifact is invalid. `UNKNOWN` means one of those tokens is absent, not that staleness was detected.
- `constrained_by` records declared applicability. Reciprocal constraints are allowed, and the relation does not establish semantic compliance.
- `evidences` is a static declared link. It does not prove truth, sufficiency, independence, or authority.
- `repository_locator` is an optional physical hint. It is not artifact identity and the library performs no filesystem lookup.
- lifecycle values are annotations, not eligibility or policy decisions.

See [API usage](docs/API.md), [relation semantics](docs/SEMANTICS.md), [scope and neighboring models](docs/SCOPE.md), and the [worked examples](examples/declared_relationships.py).

## Supported Python and development

Python 3.11 or newer is required. The product runtime uses only the Python standard library.

POSIX shell:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

## Build reproducibility scope

The local build backend pins archive entry ordering, timestamps, permissions, owners, and wheel creator-system metadata. Consecutive builds from the same source have been verified byte-identical, and the creator-system field is explicitly platform-independent. This candidate does not claim independent replay on every operating system, Python runtime, or ZIP implementation.

This is an alpha product candidate. It has not been published to PyPI, and its public compatibility policy is not yet final.

## License

Apache License 2.0. See [LICENSE](LICENSE).
