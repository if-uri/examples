# 03-artifacts — scan project artifacts

Shows the `urirun` scanner turning existing artifacts into URI bindings:
`Dockerfile` labels, `Makefile` targets, `package.json`, `pyproject.toml` and an
explicit `urirun.manifest.json`.

## Run

```bash
urirun scan . --out /tmp/bindings.json --registry-out /tmp/registry.json
urirun list /tmp/registry.json
```

Verified: `urirun scan .` → compiles bindings from the artifacts in this folder.
