# 26 — an agent composes a URI flow from the action space

Example 25 ran a fixed `kvm → ocr → llm` chain. Here an **agent decides the chain**:
given a goal and the registry's **action space** (the routes it may call), a pluggable
planner picks the steps, threads each step's output into the next, and `urirun agent run`
executes them under policy. Nothing is hard-coded to specific URIs — the agent discovers
them.

```txt
goal: "capture the screen, read its text, and summarize it"
            │
            ▼
   urirun agent space  ──►  [ kvm://…/capture, ocr://…/text, llm://…/complete, … ]
            │                         (the action space)
            ▼
   planner.plan(goal, space)  ──►  [ {kvm, payload}, {ocr, image_id:$ref:0…}, {llm, prompt:$ref:1…} ]
            │
            ▼
   urirun agent run --allow kvm/ocr/llm --allow-commands  ──►  executed, threaded, gated
```

## Run it

```bash
./agent_flow.sh
```

```
== action space the agent sees ==
{"uri":"kvm://{host}/monitor/command/capture","kind":"command","inputs":[]}
{"uri":"llm://{host}/chat/command/complete","kind":"command","inputs":[]}
{"uri":"ocr://{host}/image/query/text","kind":"query","inputs":[]}

== agent run (planner composes + executes the chain under policy) ==
  [kvm://host1/monitor/command/capture]   why: goal needs an image: capture a monitor
      out: {"image_id":"shot-mon0", ...}
  [ocr://host1/image/query/text]          why: read the captured image's text (uses the capture's image_id)
      out: {"text":"INVOICE  Acme Corp  TOTAL DUE: 42.00 USD  due 2026-07-01", ...}
  [llm://host1/chat/command/complete]     why: summarize the OCR text (uses the OCR step's text)
      out: {"summary":"Invoice for 42.00 USD, due 2026-07-01.", ...}

agent composed kvm->ocr->llm from the action space and ran it: ok
```

## How it works

- **Action space** — `urirun agent space <registry>` lists each route as
  `{uri, kind, label, inputs, required}`. That is everything the agent is allowed to
  consider; it can't invent a URI that isn't there.
- **Planner** — `planner.plan(goal, space)` is the agent. It matches capabilities by
  keyword (`capture`/`screenshot`, `ocr`/`/image/`, `llm`/`complete`) against the action
  space and emits `{uri, payload, why}` steps. It is a plain `(goal, space) -> steps`
  function — **swap in an LLM planner with the same signature** and nothing else changes.
- **Threading** — a step payload can carry `$ref:<step>.<field>` (e.g.
  `{"image_id": "$ref:0.image_id"}`). `urirun agent run` resolves it from the earlier
  step's real output at execution time, so the agent's static plan becomes a live
  data-flow chain. (This is the `run_plan` ref-resolution added in urirun.)
- **Policy** — `--allow kvm/ocr/llm` plus `--allow-commands` is the boundary. Queries run
  freely; commands run only when permitted, so the agent can't be steered into calling
  something it wasn't authorized to.

## Plugging in a real LLM planner

```python
def plan(goal: str, space: list[dict]) -> list[dict]:
    # ask an LLM to return [{uri, payload, why}] choosing only from `space`,
    # using "$ref:<step>.<field>" to pass an earlier step's output downstream.
    ...
```

Point `urirun agent run --planner yourmodule:plan` at it. The action space, `$ref`
threading, policy gate and execution are identical — only the decision changes.

## Files

- `planner.py` — the agent: `(goal, action_space) -> steps` with `$ref` threading.
- `agent_flow.sh` — `urirun agent space` + `urirun agent run` over the adopted packs.
- `test_agent_flow.py` — asserts the composed plan, the threaded execution, and the CLI.
- Reuses the flow packs from `../25-tellmesh-uri-flow/packs`.
