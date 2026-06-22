# 38 — toward a self-managing urirun (proposal + resolver prototype)

> What's missing so urirun is not only **LLM-controlled** but **LLM-managed** — it
> installs the connectors it needs, on demand, from the hub, from local
> `~/github/*/*` projects, or from GitHub.

## Where we are today

urirun is already **LLM-controlled** and has every install *primitive*:

| capability | how |
|------------|-----|
| NL → flow → execute, with self-repair | `host ask`, [example 37](../37-closed-loop-automation) |
| install on a node (admin-gated, signed) | `node://<n>/package/command/install {spec}` — spec = **PyPI name, `git+https://…`, or a local path** (anything pip accepts) |
| install a hub connector by id | `connectors install` / `node://<n>/connector/command/install {id}` |
| clone a repo → bindings → deploy | [`urirun-connector-github`](../../urirun-connector-github) |
| reject a badly-built connector | `connectors verify` (resolves every handler) |
| see/merge/pin the surface | `host deploy --merge`, registry etag, `host probe` |

So a node *can* be told to install from anywhere. **What it can't do yet is decide
to.**

## What's missing (the gap)

1. **Capability → connector resolution.** When the LLM plans a route no installed
   connector serves (`browser://…`, "send email", `llm://…/vision/command/ocr`),
   nothing maps that *need* to a connector and a place to get it.
2. **A capability-gap loop.** The closed loop self-repairs the *payload* (wrong field
   → node error → fix). It does **not** self-extend the *capability set* ("I need
   `browser://` but it isn't served → install it → retry").
3. **Local projects aren't a catalog.** The ~19 `urirun-connector-*` under
   `~/github/*` are installable by path, but nothing indexes which *capability* each
   provides so the agent can find them.
4. **No governance for autonomous install.** Installing code on a node is RCE-class;
   an autonomous installer needs a trusted-source allowlist, verify-before-serve, and
   an audit trail.

## Proposal

### 1. Connector resolver — *prototyped here* (`resolver.py`)

`resolve(capability) → [{connector, schemes, install:{local, git, pypi}}]`, indexing
three sources: local `~/github/*` projects, a git org, and the hub catalog. The
missing primitive — demonstrated live:

```
$ python3 resolver.py browser
  [155] urirun-connector-browser-control   schemes=['browser']
        install: -e /home/tom/github/if-uri/urirun-connector-browser-control
             or: git+https://github.com/if-uri/urirun-connector-browser-control.git
$ python3 resolver.py "send email"
  [ 60] urirun-connector-email             schemes=['email']
```

It indexed **19 local connectors** and maps a needed scheme / route / NL phrase to the
connector that provides it **and** how to install it (local path, git, or PyPI).

### 2. The self-managing loop

Extend the agent loop ([example 37](../37-closed-loop-automation)) with a
capability-gap step:

```
plan a step
  └─ is the step's scheme in the node's /routes?
        yes → execute
        no  → resolve(scheme)                         # resolver.py
              → pick a source (local ~/github > git org > hub)
              → node://<node>/package/command/install {spec}   # admin-gated, signed
              → connectors verify <pkg>                # gate: every handler resolves
              → re-read /routes (registry etag bumps)  # host probe confirms the surface
              → re-plan and execute
```

Now the loop **manages** urirun: it self-extends with the capability it's missing,
from local source first (fast, offline, your own `~/github`), then git, then the hub.

### 3. Governance (so autonomy is safe)

- **Source allowlist** — trusted by default: `connect.ifuri.com`, `github.com/if-uri/*`,
  `~/github/if-uri/*`. An install from outside the allowlist pauses for human approval.
- **Verify before serve** — `connectors verify` runs on the freshly installed connector
  before its routes join the registry; a connector that advertises a dead route never
  serves.
- **Admin-gated + audited** — installs go through `node:// --manage` (signed, never on
  the open `/run`); every install is logged with source, spec and authorizer, and
  emitted on the `/events` stream.

## Why local-first

Your `~/github/*` already holds 19 connectors. Resolving a capability to a **local
path** (`pip install -e <path>`) means an autonomous node extends itself from your own
work instantly and offline — git/PyPI are the fallback for a node that doesn't have the
source locally. The same `{spec}` shape (`node://…/package/command/install`) covers all
three.

## Files

- `resolver.py` — the capability→connector resolver across local/git/hub (run it: `python3 resolver.py [capability]`).

## Next to build

- Wire `resolve()` into the example-37 agent loop (gap detection + provision step).
- `urirun connectors resolve <cap>` / `connectors index` (cache the catalog).
- The source allowlist + verify-before-serve in `apply_deploy` / `node:// --manage`.
