# 14 — LLM-over-URI agent (drive Chrome + tools by URI)

An LLM-style **decision loop over a URI registry**: compile connectors into one
registry (the agent's *action space*), let a planner pick `{uri, payload}` steps,
run them under policy (`query` freely, `command` only when permitted), and feed
each result into the next decision.

This is the pattern from [`../AUTOMATION-INTEGRATIONS.md`](../AUTOMATION-INTEGRATIONS.md):
**registry → LLM picks a URI → policy gate → run → result → repeat.**

## Run

```bash
python3 agent.py "check and read https://example.com"
# queries (time/http/dom) run; the log COMMAND is skipped (gated)

python3 agent.py "check and read https://example.com" --allow-commands
# now the log:// command runs too
python3 agent.py "..." --json     # machine-readable trace
```

Example output:

```
  ✓ time://host/clock/query/now           stamp the run
      -> {"ok": true, "utc": "2026-…Z"}
  ✓ httpcheck://host/url/query/status      is the site up?
      -> {"ok": true, "status": 200, ...}
  ✓ browser://chrome/page/query/dom        read the page
      -> {"ok": true, "bytes": 561, "sample": "<!DOCTYPE html> ...Example Domain..."}
  · log://host/run/command/write           record the run  (gated)
```

## Pieces

- **`tools.py`** — a tiny self-contained connector: emits v2 `bindings` and answers
  `time`, `httpcheck`, `browser://chrome` and `log` routes. The browser route reads
  a page via **headless Chrome** (`chrome --headless --dump-dom`), with a graceful
  dry-run when no Chrome is installed. In production these are real connectors
  (`time-tools`, `http-check`, a Chrome CDP `browser-control`, `sqlite-context`).
- **`agent.py`** — `load_registry()` → `action_space()` → `plan()` → `run_step()`.
  `plan()` is deterministic so the demo runs in CI.

## Reusing the real `browser-control` connector

The browser route doesn't have to be the `tools.py` stub. When the sibling package
[`urirun-connector-browser-control`](../../urirun-connector-browser-control) is
checked out next to this repo, `agent.py` **reuses it** for the whole `browser://`
surface — the same registry, but backed by the packaged connector instead of the
demo stub:

```text
without connector:  browser://chrome/page/query/dom            (tools.py stub)
with connector:     browser://chrome/page/query/dom            ┐
                    browser://chrome/page/query/text           │ urirun-connector-
                    browser://chrome/page/command/screenshot   │ browser-control
                    browser://desktop/page/command/open        │
                    browser://desktop/page/command/screenshot  ┘
```

The connector ships `argv-template` routes whose argv invokes its own
out-of-process executor (`python3 -m urirun_connector_browser_control._exec
<subcommand> ...`), which prints the route's JSON result — so the agent drives it
**as an external tool**, with no in-process import of the connector at call time
(this is also why the routes survive being compiled into a registry).
`agent.browser_control_bindings()` loads the connector straight from the checkout
(adds the package dir to `sys.path`/`PYTHONPATH`, no install needed) only to read
those bindings, then rewrites `argv[0]` to the current interpreter so they run in
this venv. `load_registry()` then drops the inline `browser://`
stub and merges in the connector's routes; the planner prefers the connector-only
`page/query/text` route, and `run_step` unwraps the handler result from the run
envelope (`result.value`). The run banner reports which backend is active:

```bash
python3 agent.py "check and read https://example.com"
# action space: 8 routes  (browser: urirun-connector-browser-control)
#   ✓ browser://chrome/page/query/text   read the page
#       -> {"connector": "browser-control", "ok": true, ...}
```

If the connector isn't present the agent silently falls back to the `tools.py`
stub (`browser: tools.py (inline stub)`), so the example still runs standalone.
This is the point of the URI + registry substrate: a connector is *plugged into*
the agent's action space without changing the loop — see
[`../18-connector-transport`](../18-connector-transport/).

## Built into urirun

This loop now ships as a runtime command — point it at any compiled registry:

```bash
tools.py bindings > b.json && urirun compile b.json --out reg.json
urirun agent space reg.json                                   # the action space
urirun agent run reg.json --goal "check https://example.com" \
  --planner agent:plan --allow-commands                       # run a pluggable planner
```

`--planner module:function` takes `(goal, action_space)` and returns the
`[{uri, payload}]` steps — wire it to an LLM. `agent.py` here is the long-form
equivalent.

## Swap in a real LLM

Replace `plan(goal, routes)` with a model call: send the **goal** plus the
**action space** (`action_space(registry)` — the same data as `urirun`'s MCP tools)
and have the model return the `[{uri, payload}]` steps. Anything MCP/A2A-speaking
can consume the registry directly; or use the `llm` connector
(`llm://host/chat/command/complete`) inside the loop.

## Why URI + registry is a good agent substrate

- one validated, typed contract for every capability (no N bespoke SDKs);
- `query` vs `command` makes read-vs-write safe by construction;
- `--allow`/`--execute` policy curates exactly what the agent may do;
- the same registry is already MCP tools / an A2A card — discover-and-call, no glue;
- every step is a URI + payload + decision → auditable and replayable.

## Real Chrome control (CDP)

`chrome --headless --dump-dom` is the one-shot shown here. For full control use the
**Chrome DevTools Protocol** (`chrome --remote-debugging-port=9222`) and map:
`Page.navigate` → `browser://chrome/page/command/navigate`, `Runtime.evaluate` →
`…/page/query/eval`, `Page.captureScreenshot` → `…/page/command/screenshot`,
`Input.dispatchMouseEvent` → `…/page/command/click`. `query` = read DOM/eval,
`command` = navigate/click (gated). See `../AUTOMATION-INTEGRATIONS.md` §4.

## Test

```bash
pytest test_agent.py -q
```
