# urirun — optimization analysis (measured)

Numbers below were measured on this machine in this session (warm Python process
unless noted). They rank what is worth optimizing next, with the data behind each.

## Execution model — measured cost per URI call

| model | adapter | ms/call | note |
| --- | --- | --: | --- |
| in-process | `local-function` | ~0.0 | no spawn |
| process-per-URI: Go binary | `argv-template` | 2.0 | cheap spawn |
| process-per-URI: Python | `argv-template` | **220–268** | interpreter + import cold start **every call** |
| served node (argv-template) | `/run` | 237 | **still spawns per request** — serving does not amortize it |
| warm-worker pool | `WorkerPool` | **3.9** | import paid once → **69× vs cold** |

## Per-`urirun run` overhead (the auto-discovery I added)

`urirun run '<uri>'` with no source discovers + compiles **all** installed
connectors:

```
auto-discovery (entry-point scan + import ALL connectors + compile): 24.8 ms/call (97 routes)
  of which: import + urirun_bindings() for all 14 connectors:        13.2 ms
```

It imports **every** connector even to run **one** URI. Plus each `urirun` CLI call
is a fresh Python process (~28 ms interpreter cold start on top).

---

## Ranked optimizations

### 1. Lazy, scheme-indexed discovery — ✅ DONE
Was: import all connectors (~13 ms; 339 ms in a fresh process) to resolve one URI.
Now: a persisted `scheme → entry-point` index (`.urirun/scheme-index.json`,
fingerprint-invalidated) so `urirun run 'time://…'` imports **only** `time-tools`.
**Measured: ~93 ms saved per `urirun run`** in a fresh process (339 → 246 ms import).
`urirun/runtime/discovery.py`, wired into `_resolve_list_registry` for `run`.

### 2. Compiled-registry cache — ✅ DONE
The whole-runtime registry (`list` / `registry://`) is compiled once and cached to
`.urirun/discovered-registry.json`, keyed by the installed-set fingerprint.
**Measured: 30 → 10 ms warm; in a fresh process it loads JSON instead of importing
every connector.** `discovery.full_registry`, used by `list` and `registry://`.

### 3. Warm-worker inside `node serve` — ✅ DONE
A served node used to cold-start argv-template connectors per `/run` (245 ms).
`node serve --pool` keeps a warm worker per connector (`ConnectorPools`, a custom
executor so v2.run's validate → gate → execute is unchanged).
**Measured end-to-end over HTTP: 245 → 5.9 ms/request (42×).**

### 4. Hydrate `local-function` — ✅ DONE (now the connector default)
The bundled Python connectors migrated from `argv-template` (`python -m <pkg>._exec`)
to `@handler`, which emits a `local-function` binding carrying a re-importable
`python: {module, export}` descriptor. The runtime **hydrates** that descriptor at call
time, so a route runs **in-process** from a compiled file registry — no argv, no
per-connector `_exec.py`. `isolated=True` opts a route into the shared
`python -m urirun.exec` runner (crash containment / untrusted code) without writing a
shim. In-process `local-function` is ~0 ms/call vs ~220 ms for the old Python
`argv-template` spawn. `argv-template` remains for Go/untrusted/polyglot connectors,
where the warm-worker pool (#3) amortizes the spawn.

### 5. Local `urirun` daemon — ✅ DONE
Every CLI `urirun run` is a fresh process (~515 ms: interpreter + urirun import +
connector spawn). `python -m urirun.runtime.daemon serve` holds the cached registry
(#2) + a warm worker pool (#3) and answers `{uri, payload}` over a Unix socket. The
client (`daemon.call`) is **pure stdlib** — it never imports urirun, so a request is
just interpreter startup + a socket round-trip.
**Measured: 515 → 35.9 ms/call (≈14×).** `urirun/runtime/daemon.py`.

### 6. Flow / batch reuse
Flows (example 17) re-resolve the registry per step. Reuse one discovered registry + one
worker pool across all steps of a flow.

---

## Status

**1, 2, 3, 4, 5 done** (above; 1/2/3/5 measured, 4 is the connector default now).
Combined effect on a single
`time://` call: a fresh `urirun run` went 339→246 ms in import alone (#1) and never
re-imports the whole runtime for `list`/`registry://` (#2); a served node's `/run`
went 245→5.9 ms (#3); and the daemon path is 515→36 ms (#5). 6 (one registry + one
pool across a flow's steps) now mostly falls out of 1 + 3 — apply it inside the flow
runner if a flow's per-step latency ever matters.

## Summary table (measured, this machine)

| optimization | before | after | factor |
| --- | --: | --: | --: |
| #1 lazy discovery (fresh-proc import) | 339 ms | 246 ms | 1.4× |
| #2 registry cache (warm) | 30 ms | 10 ms | 3× |
| #3 warm worker in `node serve` (/run) | 245 ms | 5.9 ms | 42× |
| #5 daemon + stdlib client | 515 ms | 36 ms | 14× |

> Measurement scripts: `examples/20-runtime-transport-matrix/`,
> `examples/22-warm-worker/bench.py`.
