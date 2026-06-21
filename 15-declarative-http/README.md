# 15 — declarative HTTP/REST connectors (config, not code)

Author a whole connector from a **TOML/JSON spec** — no Python. The runtime
`fetch` adapter resolves the URL from `environments[<target>] + path`, fills
`{placeholder}` slots in url/path/headers/body from the payload, and sends
`query` routes as GET and `command` routes as POST. This is the long-tail
enabler: most integrations are "call an HTTP endpoint with auth and map fields".

## Run (httpbin)

```bash
urirun connectors from-spec httpbin.toml > httpbin.bindings.json
urirun validate httpbin.bindings.json
urirun compile httpbin.bindings.json --out httpbin.registry.json

# {code} fills the path:
urirun run 'httpbin://default/status/query/code' httpbin.registry.json \
  --payload '{"code":418}' --execute --allow 'httpbin://*'        # -> HTTP 418

# body + header templating:
urirun run 'httpbin://default/echo/command/post' httpbin.registry.json \
  --payload '{"name":"world"}' --execute --allow 'httpbin://*'     # body {hello: world}, header X-Demo: ifuri-world
```

## Spec shape

```toml
connector = "httpbin"
scheme = "httpbin"

[environments]
default = "https://httpbin.org"

[[routes]]
uri = "httpbin://default/status/query/code"
method = "GET"
path = "/status/{code}"
required = ["code"]
[routes.input]
code = { type = "integer" }
```

- `uri` containing `{env}` expands to one binding **per environment** (the target
  selects the base URL at runtime). See `ksef.toml`.
- `query` routes default to GET; `command` to POST. Override with `method`.
- `headers`/`body` values are templated from the payload (`Bearer {token}` etc.).

## KSeF 2.0, declaratively (`ksef.toml`)

KSeF is the forcing function: multi-env, `Bearer {token}` auth, `{ref}`/`{ksefNumber}`
path params, templated invoice body. The HTTP surface is **pure config**:

```bash
urirun connectors from-spec ksef.toml | tee ksef.bindings.json | head
urirun validate ksef.bindings.json        # 4 routes x 3 envs = 12, valid
```

The only imperative parts stay as a referenced helper (the §3-4 auth handshake —
challenge → XAdES/token → poll → redeem — and AES-256-CBC + RSAES-OAEP crypto).
Everything else is config — and you don't even write the routes by hand:

```bash
urirun add-openapi https://api-test.ksef.mf.gov.pl/docs/v2/openapi.json \
  --scheme ksef --target test | urirun validate -   # every path × method → a route
```

## Why this matters

One validated, typed, policy-gated contract for every HTTP integration. New
connectors (calendar, CRM, government APIs) become a spec file an LLM or a human
can write, then immediately work in `urirun run`, `urirun agent`, MCP and A2A.
See [`../AUTOMATION-INTEGRATIONS.md`](../AUTOMATION-INTEGRATIONS.md) §5.

## Secrets by reference (`secret://` / `getv://`)

Put a *reference*, never a value, in a header or body — it stays a reference in the
registry/plan and resolves only in `--execute`, behind a deny-by-default policy:

```toml
[routes.headers]
Authorization = "Bearer {getv:KSEF_TOKEN}"        # or {secret:keyring/ksef/{nip}}
```

```bash
export KSEF_TOKEN=...   # value lives in env/keyring, not the binding
urirun run 'ksef://prod/...' reg.json --execute --allow 'ksef://*' \
  --secret-allow 'getv://KSEF_TOKEN'        # without this, the secret is denied
```

The token is injected into the request header at execute time and shows as `****`
in the plan, route table, error store and result.
