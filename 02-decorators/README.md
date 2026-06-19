# 02-decorators — Python decorator bindings

`example.py` uses the public `@urirun.command` decorator to generate URI
bindings and their JSON Schema directly from Python function signatures — no
hand-written schema.

## Run

```bash
python example.py
```

Verified: `python example.py` → prints the generated bindings and a dry-run result.
