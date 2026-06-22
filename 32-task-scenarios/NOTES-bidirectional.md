# Bidirectional channel — design assessment

> *Does receiving the node's logs/errors live (and driving it) require a refactor / a
> package rebuild, or does it fit the current urirun architecture?* Short answer:
> **the "receive logs/errors as URIs from the other side" need is met now with SSE and
> no refactor.** A *full-duplex streaming* channel (WebSocket) would need a dependency
> and a server refactor — only worth it for use-cases the request/response + SSE pair
> doesn't cover.

## What was added (no refactor, no new dependency)

- **Node → host event stream** over **Server-Sent Events**: `GET /events` on the node
  streams `run` and `error` events, each carrying a **URI** (`error://local/E-…`), the
  instant a route runs/fails. Built on the existing `ThreadingHTTPServer` with a small
  in-process `EventHub` (bounded per-subscriber queues, heartbeats, drop-on-slow).
- Host consumers: `urirun host watch <node>` / `mesh.watch_node()` / plain `curl -N`.
- This is exactly the stated requirement: *"otrzymywać od razu logi/errors w formie URI
  z drugiej strony."* It is unidirectional (node→host), which is the direction logs flow.

The host→node direction already exists as **request/response** (`POST /run`) plus
**push provisioning** (`POST /deploy`). So today's topology is:

```
host ──POST /run, /deploy────────────────►  node      (commands, request/response)
host ◄──────────── GET /events (SSE) ──────  node      (logs/errors, streaming)
```

## Why SSE, not WebSocket (for this need)

| | SSE (chosen) | WebSocket |
|---|---|---|
| direction | server→client (one-way) | full duplex |
| deps | **none** (stdlib `http.server`) | needs `websockets`/`wsproto` + an async loop |
| fits current server | yes — a long-lived GET on `ThreadingHTTPServer` | no — needs ASGI/asyncio or a WS handshake bolted on |
| reconnect/replay | built-in (`Last-Event-ID`) — not yet wired | manual |
| our payload | logs/errors flow node→host only | overkill |

For **logs/errors/telemetry** SSE is the right tool and required **zero** structural
change. WebSocket earns its keep only when the *host* must **stream** to the node (not
just call `/run`) — e.g. live input injection (mouse move stream), bidirectional media,
or interactive shells.

## Does a fuller solution need a refactor + rebuild?

**Not for the current goal.** The package shipped these as additive endpoints/commands
(`/events`, `host watch`) — backward compatible, same `urirun` package, same wheel.

A refactor **would** be warranted if you adopt any of these:

1. **Full-duplex / interactive control** (stream input to the node, live shell, media).
   → `ThreadingHTTPServer` is the wrong base. Move the node server to **ASGI**
   (`uvicorn`+`starlette`) or add a dedicated WS port. This is a real refactor of
   `node/mesh.py:serve_node` and a new optional dependency (`urirun[ws]`).
2. **Event auth + scoping.** *(done — see increment #2 below.)* `/events` is gated by the
   same token/key auth as `/run` when `--require-run-auth` is on (otherwise open, like an
   ungated `/run`), with a `?scheme=` filter and `Last-Event-ID` replay.
3. **Durable / fan-out events** across many nodes and a UI. → introduce a broker
   (the existing `mesh-urirun-com` relay, or MQTT via `urirun-connector-mqtt`) and have
   nodes *publish* events to it; the host subscribes once. This is an integration, not a
   core refactor — and it's the natural path for NAT'd nodes (SSE needs a reachable port).

## Recommended increments (in order, each shippable on its own)

1. **(done)** SSE `/events` + `host watch` — node→host logs/errors as URIs.
2. **(done)** `/events` gated behind auth when `--require-run-auth` (token or enrolled-key
   signature; 403 otherwise), a `?scheme=kvm,him,error` server-side filter, and
   `Last-Event-ID` replay from a ring buffer (`id:` lines + `host watch --follow`
   reconnect). *Additive — no refactor.*
3. Publish events to the `mesh-urirun-com` relay / MQTT for NAT'd nodes + multi-node UI.
   *(integration — no core refactor)*
4. **Only if** interactive/full-duplex control is required: add an optional ASGI/WS
   transport (`urirun[ws]`) alongside the HTTP one. *(true refactor — defer until needed)*

## Bottom line

The YAML-scenario + live-SSE-events solution demonstrated here is **production-shaped for
the stated need and needs no package rebuild beyond the additive changes already made**.
Keep WebSocket/ASGI on the roadmap, triggered specifically by an interactive-control
requirement — not by the logging/telemetry use-case, which SSE serves well.
