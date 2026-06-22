# 22 — warm-worker pool (amortize the cold start)

`argv-template` runs each URI as a fresh OS process. For a **compiled** connector
that's ~2 ms; for an **interpreted** one (Python/Node) it's the interpreter +
package import cold start on *every* call — ~220–270 ms. The `WorkerPool`
(`urirun.runtime.worker`) keeps one connector process alive, imports it **once**,
and runs each request in-process over a pipe.

```bash
python3 bench.py
```

Measured on `sqlite-context` (`log://host/logs/query/recent`):

```
correctness: cold ok=True warm ok=True same-shape=True

  process-per-URI (cold spawn)            267.6 ms/call
  warm-worker pool (import once)            3.9 ms/call

  SPEEDUP: 69x   (268 ms -> 3.9 ms/call)
```

Same result, **69× faster** — the cold start is paid once, not per call.

## When to use which (the design answer)

| Model | adapter | cost/call | use when |
| --- | --- | --- | --- |
| process-per-URI | `argv-template` / `spawn` | 2 ms (Go) · ~220 ms (Python/Node) | isolation, polyglot, untrusted, low-frequency, compiled binaries |
| **warm-worker pool** | `WorkerPool` | **~4 ms** | high throughput on an **interpreted** connector |
| in-process | `local-function` | ~0 ms | hot pure-Python paths, shared state |
| remote | `fetch` / node `/run` | network | services / APIs |

> Note: `urirun node serve` does **not** amortize this for `argv-template` — its
> `/run` still spawns the connector per request. The warm-worker pool is what
> reuses the process. So: keep process-per-URI as the safe default; reach for the
> pool (or `local-function`, or a compiled binary) only on hot interpreted paths.

`WorkerPool(cli_ref)` spawns `python -m urirun.runtime.worker <module:main>`,
which imports the connector CLI once and answers `{"argv": [...]}` requests.
`pool.run_uri(uri, registry, payload)` renders the route's argv template for you.
