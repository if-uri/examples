# 35 — deploy a browser/office/tools surface onto a remote node (no SSH)

Push a **self-contained, multi-scheme surface** onto a running urirun node over
`POST /deploy` — and then **control the remote machine's browser** from the host.
One file, only stdlib + the Chrome that's already on the node, so it deploys where
pip-installing the real connector packages isn't possible.

```
host                         remote node (e.g. lenovo, behind NAT, SSH closed)
 host copy-id    ──signed──►  enroll the SSH key (TOFU / signed)
 host deploy     ──code+──►   write lenovo_node.py + hot-swap the served registry
                  bindings    (no restart) — routeCount jumps, new schemes appear
        │
        ▼  browser://laptop/page/query/text {url}
 drive it ───────────────►   node runs headless Chrome, returns the page text
        ◄───────────────     ...or a screenshot, or opens a real window
```

## What it deploys (14 routes, 8 schemes)

| scheme | routes |
|--------|--------|
| `browser://` | `page/query/text`, `page/query/screenshot`, `desktop/page/command/open` — **real headless Chrome** |
| `sys://` | `host/query/info`, `disk/query/usage` |
| `fs://` | `file/command/write`, `file/query/read`, `dir/query/list` (sandboxed under `~/.urirun-node/ws`) |
| `codec://` `hash://` `uuid://` | base64 / sha256 / uuidv4 (the polyglot connectors, in stdlib) |
| `httpcheck://` | `url/query/status` |
| `office://` | `note/command/write`, `note/query/read` |

## Run

```bash
NODE_URL=http://192.168.188.201:8765 ./deploy.sh   # enroll key + deploy + verify
NODE_URL=http://192.168.188.201:8765 python3 verify.py
```

Verified live on a real Fedora node ("lenovo"):

```
  ✓ browser://laptop/page/query/text        {"text":"Example Domain ... documentation examples ..."}
  ✓ browser://laptop/page/query/screenshot  {"screenshot":"~/.urirun-node/ws/shot-….png","bytes":18150}
  ✓ sys://laptop/disk/query/usage           {"total_gb":157.7,"free_gb":11.2,"used_pct":92.4}
  ... 9/9 routes verified on the remote node
```

## Why `isolated=False` matters here

The handlers are declared `isolated=False`, which compiles to a **`local-function`**
binding (run in the node's own process) rather than `local-function-subprocess`.
That's the key to deploy: `/deploy` adds its code dir to the *node process's*
`sys.path`, so an in-process handler imports the pushed module — an isolated
subprocess would start fresh and `ModuleNotFoundError`. (See `tellmesh_bridge.py`
in [example 31](../31-llm-remote-office), which deploys the same way.)

## Bootstrap from git — the `github` connector

To put *real* connector packages on a node (not just this stdlib surface), use
[`urirun-connector-github`](../../urirun-connector-github): the node clones a repo
and emits its bindings, which you then `host deploy`:

```bash
urirun run 'github://host/repo/command/clone'   --payload '{"url":"https://github.com/if-uri/urirun-connector-time-tools.git"}' --execute
urirun run 'github://host/repo/query/bindings'  --payload '{"dest":"~/.urirun-projects/urirun-connector-time-tools","module":"urirun_connector_time_tools"}' --execute
# -> bindings → compile → host deploy onto any machine
```

For the full desktop (windows / keyboard / mouse / LibreOffice), the
**tellmesh** packs (`urihim`/`urikvm`/`uribrowser`/`urioffice`) must be importable
on the node; bridge them as in example 31. This example covers everything that is
self-contained-deployable, including real browser control.

## Files

- `lenovo_node.py` — the deployable surface (one file, `local-function` handlers).
- `deploy.sh` — enroll key + `host deploy` + verify.
- `verify.py` — drive every route on the node and assert (incl. browser).
