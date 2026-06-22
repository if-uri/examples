# 23 — embedded URIRUN layer

Every other example installs a **connector** to add routes. This one shows the
routes urirun carries *by itself* — the embedded layer that resolves with **no
connector installed and no registry file**. The runtime answers them directly:

| Scheme        | Adapter             | Routes                                                            | What it gives you            |
|---------------|---------------------|------------------------------------------------------------------|------------------------------|
| `registry://` | `registry-introspect` | `registry://local/routes/query/list`, `registry://local/bindings/query/show` | the runtime describing itself |
| `error://`    | `error-store`       | `error://local/errors/query`, `error://local/errors/command`, `error://local/<code>/query/info` | the addressable error store   |

Both are *resolver builtins* (`_builtin_registry_route_entry` /
`_builtin_error_route_entry` in `runtime/v2.py`): when a `registry://` or
`error://` URI is not in the registry, the runtime mounts it automatically. So
the introspection and observability surface uses the **same URI contract** an
LLM/MCP/A2A client already speaks.

> `log://` (runtime logs) is often grouped with these, but it lives in the
> **host layer** and needs host setup, so it is intentionally left out of this
> zero-config demo.

## Run

```bash
./demo.sh
```

Requires **urirun ≥ 0.4.4** (the `registry://` builtin and zero-config `run`).
Override the binary if needed:

```bash
URIRUN="python3 -m urirun.v2" ./demo.sh
```

What it does, all without a connector or a compiled registry:

1. `registry://local/routes/query/list` — list every live route in the runtime.
2. same route, filtered locally — show just the embedded `registry://`/`error://` layer.
3. `registry://local/bindings/query/show` — inspect one binding's full contract.
4. `error://local/errors/query` — query the runtime error store.

## Why this matters

The runtime is **self-describing and self-observing over URIs**. You do not need
a special API to ask "what can I run?" (`registry://`) or "what went wrong?"
(`error://`) — they are routes like any other, discoverable in `urirun list` and
runnable with `urirun run`. Any failed `run` is recorded with a stable
`error://local/<code>/query/info` address you can look up later.

See also: [`13-simple_defaults`](../13-simple_defaults) for the connector
*authoring* side (declaring your own routes).
