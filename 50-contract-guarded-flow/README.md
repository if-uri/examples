# 50 — contract-guarded flow

**Reuse a urirun connector in a new flow, guarded by its contract.**

When you drop a connector into a new example/flow, how do you know its output still
matches what the rest of the flow expects? You declare a **contract** once and let it
**guard every step**. A connector that silently drifts from its declared shape is caught
at the flow boundary — before any downstream step trusts a bad envelope.

This example is fully self-contained (no external connector install) and shows the whole loop:

```
@conn.handler        →  CONTRACTS (declared truth)  →  conform()  (gate the contract)
   (connector)              urirun_contract.Contract        effect↔verb, examples, reversible
        │                                                          │
        ▼ compile_registry(conn.bindings())                        │
   urirun.run(uri, registry, payload)  ── per step in the flow ────┤
        │  result.value = the connector's envelope                 ▼
        └──────────────────────────────▶  envelope_violation(contract, envelope)
                                              the contract GATE, inside the flow
```

## Run

```bash
make run     # honest connector → every step conforms
make drift   # buggy handler (count:str, no `connector`) → contract CATCHES it
make both    # both, side by side
make test    # pytest: honest passes, drift caught, neutral JSON == in-process contracts
```

Honest run — every step satisfies the contract:

```
flow: notes (honest handler) — contract guards every step
  entry/command/append     -> OK ✓
  entry/command/append     -> OK ✓
  entry/query/list         -> OK ✓
→ honest connector conforms across the flow: YES ✓
```

Drift run — `append` returns a mis-shaped envelope (`count` as a string, no `connector`);
the contract catches it at the flow boundary while the honest `list` step still passes:

```
flow: notes (DRIFT handler) — contract guards every step
  entry/command/append     -> CONTRACT VIOLATION ✗ — out: missing required key 'connector'
  entry/query/list         -> OK ✓
→ drift caught by contract: YES ✓
```

## Why this matters for reuse

- **One declared truth.** The route's `out` shape, effect class and reversibility live in a
  `Contract` (and the neutral [`contracts.json`](contracts.json)). The flow doesn't re-derive
  them — it reads them. See [`../../urirun-contract/`](../../urirun-contract/).
- **Any language.** The same `contracts.json` drives the **JS and Go** envelope guards
  (`urirun-contract/sdk/js`, `sdk/go`) — so a Python connector reused behind a JS or Go flow
  is guarded identically. This example asserts the in-process `CONTRACTS` and `contracts.json`
  declare the same shape.
- **Drift fails loud, not silent.** Without the contract, a connector that changed its output
  would quietly corrupt downstream steps. With it, the flow stops at the first violation with
  a located message (`out: missing required key 'connector'`).

## Reusing urirun in your own example

1. **Author or pip-install a connector** — `conn = urirun.connector("x", scheme="x")`,
   `@conn.handler("noun/verb/action")`. (Or `pip install urirun-connector-<name>`.)
2. **Declare its contract** next to it — `contracts.py` (`CONTRACTS = {...}`) or a neutral
   `contracts.json`. Run `conform()` once; `python -m urirun_contract.contract_scaffold`-style
   scaffolding can bootstrap it from the handler routes.
3. **Build a registry** — `urirun.compile_registry(conn.bindings())`.
4. **Run the flow** — `urirun.run(uri, registry, payload, mode="execute")` per step
   (or `urirun.run_steps(steps, registry)`).
5. **Guard each step** — `envelope_violation(CONTRACTS[route], result["result"]["value"])`.

See the top-level [examples README](../README.md) and
[`docs/generating-connectors.md`](../../docs/generating-connectors.md) for the connector +
contract authoring path.
