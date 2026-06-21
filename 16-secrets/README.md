# 16 — secrets by reference (`secret://` / `getv://`)

Credentials addressed by **reference, never value**. A URI/binding carries
`secret://keyring/svc/acct` or `getv://NAME`; the value is resolved **only in
`--execute`**, behind a **deny-by-default** policy, injected into the request at
the executor boundary, and shown as `****` on every serialized surface (registry,
plan, route table, error store, result).

```bash
python3 secret_demo.py
```

It starts a tiny local server that validates a Bearer token **without echoing it**,
then proves all the invariants:

```
registry holds only the reference (no value)   : True
dry-run does not resolve / leak the secret      : True
execute WITHOUT --secret-allow is denied        : True
execute WITH --secret-allow runs, auth valid    : True / True
the token never appears in the result           : True
```

## How it maps to the CLI

```bash
urirun connectors from-spec connector.toml | urirun compile - --out reg.json
# header in the spec:  Authorization = "Bearer {getv:DEMO_TOKEN}"

export DEMO_TOKEN=...                                   # value in env/keyring, not the binding
urirun run 'sdemo://local/auth/command/call' reg.json --execute \
  --allow 'sdemo://*' --secret-allow 'getv://DEMO_TOKEN'   # without --secret-allow: denied
```

`secret://keyring/<svc>/<acct>` (OS credential store), `secret://dotenv/<path>#NAME`
and `getv://NAME` are supported; `vault`/`oauth`/`browser` are reserved. A remote
`urirun node serve` resolves **no** secrets unless started with `--allow-secrets`.

## Test

```bash
pytest test_secret_example.py -q
```
