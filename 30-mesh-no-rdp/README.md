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
urirun node list --host 192.168.1.20 --ports 8765-8815   # every node running on a machine
curl -s http://192.168.1.20:8765/routes | python3 -m json.tool   # ask the node directly

# call a route the default node actually serves (env/proc/shell/log), namespaced under
# the node's --name. `node.sh --name officepc` -> routes live under `…://officepc/…`:
curl -s -X POST http://192.168.1.20:8765/run -H 'Content-Type: application/json' \
     -d '{"uri":"shell://officepc/command/uname","payload":{}}'
curl -s -X POST http://192.168.1.20:8765/run -H 'Content-Type: application/json' \
     -d '{"uri":"env://officepc/runtime/query/health","payload":{}}'

# shut down on each machine:
urirun node stop --all                         # stop every node running on this machine
systemctl --user disable --now urirun-node     # a --service node respawns on kill; disable it
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

## Re-provision a node from the host — no SSH (`POST /deploy`)

A running node can be **re-provisioned over the mesh**: push a new registry (and even the
handler code) and the node hot-swaps what it serves, no restart. `get.urirun.com/node.sh`
turns this on by default. Auth is **SSH-key based, like `ssh-copy-id`** — no shared token:

```bash
uri-copy-id 192.168.1.20                       # enroll your ~/.ssh/id_ed25519 on the node
#   first key on a fresh node = trust-on-first-use; later keys must be signed by an enrolled one
urirun host copy-id --all --config "$HC"       # …or onto every node in the mesh at once

# now push routes/code, signed with your key (no token to remember):
urirun host deploy officepc --config "$HC" \
  --bindings my.bindings.json --identity ~/.ssh/id_ed25519
```

A node started with `--key-auth` keeps `~/.urirun-node/authorized_keys` and verifies an
ed25519 signature on each `/deploy`; `GET /health` reports `"deploy"`/`"keyAuth"`. A shared
token still works as an alternative (`node serve --admin-token …` + `host deploy --token`).
[Example 31](../31-llm-remote-office) uses exactly this to push a whole office/desktop URI
surface onto a remote node and drive it from natural language.

## Manage the nodes on a machine

```bash
urirun node list                 # every running node here (any port; probes listening sockets)
urirun node stop --port 8766     # stop one instance (repeatable)
urirun node stop --all           # stop them all (node.sh's free-port fallback breeds duplicates)
```

## Watch a node's activity live (no SSH)

A node streams every `/run` and every error as Server-Sent Events on `GET /events`, so you
can follow what a remote machine is doing in real time — over plain HTTP, nothing to tail:

```bash
HC=~/.urirun-host/mesh.json
urirun host watch node-b --config "$HC"                  # live stream, formatted
urirun host watch node-b --scheme sh,error --config "$HC"   # only these schemes
urirun host watch node-b --follow --config "$HC"         # reconnect + replay on drop
curl -N http://192.168.1.20:8765/events                  # raw SSE, no CLI
```

```
data: {"event":"run","uri":"sys://node-b/runtime/query/info","ok":true, ...}
data: {"event":"error","uri":"error://local/E-a7d90355/...","message":"Route not found: ...", ...}
```

`GET /health` reports `events` (subscriber count); for the node's own stdout use
`tail -f ~/.urirun-node/node.log` (`--background`) or `journalctl --user -u urirun-node -f`
(`--service`). [Example 32](../32-task-scenarios) drives scenarios while watching this stream.

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

== discover running nodes on this machine ('urirun node list') ==
  PORT   NAME    ROUTES  DEPLOY  EXEC  URL
  34489  node-b  4       False   True  http://127.0.0.1:34489
  58503  node-a  4       False   True  http://127.0.0.1:58503

== shut them down with 'urirun node stop' (SIGTERM -> port freed) ==
  port 58503: stopped (pids [...])
  port 34489: stopped (pids [...])
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
- `mesh_local.sh` — two nodes + a host, serve → register → dispatch → `node list` → `node stop`.
- `test_mesh.py` — asserts the controller drives a node and the enum boundary holds.
