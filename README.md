# ifURI examples

Runnable examples for `urirun` and ifURI-style URI workflows.

This repository was split out from:

```text
tellmesh/urihandler/v2/examples
```

## Examples

Numbered roughly from basics to advanced. Each folder is `NN-name/` with its own
`README.md`.

| # | Example | What it shows | Tested (host) |
|---|---------|---------------|---------------|
| 01 | [`01-json/`](01-json/) | binding document (JSON Schema + adapter) | ✅ validate/compile |
| 02 | [`02-decorators/`](02-decorators/) | Python decorator-generated bindings | ✅ `example.py` |
| 03 | [`03-artifacts/`](03-artifacts/) | scan Dockerfile/Makefile/package/manifest | ✅ `urirun scan` |
| 04 | [`04-python/`](04-python/) | Python adapter, adopt and MCP/A2A tests | ✅ `pytest` |
| 05 | [`05-generators/`](05-generators/) | JS, Node.js, TypeScript and PHP generation | ✅ js/node/php |
| 06 | [`06-html_uri_app/`](06-html_uri_app/) | browser UI calling a Python backend via URI | ✅ `test.mjs` |
| 07 | [`07-transports/`](07-transports/) | local, queue, serverless, HTTP, gRPC | ✅ `test_transports.py` |
| 08 | [`08-multi_transport/`](08-multi_transport/) | HTTP + gRPC worker transport demo | needs Docker |
| 09 | [`09-docker_uri_flow/`](09-docker_uri_flow/) | Compose services over URI resources | ✅ host tests; flow needs Docker |
| 10 | [`10-device_mesh_lab/`](10-device_mesh_lab/) | dashboard, device agents, `browser://` routes | ✅ host tests |
| 11 | [`11-novnc_lan_flow/`](11-novnc_lan_flow/) | multi-computer noVNC LAN workflow | needs Docker + noVNC |

All host-runnable checks pass with `urirun` installed (e.g. from
`github.com/tellmesh/urirun`). Docker-based demos (08, 11 and the full 09 flow)
require Docker.

## Related repositories

- `github.com/if-uri/app`
- `github.com/if-uri/docs`
- `github.com/tellmesh/urirun`
