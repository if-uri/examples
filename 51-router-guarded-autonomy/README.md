# 51 — router-guarded autonomy

**The autonomy safety stack: DECIDE → ROUTE → EXECUTE → GUARD.**

An autonomous agent turns a goal into a plan of URI actions. Before any action runs, two
pre-flight gates make the autonomy safe and legible:

```
goal ──(agent decides)──▶ [ uri, uri, uri ]
                               │
   GATE 1  router://  ─────────┤  WHERE does each step run? (host vs node)
                               │  unroutable step → ABORT the whole plan, before acting
                               ▼
   GATE 2  contract   ── executes routable steps, validates each envelope (shape)
```

1. **Router** ([`urirun-connector-router`](../../urirun-connector-router/)) diagnoses, per step,
   *where it runs* — host or a named node — and **blocks the plan** if any step targets something
   not in the mesh. The agent never acts against a target that does not exist.
2. **Contract** ([`urirun-contract`](../../urirun-contract/)) validates each executed step's envelope,
   so a drifted handler is caught at the boundary (see [example 50](../50-contract-guarded-flow/)).

Fully offline and deterministic (the agent decider is a fixed map here; swap for a live LLM as in
[example 37](../37-closed-loop-automation/)).

## Run

```bash
make run     # routable plan: router pins every step to 'host', executes, contract OK
make rogue   # agent picks a node NOT in the mesh → router blocks the plan pre-flight
make both
make test    # pytest: routable runs+conforms, rogue blocked before execution
```

Routable plan — the router pins every action's location, then steps execute under contract:

```
router pre-flight — WHERE each action runs:
  audit://host/sys/query/info   -> host
  audit://host/proc/query/top   -> host
executing + contract guard:
  audit://host/sys/query/info   -> OK ✓
  audit://host/proc/query/top   -> OK ✓
→ violations: 0
```

Rogue plan — the agent decided a step on `ghost` (not in the mesh); the router refuses it **before**
any action runs:

```
router pre-flight — WHERE each action runs:
  kvm://ghost/screen/query/capture -> ??  ✗ BLOCKED at 'target'
→ plan NOT routable — ABORT before acting ✓
```

## Why this matters

Autonomous agents fail dangerously when they act before knowing *where* an action lands or *what
shape* it returns. The router answers **where** (and stops doomed plans pre-flight); the contract
answers **shape** (and stops drift at the boundary). Together they turn "the model decided to do
something" into "the model's plan was checked for location and shape before and during execution."
