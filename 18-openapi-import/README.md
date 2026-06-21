# 18 · OpenAPI → URI routes, secured by reference

Two urirun 0.4 features in one runnable flow: turn an existing REST API into
URI-addressed routes with no handler code, then call one with an auth header that
travels **by reference** — the live request carries the real token, but no
serialized surface ever prints it.

## What it does

1. `urirun add-openapi petstore.json --scheme pet --base-url …` imports the spec
   into declarative `fetch` routes (one per path × method):
   ```
   pet://api/pets/query/get      ->  GET  /pets
   pet://api/pets/command/post   ->  POST /pets
   pet://api/pets/{id}/query/get ->  GET  /pets/{id}
   ```
2. The `GET /pets` route gets an `Authorization: Bearer {getv:PET_TOKEN}` header — a
   **reference**, not the value.
3. `run.py` starts a tiny mock API and calls the route in `--execute` with
   `secretAllow: ["getv://*"]`. The token resolves only at the executor boundary.

## Run

```bash
pip install urirun
PET_TOKEN=demo-key make run
```

```
add-openapi -> 3 routes
run ok: True | status: 200
the mock received: Bearer demo-key          # the real token reached the API
token in the run envelope:  False           # …but never the envelope,
token in the registry:      False           # …never the registry,
registry keeps the {getv:..} reference: True
```

## See also

- [docs.ifuri.com/openapi](https://docs.ifuri.com/openapi.html) — `add-openapi` and
  declarative connectors (`from-spec`).
- [docs.ifuri.com/secrets](https://docs.ifuri.com/secrets.html) and example
  [16-secrets](../16-secrets/) — `secret://` providers, the deny-by-default policy
  and node `--allow-secrets`.
