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

# control it (no RDP) — only the routes the node exposed, each policy-gated:
urirun host nodes                  # see registered nodes + their routes
curl -s -X POST http://192.168.1.20:8765/run -H 'Content-Type: application/json' \
     -d '{"uri":"sh://officepc/command/run","payload":{"cmd":"uptime"}}'

# shut down on each machine:
systemctl --user disable --now urirun-node     # node (installed with --service)
# or just stop the process if started in the foreground
```

The node's security boundary is its **`--allow` globs + each route's input schema**.
A controller can only call exposed routes, and only with permitted arguments — e.g. the
demo's `sh://…/command/run` accepts an `enum` of whitelisted commands, so `rm -rf /` is
rejected before it ever runs.

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
- **NAT-friendly relay** — for hosts on the open internet (not the same LAN), example 31
  routes the same `/run` calls through a PHP relay at `mesh.urirun.com`.

## Files

- `node.bindings.template.json` — the small registry each node serves (`sys`/`sh`/`log`).
- `mesh_local.sh` — two nodes + a host, serve → register → dispatch → shut down.
- `test_mesh.py` — asserts the controller drives a node and the enum boundary holds.
