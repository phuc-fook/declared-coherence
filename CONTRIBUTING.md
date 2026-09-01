# Contributing

Contributions should preserve the library's narrow scope: deterministic validation of explicitly supplied artifact-relation declarations. Feature proposals for crawling, configuration formats, policy, mutation, plugins, or repository services should begin as separate design discussions rather than implementation patches.

Use Python 3.11 or newer and keep the product runtime standard-library only. Run before submitting a change:

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

Tests should use neutral synthetic data. Avoid machine-specific timing assertions and preserve deterministic structured outputs.
