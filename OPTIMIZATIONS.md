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

### 1. Lazy, scheme-indexed discovery  (biggest, cleanest)
Today: import all 17 connectors (~13 ms) to resolve one URI. Build a persisted
`scheme → entry-point` index (`.urirun/scheme-index.json`), refreshed on
`urirun install`; then `urirun run 'time://…'` imports **only** `time-tools`.
**Win:** ~13 ms → ~1 ms for the import step; scales as more connectors are installed.
Needs a cache because the scheme isn't in entry-point metadata without importing.

### 2. Compiled-registry cache
Cache the discovered+compiled registry keyed by the installed-package set; invalidate
on `install`. Removes the remaining ~12 ms scan+compile per call. Pairs with #1.

### 3. Warm-worker inside `node serve`  (highest absolute win)
Measured: a served node still cold-starts argv-template connectors per `/run` (237 ms).
Wire the `WorkerPool` (already built, `urirun.runtime.worker`) into `node serve` so each
connector keeps a warm process. **Win:** 237 ms → ~4 ms per `/run` for interpreted
connectors under load.

### 4. Hydrate `local-function` from the entry point at run time
`local-function` routes can't run via `urirun run` on a compiled registry (the callable
is lost on serialize). Re-import the ref from its entry point at dispatch. Then a pure
Python connector can be `local-function` (**~0 ms**, no spawn) instead of `argv-template`
(220 ms). This is the right default for hot pure-Python connectors — and matches the
direction the connectors are already moving.

### 5. A local `urirun` daemon (or reuse `node serve`)
Every CLI `urirun run` pays the ~28 ms interpreter cold start. For high-frequency CLI
use, a local socket daemon (or just pointing the CLI at a running `node serve`) amortizes
both the interpreter and the discovery.

### 6. Flow / batch reuse
Flows (example 17) re-resolve the registry per step. Reuse one discovered registry + one
worker pool across all steps of a flow.

---

## Priority

1 + 2 together make every `urirun run` ~10× cheaper to start (~25 ms → ~2 ms) and are
low-risk. 3 is the biggest absolute win for serving under load and reuses code already
written. 4 changes the default execution model for pure-Python connectors from 220 ms to
0 ms. 5 and 6 matter only for very high call rates.

> Measurement scripts: `examples/20-runtime-transport-matrix/`,
> `examples/22-warm-worker/bench.py`.
