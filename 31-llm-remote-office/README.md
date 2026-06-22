# 31 — drive a remote computer's office work from natural language (LLM → URI → mesh)

You type an office task in plain language on your **host**; an **LLM** (liteLLM, config
from `examples/.env`) turns it into a **URI plan**; urirun **delegates each step to a
remote node** (`192.168.188.201`, the default urirun port `:8765`) over the mesh; and
the run is **logged on both sides** — the host's trace *and* the node's own log — so you
see exactly what happened on each machine.

It combines three earlier examples into one operational setup:

- **[27](../27-agent-llm-rdp)** — a real LLM plans over the tellmesh URI surface.
- **[30](../30-mesh-no-rdp)** — control a computer from another over the urirun node/host
  mesh (no RDP; least-privilege, policy-gated routes over HTTP).
- **[24](../24-adopt-tellmesh-packs)** — adopt the `../tellmesh/*` libraries
  (`urihim`, `urikvm`, `uribrowser`, `urioffice`, `uriscreen`, `urishell`) into the
  registry the node serves.

```txt
 HOST (studio)                                   NODE (lenovo @ 192.168.188.201:8765)
 ──────────────                                  ────────────────────────────────────
 "open example.com and type the invoice no."     urirun node serve  (office registry)
        │  examples/.env (OPENROUTER_API_KEY,       exposes, policy-gated:
        │                 LLM_MODEL)                  browser://lenovo/page/open
        ▼                                             him://lenovo/keyboard/command/type-text
  GET /health + /routes  ◄──── the node's live ─────  kvm://lenovo/monitor/.../screenshot
  (the action space)            action space          urioffice://lenovo/document/command/open
        │                                              screen://lenovo/monitor/0/query/frame
        ▼                                              shell://lenovo/process/command/run
  LLM plans [{uri,payload,why}]                        log://lenovo/session/...   ◄─┐
        │                                                                           │
        ▼  POST /run {uri,payload}                                                  │
  dispatch each step ───────────────────────────────►  node runs it, returns JSON   │
        │  + log each step on the node ─────────────────────────────────────────────┘
        ▼
  generated/run-log.md + host-run-*.log   ◄── read the node's own log back (both sides agree)
```

## Two machines, two commands

### 1. On the node (the machine you want to control — `192.168.188.201`)

Copy this example dir (and the `../tellmesh` checkout) to the node, then:

```bash
./node_serve.sh
#   name=lenovo, binds 0.0.0.0:8765, ALLOW_REAL=1 (drives the real mouse/keyboard/
#   browser/LibreOffice). Builds the registry from the tellmesh manifests and serves it.

ALLOW_REAL=0 ./node_serve.sh        # safe mock mode (handlers return without touching the box)
NODE_NAME=officepc ./node_serve.sh  # different node name / URI host segment
```

It picks `../tellmesh/urisys-node/.venv/bin/python` (it has `urirun` + `uricontrol` +
the connectors); override with `PY=…`, and the checkout locations with
`IFURI_DIR=… TELLMESH_DIR=…`. The node prints `routes: 34` and the served schemes
(`browser, env, him, kvm, log, proc, screen, shell, urioffice`).

> **The bridge.** Real tellmesh handlers are `handler(payload, context)`; urirun's
> local-function adapter calls `fn(**payload)`. `tellmesh_bridge.py` reads each
> manifest, imports the real handler, and exposes a `fn(**payload)` wrapper that
> forwards a *persistent* context (mock state, config, the `allow_real` flag) — so the
> whole tellmesh office surface executes in-process under the urirun node, unmodified.

### 2. On the host (your machine)

```bash
./office_cli.sh "open https://example.com and take a screenshot" --yes
./office_cli.sh "type 'Faktura 07/2026 zatwierdzona' then capture monitor 0" --yes
NODE_URL=http://192.168.188.201:8765 ./office_cli.sh "list the top processes" --yes
```

- no `--yes` → **commands are not dispatched** (queries still run); add `--yes` to execute.
- `--dry-run` → plan and show, dispatch nothing.
- `--json` → machine-readable trace.
- model/key come from `examples/.env`; with no key it falls back to a deterministic
  heuristic so the loop still runs. The configured `LLM_MODEL` is an image-preview model
  that plans JSON fine (like example 27) but cannot do MCP tool-calling — point
  `URIRUN_OFFICE_MODEL` at a stronger model if you want richer plans.

## Provision the node FROM the host (no SSH) — `POST /deploy`

You don't have to log into the node to change what it serves. urirun nodes expose a
token-gated `POST /deploy` that accepts a registry **and the handler code**, then
hot-swaps the served surface live (no restart). So after the node runs once with an
admin token, the host drives everything over the mesh:

```bash
# on the node — /deploy is ON by default with SSH-key auth (no shared secret):
./node_serve.sh
#   deploy /api : ENABLED (ssh-key: run 'uri-copy-id' from the host)

# from the host — enroll your SSH key once, then push the office bindings + bridge code:
./deploy_from_host.sh
#   == enroll SSH key (uri-copy-id; trust-on-first-use) ==   ← first run only
#   == push … ==  -> node routeCount jumps 7 -> 34, no restart. Re-run any time.
```

### SSH-style auth — `uri-copy-id` (no tokens)

Managing many nodes by shared token is a pain, so urirun also does **public-key auth
like SSH**, reusing your `~/.ssh/id_ed25519`:

```bash
uri-copy-id 192.168.188.201          # ssh-copy-id for urirun: enroll your key on the node
#   (equiv: urirun host copy-id 192.168.188.201 --identity ~/.ssh/id_ed25519)
urirun host deploy lenovo --bindings node-office.bindings.json \
  --code tellmesh_bridge.py --identity ~/.ssh/id_ed25519     # signed, no token
```

- The node keeps `~/.urirun-node/authorized_keys`. The **first** enrollment on a fresh
  node is trust-on-first-use (claims the node, no secret); afterwards adding a key must
  be **signed by an already-enrolled key**. Start the node with `--key-auth`
  (`node_serve.sh` and `get.urirun.com/node.sh` do this by default).
- `/deploy` then authenticates by an **ed25519 signature** over the request
  (purpose + timestamp + body hash, ±300 s) — `urirun host deploy --identity KEY`.
- Token auth still works in parallel: set `URIRUN_NODE_TOKEN` on the node and pass
  `--token`. The node needs the `cryptography` package for key-auth (`node.sh` installs
  it; otherwise `pip install cryptography`).

Under the hood it is a first-class urirun command:

```bash
urirun host deploy lenovo --bindings node-office.bindings.json \
  --code tellmesh_bridge.py --env TELLMESH_DIR=~/github/tellmesh \
  --allow 'him://lenovo/**' --allow 'browser://lenovo/**' --token secret
#   (lenovo resolves from the host mesh config, or pass a full URL)
```

- `--code FILE` ships a handler module the node writes to `~/.urirun-node/deploy/` and
  imports lazily — that is how `tellmesh_bridge.py` gets onto the node. Heavy packages
  the bridge imports (`urihim`, `urikvm`, …) must already be installed on the node;
  `--env TELLMESH_DIR=…` points the bridge at them.
- **Token**: `urirun node serve --generate-token` (what `node_serve.sh` uses) mints a
  random token and persists it to `~/.urirun-node/admin-token` (0600), reused across
  restarts so the host's token stays valid; `--admin-token TOKEN` / `URIRUN_NODE_TOKEN`
  pins your own; `--admin-token auto` is the generate-or-reuse shorthand.
- **Security**: `/deploy` is **off** unless a token is set, and every call must send the
  matching `X-Urirun-Token`. It can add executable routes and push code, so treat the
  token like a deploy key and use it only on a trusted LAN. `GET /health` reports
  `"deploy": true|false`.

> Chicken-and-egg: the *first* time still needs the node started with a token (and, for
> the office handlers, the tellmesh runtime present). After that, every update —
> new bindings, new allow policy, new handler code — is host-driven over HTTP.

### Managing many nodes

```bash
urirun node list                       # every running node on THIS machine (any port)
urirun node list --host 192.168.188.201 --ports 8765-8820   # probe a remote range
urirun node stop --port 8766           # stop one instance (repeatable)
urirun node stop --all                 # stop every running node on this machine
uri-copy-id 192.168.188.201            # enroll your key on one node
urirun host copy-id --all              # …or on every node in the mesh config
```

`node.sh`'s free-port fallback (8765 busy → next port) is why duplicates appear;
`node list` finds them all, `node stop` clears them. (systemd `--user` services respawn
on kill — disable those with `systemctl --user disable --now urirun-node`.)

## Both-sides logging (the point of the setup)

Every run is recorded twice, and the host reads the node's log back so you can confirm
they agree:

- **host side** — live trace + `generated/host-run-<ts>.log` + `generated/run-log.md`/`.json`.
- **node side** — before/after each step the host writes to `log://lenovo/session/command/write`,
  so the node's own log (`~/.urirun-node/notes.jsonl`) records the delegated task, every
  dispatched URI + payload, and every result. Read it independently any time:

```bash
curl -s -X POST http://192.168.188.201:8765/run -H 'Content-Type: application/json' \
  -d '{"uri":"log://lenovo/session/query/recent","payload":{"limit":20}}'
```

A real run delegated to the live node, end to end:

```
  [0] browser://lenovo/page/open            -> ok {"url":"https://example.com","title":...}
  [1] him://lenovo/keyboard/command/type-text -> ok {"typed":"Faktura 07/2026 zatwierdzona","chars":28}
  [2] screen://lenovo/monitor/0/query/frame -> ok {... frame ...}   (needs ALLOW_REAL=1 on the node)

== node-side log (read back from the node) ==
  node: [host] new task: "open https://example.com ..." (3 steps, planner=llm)
  node: [host->node] step 0: browser://lenovo/page/open payload={"url":"https://example.com"}
  node: [node] step 0 ok: {"url":"https://example.com",...}
  ...
```

## Office tasks this covers

| intent | URI(s) the LLM picks |
|--------|----------------------|
| log into a website / fill a form | `browser://lenovo/page/open`, `browser://lenovo/form/command/submit` |
| download / open a page, read it | `browser://lenovo/page/open`, `browser://lenovo/page/query/dom` |
| type / hotkeys / mouse on the box | `him://lenovo/keyboard/command/type-text`, `…/keyboard/command/hotkey`, `him://lenovo/mouse/command/click` |
| open / save / export a document | `urioffice://lenovo/document/command/open`, `…/command/export-pdf` |
| screenshot / OCR-driven clicking | `kvm://lenovo/monitor/{n}/query/screenshot`, `kvm://lenovo/task/command/click-text` |
| run anything on the machine | `shell://lenovo/process/command/run` |
| screen frames | `screen://lenovo/monitor/0/query/frame` |

OS-independent by construction: the host only ever speaks **URI + JSON payload**; what a
URI *does* on the node is the node's connector + its `allow_real` driver
(`xdotool`/`ydotool`, a real browser, LibreOffice). The same plan drives Linux, macOS or
Windows nodes unchanged.

## Safety / policy

The node's `--allow` globs are the security boundary (here: **open** — every office
scheme, including `shell://lenovo/process/command/run`, may execute). Tighten it by
editing `node_serve.sh` (e.g. drop the `shell` allow, or only allow `query` routes).
Each route also validates its payload against the input schema before running. The host
never holds node secrets — `secret://` resolution is off on the node by default.

## Files

- `tellmesh_bridge.py` — adapt tellmesh `(payload, context)` handlers to urirun's
  local-function convention; `build_bindings()` emits the office bindings.
- `build_node_registry.py` — office bindings + base (health/log/proc) → compiled registry.
- `node_serve.sh` — **run on the node**: build + (re)serve on `:8765`.
- `office_agent.py` / `office_cli.sh` — **run on the host**: NL → LLM plan → dispatch →
  both-sides log.
- `test_office.py` — offline end-to-end test (fake node + heuristic planner).

## Test

```bash
python3 -m pytest test_office.py -q     # or: python3 test_office.py
```
