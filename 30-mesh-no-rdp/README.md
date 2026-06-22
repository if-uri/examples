# 30 — control one computer from another, without RDP (urirun mesh)

RDP gives a remote operator the *whole* machine. urirun gives the controller only the
**specific routes a node chooses to expose**, each policy-gated — least-privilege remote
control over plain HTTP. No desktop, no full session: the controller calls named URIs,
the node runs them and returns JSON.

```txt
computer B (node)                         computer A (controller / host)
  urirun node serve  --allow sys/sh/log     urirun host add-node B http://B:8765
     │  exposes:                                 │
     │   sys://B/runtime/query/info              │  POST /run {uri, payload}
     │   sh://B/command/run  (enum-whitelisted)  ├──────────────────────────►  runs on B,
     │   log://B/session/...                     │  ◄──────────────────────────  returns JSON
```

## On each computer (the real workflow)

```bash
# on every machine you want to control (the "nodes"):
curl -fsSL https://get.urirun.com/node.sh | bash -s -- --name officepc --service
#   --service installs a boot service; it serves a small registry over HTTP on :8765

# on the controlling machine (the "host"):
curl -fsSL https://get.urirun.com/host.sh | bash -s -- --name studio \
     --add-node officepc=http://192.168.1.20:8765
HC=~/.urirun-host/mesh.json     # host.sh stores the mesh config here — always pass it

# control it (no RDP). ALWAYS pass --config, or host commands look in ./.urirun and show (none):
urirun host nodes  --config "$HC"     # registered nodes
urirun host routes --config "$HC"     # the exact URIs each node exposes
curl -s http://192.168.1.20:8765/routes | python3 -m json.tool   # ask the node directly

# call a route the default node actually serves (env/proc/shell/log), namespaced under
# the node's --name. `node.sh --name officepc` -> routes live under `…://officepc/…`:
curl -s -X POST http://192.168.1.20:8765/run -H 'Content-Type: application/json' \
     -d '{"uri":"shell://officepc/command/uname","payload":{}}'
curl -s -X POST http://192.168.1.20:8765/run -H 'Content-Type: application/json' \
     -d '{"uri":"env://officepc/runtime/query/health","payload":{}}'

# shut down on each machine:
systemctl --user disable --now urirun-node     # node (installed with --service)
# or just stop the process if started in the foreground
```

> **Two gotchas that bite first-timers**
> 1. `urirun host nodes` with no `--config` reads `./.urirun/mesh.json` and prints `(none)`.
>    The mesh `host.sh` created is at `~/.urirun-host/mesh.json` — pass `--config "$HC"`.
> 2. A node's routes are namespaced under **its own `--name`** (defaulting to the machine's
>    *hostname*), **not** the alias you used in `--add-node alias=URL`. If you ran `node.sh`
>    without `--name`, run `curl http://NODE:8765/routes` to see the real scheme/name, e.g.
>    `shell://lenovo/command/uname`. The default node has **no** `sh://…/command/run` route —
>    that scheme belongs to this example's own `mesh_local.sh` registry below.

The node's security boundary is its **`--allow` globs + each route's input schema**. A
controller can only call exposed routes, and only with permitted arguments — e.g.
`shell://…/command/which` takes a `binary` param, and the local-demo's `sh://…/command/run`
accepts an `enum` of whitelisted commands, so `rm -rf /` is rejected before it ever runs.

## Run the whole thing locally (two nodes + a host)

```bash
./mesh_local.sh
```

It simulates two computers as local nodes and a controller, end to end:

```
== control node-b FROM the controller, over HTTP (no RDP) ==
  [b] sys info      -> {"host":"…","platform":"Linux-…","cwd":"…"}
  [b] run 'uname -a' -> Linux … #35-Ubuntu …
  [a] write log     -> {"wrote":"hello from the controller"}
  [a] read log      -> {"lines":["{…\"text\": \"hello from the controller\"}"]}

== least-privilege check: a non-whitelisted command is REFUSED by the node ==
  rm -rf / -> false 'rm -rf /' is not one of ['uname -a', 'uptime', 'id', 'date', 'df -h /']
```

## Why this beats RDP for automation

- **Least privilege** — expose three routes, not the whole desktop. The controller
  cannot do anything the node didn't publish.
- **Structured, not pixels** — every call returns JSON you can pipe, test, and chain
  (see examples 25–29 for flows and agents over exactly these routes).
- **NAT-friendly relay** — for hosts on the open internet (not the same LAN), the
  `mesh-urirun-com` repo (`mesh.urirun.com`) routes the same `/run` calls through a small
  PHP relay so both sides only need outbound HTTP — no inbound ports, no port-forwarding.

## Files

- `node.bindings.template.json` — the small registry each node serves (`sys`/`sh`/`log`).
- `mesh_local.sh` — two nodes + a host, serve → register → dispatch → shut down.
- `test_mesh.py` — asserts the controller drives a node and the enum boundary holds.
