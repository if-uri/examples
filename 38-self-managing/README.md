# 38 — self-managing urirun (resolver + loop + governance)

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

### 2. The self-managing loop — *built here* (`self_managing.py`)

`self_managing_loop(client, goal, planner, resolver, provision)` extends the agent
loop ([example 37](../37-closed-loop-automation)) with a capability-gap step:

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

Proven offline (`test_self_managing.py`, 2 passed): a node starts serving only
`sys://`; the loop is asked to write a `note://`, **detects the gap, provisions the
note connector, re-discovers the now-larger surface, and completes the goal** — and a
second test shows it reports an unresolvable capability cleanly. The production
`make_provision(...)` installs via the admin-gated `node://.../package/command/install`
(local path → git fallback) then `host deploy --merge`s the connector's bindings.

### 3. Governance — *built here* (`governance.py`)

`governed_provision(install_fn, allowlist=, verify_fn=, approve=, audit=)` wraps any
provision with the safety gates, so autonomy is safe by default:

- **Source allowlist** — trusted by default: `connect.ifuri.com`, `github.com/if-uri/*`,
  `~/github/if-uri/*`. An install from outside the allowlist is blocked unless an
  `approve(candidate)` callback (a human) says yes.
- **Verify before serve** — `make_verify_fn()` runs `connectors verify` on the
  connector's source before its routes serve; a connector that advertises a dead route
  never joins the registry.
- **Admin-gated + audited** — the underlying install goes through `node:// --manage`
  (signed, never on the open `/run`); every decision (source, spec, verdict) is handed
  to an `audit` sink for the log / `/events` stream.

Proven offline (`test_governance.py`, 4 passed): a trusted source installs; an untrusted
one is blocked without approval and allowed with it; a connector that fails verify is
not served.

### 4. Real connector E2E — *proved here* (`test_e2e_self_managing.py`)

The end-to-end test starts a real local node with only `sys://`, asks for a
`time://` route, resolves that capability to `urirun-connector-time-tools`, gates it
through governance, provisions the connector, re-discovers the node surface, and runs
the new route. This is the self-managing path with a real connector, not a stub.

## Why local-first

Your `~/github/*` already holds 19 connectors. Resolving a capability to a **local
path** (`pip install -e <path>`) means an autonomous node extends itself from your own
work instantly and offline — git/PyPI are the fallback for a node that doesn't have the
source locally. The same `{spec}` shape (`node://…/package/command/install`) covers all
three.

## Files

- `resolver.py` — the capability→connector resolver across local/git/hub.
- `self_managing.py` / `test_self_managing.py` — the loop (gap → resolve → provision → re-plan) + `make_provision`; offline proof (node gains a capability mid-run), 2 cases.
- `governance.py` / `test_governance.py` — allowlist + verify-before-serve + audit gates, 4 cases.
- `test_e2e_self_managing.py` — real-node proof using `urirun-connector-time-tools`.

## Next to build

- Persist/cache the connector index so repeated `connectors resolve` calls do not rescan
  local projects every time.
- Wire the core resolver + `NodeClient.ensure_scheme(...)` into production NL→flow
  execution, so a missing scheme automatically triggers resolve → install → adopt → retry.
- Move governance deeper into node-side management (`apply_deploy` / `node:// --manage`),
  so allowlist, verify-before-serve, and audit are enforced even outside this example.
