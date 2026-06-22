# 37 — closed-loop task automation (NL → YAML flow → execute → repair)

Three **closed-loop** automation patterns against a urirun node, all over the URI
contract, all with a **pluggable planner** (real LLM / offline heuristic / a test
stub) so the same loops run live or in CI. NL drives the plan; the node's own
results and validation close the loop.

| pattern | loop |
|---------|------|
| **A. self-repair** | NL → plan a flow → execute → on a node error feed that error back to the planner → corrected flow → retry |
| **B. goal-verify** | plan → execute → **probe the node** to check the goal is met → if not, re-plan with the observed state → repeat |
| **C. agent** | observe → planner picks **one** next action → act → repeat until it says *done* (or a step budget) |

Cross-step data flow uses urirun's `<field>_from` convention (no `${...}` templating):
`{text_from: "find_py.result.stdout"}` feeds an earlier step's output into a later
step, resolved by `urirun.node.mesh.resolve_step_payload`.

## Run live (real LLM, real node)

```bash
set -a; . ../.env; set +a            # LLM_MODEL + OPENROUTER_API_KEY
NODE_URL=http://192.168.188.201:8765 python3 run.py
```

Verified live on a node ("laptop", 192.168.188.201):

```
== A. self-repair ==   ok=True in 1 iteration(s)
== B. goal-verify ==   ok=True in 1 iteration(s)
== C. agent ==         ok=True in 2 step(s); reason: OS and top processes captured
session saved: ~/.urirun/laptop/session/closed-loop-<ts>/
```

When the LLM's first plan uses a wrong field, the node answers `'text' is a required
property` and the **self-repair loop feeds that back** so the planner fixes it — the
loop closes through the node's schema validation (demonstrated separately:
`message` → node error → `text` → success).

## Run offline (CI, no LLM, no remote node)

```bash
python3 -m pytest test_closed_loop.py -q     # 5 passed
```

The test spins a **local** urirun node and drives all three loops with deterministic
stub planners — including a forced first-attempt failure that the self-repair loop
corrects, and the `_from` chaining (`which python3` → its stdout logged as a note).

## Files

- `closed_loop.py` — the three loop functions + `execute_flow` (with `_from` chaining).
- `planners.py` — `make_llm_planner` / `make_llm_decider` (litellm) and `heuristic_planner` (offline).
- `run.py` — drive all three live against a node; saves a session under `~/.urirun/<node>/session/`.
- `test_closed_loop.py` — offline CI test (local node + stub planners), 5 cases.

## Why this is "closed"

A one-shot `host ask` plans and runs once. These loops add the **feedback edge**: the
node's error (A), the node's observed state (B), or the running transcript (C) flows
back into the next decision. Combined with the node's schema validation and
`urirun.result_degraded` (surfaced in the trace), the AI corrects itself instead of
emitting a plausible-but-wrong plan and stopping.

See also [`32-host-ask-over-relay`](../32-host-ask-over-relay) (one-shot NL→flow over
the relay) and [`15-llm-yaml-repair`](../15-llm-yaml-repair) (the original repair loop).
