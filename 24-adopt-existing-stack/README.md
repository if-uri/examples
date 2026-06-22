# 24 — adopt urirun into an existing stack

You already have a project: real services, real functions, several languages and
libraries. You **don't** want to rewrite any of it. You just want every capability
reachable as a **URI** — from the CLI, over HTTP, from another service, from an
LLM/agent — without inventing a new API per consumer.

That is exactly what urirun adopts onto an existing codebase. This example takes a
tiny but realistic stack and wires it up, end to end, on docker-compose.

## The "existing" stack (`legacy/`, pretend it's yours)

| File | Runtime | Existing capability |
|------|---------|---------------------|
| `legacy/inventory.py`  | Python  | `check_stock`, `reserve` |
| `legacy/notify.mjs`    | Node.js | send a notification |
| `legacy/report.sh`     | shell   | daily sales report |

Nothing in `legacy/` knows about urirun. It keeps its own libraries and entry points.

## The only thing you add: bindings

`shop.bindings.json` maps a **URI → an argv template that calls the existing entry
point**. No SDK import, no framework, no rewrite:

```json
"shop://inventory/stock/query/check": {
  "adapter": "argv-template",
  "argv": ["python3", "legacy/inventory.py", "check", "--sku", "{sku}"],
  "inputSchema": { "type": "object", "required": ["sku"],
                   "properties": { "sku": { "type": "string" } } }
}
```

The URI shape is `scheme://target/resource/<query|command>/action`. The
`inputSchema` is the contract every layer (CLI, HTTP, MCP, A2A) validates against.

---

## Step by step

### 0. Prerequisites
`urirun >= 0.4.4`, plus the runtimes your code uses (`python3`, `node`, `bash`).
```bash
pip install "urirun>=0.4.4"      # or: pipx install urirun
urirun --version
```

### 1. Validate & compile the bindings into a registry
```bash
urirun validate shop.bindings.json
urirun compile shop.bindings.json --out shop.registry.json
urirun list shop.registry.json
```

### 2. Layer 1 — CLI (every runtime, one command)
```bash
urirun run 'shop://inventory/stock/query/check'  shop.registry.json --execute --allow 'shop://*' --payload '{"sku":"sku-1"}'
urirun run 'shop://notify/email/command/send'    shop.registry.json --execute --allow 'shop://*' --payload '{"to":"a@b.com","msg":"hi"}'
urirun run 'shop://report/sales/query/daily'     shop.registry.json --execute --allow 'shop://*' --payload '{"date":"2026-06-22"}'
```
Same verb (`urirun run`) reaches Python, Node and shell. `--allow` is the security
boundary; everything is a dry-run plan until `--execute`.

### 3. Layer 2 — HTTP (every service, no client library)
```bash
urirun node serve --registry shop.registry.json --host 0.0.0.0 --port 8080 --execute --allow 'shop://*'
# from anywhere:
curl -s -X POST http://localhost:8080/run -H 'Content-Type: application/json' \
  -d '{"uri":"shop://inventory/stock/query/check","payload":{"sku":"sku-3"}}'
```

### 4. Layer 3 — MCP & A2A (the agent / LLM layer)
The same registry projects to MCP tools and an A2A agent card — no extra code:
```bash
urirun-v2-mcp tools shop.registry.json     # MCP tool definitions for an LLM
urirun-v2-mcp card  shop.registry.json --name shop --url http://gateway:8080/
urirun-v2-mcp serve shop.registry.json --execute   # live MCP server over stdio
```

### 5. Layer 4 — in-process (same runtime, no subprocess)
```python
import urirun, json
reg = urirun.compile_registry(json.load(open("shop.bindings.json")))
policy = {"execute": {"allow": ["shop://*"], "deny": []}}
print(urirun.run("shop://inventory/stock/query/check", reg, {"sku": "sku-1"},
                 mode="execute", policy=policy))
```

### 6. Everything together — docker-compose
```bash
docker compose up --build
```
- `gateway` — one container with python+node+bash, serving every `shop://` route over HTTP (`:8080`).
- `client` — a *separate* container calling those URIs with plain `curl` (no shared code, no SDK).

### One-shot local proof (no docker)
```bash
./verify.sh        # compiles, runs all 4 URIs across 3 runtimes, projects MCP + A2A
```

---

## URI in every runtime and on every layer

| Layer / consumer        | How it calls `shop://…`                         |
|-------------------------|--------------------------------------------------|
| CLI / scripts           | `urirun run <uri> …`                              |
| HTTP / microservices    | `POST /run` to `urirun node serve`               |
| LLM / agents (MCP)      | `urirun-v2-mcp serve` (tools auto-generated)      |
| Agent-to-agent (A2A)    | `urirun-v2-mcp card` (skills auto-generated)      |
| Same-process Python     | `urirun.run(uri, registry, payload)`             |
| Python / Node / shell   | argv templates — the existing code, unmodified   |

One contract (`shop.bindings.json`), one security model (`--allow`), every layer.

## Adopting *your* project

1. **List your entry points** — CLIs, scripts, `npm`/console scripts, Make targets.
2. **Write one binding per capability** (argv/shell template → that entry point), or
   let `urirun scan .` adopt a Dockerfile / package.json / Makefile / scripts for you.
3. **Pick a scheme** (`shop://`, `crm://`, …) and `target/resource/verb/action` paths.
4. `compile` → serve / project. Optionally publish the bindings under the
   `urirun.bindings` entry-point group so `urirun run` auto-discovers them after
   `pip install` (see the connector examples).

See also: [`13-simple_defaults`](../13-simple_defaults) (authoring), 
[`23-embedded-urirun`](../23-embedded-urirun) (builtin URIs), 
[`08-multi_transport`](../08-multi_transport) (transport matrix).
