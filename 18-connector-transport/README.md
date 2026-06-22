# 18 — connect a connector to any runtime over any transport

Every `urirun-connector-*` has the same shape: it emits **`urirun_bindings()`** (a v2
bindings doc). That doc compiles to a **registry**, and a registry is transport- and
runtime-agnostic — the same one runs locally, is served over HTTP, or is projected to
MCP/A2A. So a connector is *plugged into a runtime*, not bound to one.

This demo takes the **`domain-monitor`** connector and:

```
domain-monitor connector ──▶ urirun_bindings() ──▶ compiled registry
        │
        ▼  served over HTTP by `urirun node serve --allow 'monitor://*'`   (the transport)
   ┌──────────┐        POST /run {uri, payload}        ┌──────────────────────────┐
   │  client  │ ───────────────────────────────────▶  │ node (has the connector) │
   │ (no      │ ◀───────── result envelope ─────────── │  /health /routes         │
   │ connector│                                        │  /mcp/tools /a2a/card    │
   └──────────┘                                        └──────────────────────────┘
```

The **client container has urirun but NOT the connector** — it drives `monitor://...`
purely over the URI + HTTP contract. Swap the client for `curl`, an MCP client, or
another node and nothing changes.

## Run

```bash
docker compose up --abort-on-container-exit --exit-code-from client
```

Three services: **target** (an nginx site to monitor), **node** (serves the connector
over HTTP), **client** (calls it, no connector installed). Expected:

```
node /routes    == 8 connector routes exposed over HTTP
node /mcp/tools == 8 MCP tools (same registry)
monitor://host/http/query/status OVER HTTP: ok=True | http status: 200
browser route (not in --allow): refused   ← transport security boundary
```

## The two pieces that make it transport-agnostic

1. **`urirun_bindings()` → registry.** `node/serve.sh` builds the registry straight
   from the connector — no connector-specific server code.
2. **`urirun node serve`.** Exposes the registry over HTTP (`/run`, `/health`,
   `/routes`, `/mcp/tools`, `/a2a/card`). The operator's **`--allow` glob is the
   security boundary** — only matching routes execute; everything else is denied even
   though it is listed. Secrets are off on a node unless `--allow-secrets`.

## Other transports, same registry

- **local:** `urirun run 'monitor://host/http/query/status' registry.json --execute --allow 'monitor://*'`
- **forwarding:** point `URI_SERVICE_MAP` at the node so a local `monitor://` URI is
  transparently dispatched to the remote node.
- **MCP / A2A:** the node already serves `/mcp/tools` and `/a2a/card` from the same registry.

Any `urirun-connector-*` works here — replace the image's connector and the `--allow`
glob; the node, client and transport are unchanged.
