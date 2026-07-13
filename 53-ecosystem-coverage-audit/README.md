# 53-ecosystem-coverage-audit

This example treats the if-uri repository inventory as a testable artifact.
It demonstrates how `if-uri/examples` stays aligned with the wider ecosystem:

- `ci/ecosystem-coverage.yml` classifies every known `if-uri/*` repository.
- `scripts/audit_ecosystem_coverage.py` detects new unclassified repositories.
- The audit also detects missing example directories, missing README files and
  example directories that are not mapped to any repository.

## Repositories

- `if-uri/examples`
- `if-uri/urirun`
- all active `if-uri/urirun-connector-*` repositories through the coverage map

## URI scope

This example does not execute a runtime URI route. It covers the catalog layer:
repository -> capability -> example mapping. The mapped examples cover concrete
URI surfaces such as `kvm://`, `human://`, `llm://`, `flow://`, `mesh://`,
`router://`, `contract://`, `sheet://`, `invoice://`, `ksef://` and others.

## Run

```bash
python run.py
python -m pytest -q .
```

`run.py` writes reports to `reports/ecosystem-audit/`.

## CI classification

Class: `host`.

The example is deterministic and offline when given the checked-in coverage map.
The scheduled workflow can additionally fetch the live GitHub organization list.
