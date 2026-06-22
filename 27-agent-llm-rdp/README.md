# 27 — a real LLM agent drives a computer-control task over tellmesh URIs

Example 26 used a heuristic planner. This one plugs in a **real LLM** (OpenRouter via
liteLLM, configured from `urirun/.env`) and gives it a concrete computer-control goal
over the **real tellmesh URI surface** — `rdp` + `kvm` + `screen` + `ocr` + `llm`
(adopted by `urirun adopt-pack`). It then **records what happened, step by step**, and
judges whether the intention was realized.

```txt
goal ─► urirun action space (20 real tellmesh routes: rdp/kvm/screen/ocr/llm)
     ─► llm_planner.plan(goal, space)  ──(OpenRouter/liteLLM)──►  [{uri, payload, why}]
     ─► each step dry-run under policy (rdp/kvm/screen/ocr/llm allowed)
     ─► generated/run-log.md  +  intention-realized verdict
```

## Run it

```bash
python3 run_task.py                  # uses urirun/.env (OPENROUTER_API_KEY, LLM_MODEL)
GOAL="..." python3 run_task.py       # your own goal
```

If no key is configured it falls back to a deterministic heuristic, so the example
always runs. Steps are **dry-run**: the real tellmesh handlers need the whole monorepo
to execute, but dry-run resolves each URI, validates it, and applies the policy gate —
which is what "did the agent produce a valid, permitted plan for the goal" requires.

## What actually happened (recorded live)

Goal: *"Control the computer over RDP: open the RDP target, take a screenshot of the
remote screen with the kvm connector, OCR the screen text, then decide the next
action."* — planner: **llm** (`openrouter/google/gemini-3.1-flash-image-preview`),
action space: 20 routes.

| # | URI | resolved | permitted | why (LLM's reasoning) |
|---|-----|----------|-----------|-----------------------|
| 0 | `rdp://host1/session/command/prepare-target` | ✓ | ✓ | Open the RDP target to establish a remote session. |
| 1 | `kvm://host1/monitor/0/query/screenshot` | ✓ | ✓ | Take a screenshot of the remote screen using the KVM connector. |
| 2 | `ocr://host1/image/latest/query/text` | ✓ | ✓ | OCR the text from the latest screenshot. |
| 3 | `llm://host1/text/query/decide` | ✓ | ✓ | Decide the next action based on the OCR text and the goal. |

The LLM even threaded the data flow itself — step 3's payload was
`{"context": "$ref:2.text", "goal": "Control the computer over RDP"}`, i.e. it passed
the OCR step's output into the decision step using urirun's `$ref` convention.

**Verdict: YES** — the agent composed a valid, permitted plan covering the whole goal
(rdp ✓, screenshot ✓, ocr ✓, decide ✓; every chosen URI resolved + permitted).

The full record is written to `generated/run-log.md` and `generated/run-log.json`.

## Why this is trustworthy, not a demo prop

- **The agent can only pick real URIs.** The action space comes from adopting actual
  tellmesh manifests; `llm_planner` filters out any URI the model invents that isn't in
  the space, so a hallucinated route can't enter the plan.
- **Every step is policy-gated.** `--allow rdp/kvm/screen/ocr/llm` is the boundary; the
  log records the `permitted` decision per step. A URI outside the allow-set is denied.
- **The record is mechanical.** Coverage (rdp/screenshot/ocr/decide) and
  resolved+permitted are computed from the trace, not asserted by hand — the verdict
  flips to NO if any piece is missing.

## Files

- `llm_planner.py` — `(goal, action_space) -> steps` via liteLLM/OpenRouter, constrained
  to the action space, with a deterministic offline heuristic fallback.
- `run_task.py` — adopt the tellmesh packs → action space → plan → dry-run each step →
  write the run log + verdict.
- `test_agent_llm.py` — offline CI (heuristic path, JSON extraction) + a live test that
  runs only when a key is configured.
