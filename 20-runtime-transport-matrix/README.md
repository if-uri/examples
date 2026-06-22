# 20 — the thesis: urirun between any-language runtime and any transport

The claim: **urirun is the layer that sits between the runtime (connectors, in any
language) and the transport (any wire).** Neither side touches the contract — a URI
+ JSON Schema + policy + `v2.run`. So a connector's language and the transport are
independent choices.

This example proves it as a **matrix**: connectors written in **Go / PHP / JS /
Python**, each driven over **in-process / queue (≈ MQTT/NATS) / HTTP / MCP**.

```bash
python3 matrix.py
pytest test_matrix.py -q
```

```
                      inprocess   queue~MQTT  http        mcp
hash (Go)             ✓           ✓           ✓           ✓     identical out
base64 (PHP)          ✓           ✓           ✓           ✓     identical out
uuid (JS)             ✓           ✓           ✓           ✓     ok everywhere
time-tools (Python)   ✓           ✓           ✓           ✓     ok everywhere
VERDICT: urirun sits between any-language runtime and any transport ✓
```

- **Deterministic connectors (Go hash, PHP base64) return byte-identical output
  across every transport** — the transport only moves `{uri, payload}`; it never
  changes the result.
- The Python runtime **spawns the Go/PHP/JS connectors** via the URI argv; the
  transport has no idea what language is on the other end.

## The two axes, and where each is proven

| Axis | Proven by |
| --- | --- |
| transport-independent (http, mqtt/queue, mcp, grpc, serverless, in-process) | [`07-transports`](../07-transports/) — same URI, 5 transports, identical output |
| runtime/language-independent (Python, PHP, Go, JS) | [`19-all-connectors`](../19-all-connectors/) — 17 connectors, one contract |
| one connector served over a transport | [`18-connector-transport`](../18-connector-transport/) — HTTP node + MCP/A2A |
| **both axes at once (this example)** | **`20-runtime-transport-matrix`** — language × transport |

`grpc` is a real transport too (needs `grpcio`); **WebSocket is the next adapter** —
adding a transport is "move `{uri, payload}`", never a redesign.
