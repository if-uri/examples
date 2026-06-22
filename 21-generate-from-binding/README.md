# 21 — generate transport/runtime artifacts FROM a binding spec

> **Now first-class:** this generator graduated into urirun core as
> `urirun gen proto|openapi|client <registry>` (richer: a generic carrier rpc +
> typed rpc per route + a NUANCE report for JSON-Schema↔proto3 mismatches). Run
> `./gen.sh` to use it; `generate.py` below is the original standalone walkthrough.

A URI scheme binding (uri + JSON-Schema `inputSchema` + kind + adapter) is the
**single source of truth**. Because it is typed and machine-readable, you generate
everything around it instead of hand-writing per (language × transport):

```bash
python3 generate.py          # 1 binding (domain-monitor, 8 routes) -> 3 artifacts
```

```
from 1 binding spec (8 routes) generated:
  generated/service.proto   — protobuf + gRPC (8 rpc, 42 typed fields)
  generated/openapi.json    — OpenAPI 3 (8 paths)
  generated/client.py       — typed Python client (8 functions, runs)
```

- **protobuf/gRPC**: one `rpc` per route; request message fields come straight from
  `inputSchema` (string→string, integer→int64, number→double, boolean→bool, array→repeated).
- **OpenAPI 3**: one path per route; `requestBody` schema = `inputSchema`.
- **typed client**: one function per route; the generated `client.py` actually drives
  `urirun.run` (verified in the test).

Add a target (a Go client, an SSH wrapper, a Lambda handler, a TypeScript SDK) = add
a generator that reads the same registry. **N languages × M transports becomes N+M
generators, not N×M hand-written integrations.**

## Where this sits in the architecture

```
 author bindings            the contract                 project / generate
 (any language)        URI + JSON Schema + policy        (any runtime / transport)
   05-generators  ──▶  ┌──────────────────────┐  ──▶  v2_mcp (MCP tools / A2A card)
   add-openapi    ──▶  │   urirun_bindings()  │  ──▶  v2_grpc (gRPC transport)
   connector SDK  ──▶  │   = the registry     │  ──▶  v2_service (HTTP)
   from-spec      ──▶  └──────────────────────┘  ──▶  THIS: proto / openapi / clients
```

Inward (declare the contract) and outward (generate adapters) both pivot on the
registry. See [`20-runtime-transport-matrix`](../20-runtime-transport-matrix/) for the
runtime×transport proof, and [`05-generators`](../05-generators/) for the inward side.
