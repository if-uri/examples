# 02-decorators — Python decorator bindings

`example.py` uses `urirun.v2` decorators (`@uri_command`) to generate URI
bindings and their JSON Schema directly from Python function signatures — no
hand-written schema.

## Run

```bash
python example.py
```

Verified: `python example.py` → prints the generated bindings and a dry-run result.
