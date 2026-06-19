# 01-json — binding document

A minimal `urirun` binding document: URI routes with JSON Schema inputs and
adapter configuration. This is the portable contract the runtime compiles into a
registry.

## Run

```bash
urirun validate bindings.v2.example.json
urirun compile bindings.v2.example.json --out /tmp/registry.json
urirun list /tmp/registry.json
```

Verified: `urirun validate bindings.v2.example.json` → ok.
