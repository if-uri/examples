# 22 — warm-worker pool (amortize the cold start)

`local-function-subprocess` runs each URI as a fresh OS process. For an
interpreted connector (Python/Node) that means the interpreter + package import
cold start on *every* call. The `HandlerPool` (`urirun.runtime.worker`) keeps one
handler worker alive, imports the connector **once**, and runs each request
in-process over a pipe.

```bash
python3 bench.py
```

Measured on `sqlite-context` (`log://host/logs/query/recent`):

```
correctness: cold ok=True warm ok=True same-shape=True

  local-function subprocess               345.9 ms/call
  warm handler pool                          7.3 ms/call

  SPEEDUP: 47x   (346 ms -> 7.3 ms/call)
```

Same result, **47× faster** in this run — the cold start is paid once, not per
call.

## When to use which (the design answer)

| Model | adapter | cost/call | use when |
| --- | --- | --- | --- |
| process-per-URI | `argv-template` / `local-function-subprocess` | 2 ms (Go) · ~220 ms (Python/Node) | isolation, polyglot, untrusted, low-frequency, compiled binaries |
| **warm handler pool** | `HandlerPool` | **~4 ms** | high throughput on an **interpreted** connector |
| in-process | `local-function` | ~0 ms | hot pure-Python paths, shared state |
| remote | `fetch` / node `/run` | network | services / APIs |

> Note: the default isolated path does **not** amortize this — each call still
> starts a connector subprocess. The warm pool is what reuses the process. So:
> keep process-per-URI as the safe default; reach for the pool (or
> `local-function`, or a compiled binary) only on hot interpreted paths.

`HandlerPool()` spawns `python -m urirun.runtime.worker --handler`, imports each
handler ref once, and answers `{"ref": "module:export", "payload": {...}}`
requests.
