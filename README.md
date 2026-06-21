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
| 05 | [`05-generators/`](05-generators/) | JS, Node.js, TypeScript, PHP, Go and C generation | ✅ js/node/ts/php/go/c |
| 06 | [`06-html_uri_app/`](06-html_uri_app/) | browser UI calling a Python backend via URI | ✅ `test.mjs` |
| 07 | [`07-transports/`](07-transports/) | local, queue, serverless, HTTP, gRPC | ✅ `test_transports.py` |
| 08 | [`08-multi_transport/`](08-multi_transport/) | HTTP + gRPC worker transport demo | needs Docker |
| 09 | [`09-docker_uri_flow/`](09-docker_uri_flow/) | Compose services over URI resources | ✅ host tests; flow needs Docker |
| 10 | [`10-device_mesh_lab/`](10-device_mesh_lab/) | dashboard, device agents, `browser://` routes | ✅ host tests |
| 11 | [`11-novnc_lan_flow/`](11-novnc_lan_flow/) | multi-computer noVNC LAN workflow | ✅ Docker/noVNC `make test-full` |
| 12 | [`12-full_e2e_connect_lab/`](12-full_e2e_connect_lab/) | get/connect/ifuri public smoke + pc1/pc2 Docker E2E + connector/MCP/A2A checks | ✅ public smoke; full flow needs Docker |
| 13 | [`13-simple_defaults/`](13-simple_defaults/) | convention-based connector defaults in Python and JS | ✅ python/js validate |
| 14 | [`14-llm-uri-agent/`](14-llm-uri-agent/) | LLM-over-URI agent loop: registry as action space, drive Chrome + tools by URI under policy | ✅ `pytest` |

See [`AUTOMATION-INTEGRATIONS.md`](AUTOMATION-INTEGRATIONS.md) for the URI→registry→LLM
pattern and a plan for browser/email/KSeF/government connectors.

All host-runnable checks pass with `urirun` installed (e.g. from
`github.com/if-uri/urirun`). Docker-based demos (08, 11 and the full 09 flow)
require Docker.

The noVNC LAN flow now has a full four-computer smoke test:

```bash
cd 11-novnc_lan_flow
make test-full
```

It executes 16 URI steps across 24 generated routes and verifies screenshots
from `pc1`, `pc2`, `pc3` and `pc4`.

Full installer/connector/registry scenario:

```bash
cd 12-full_e2e_connect_lab
make test
```

The full Docker scenario installs available connectors from
`connect.ifuri.com`, runs host-node communication across `pc1` and `pc2`,
executes connector URI routes, verifies gRPC transport, and checks MCP tools plus
A2A skills. Current connector Docker coverage is `planfile`, `sqlite-context`,
`domain-monitor`, `http-check`, `time-tools`, `namecheap-dns`,
`browser-control` and `grpc-transport`; planned catalog entry `mqtt` is
reported as skipped until its package exists.

## Run all tests

```bash
make test          # or: ./run_tests.sh
```

Runs the host-runnable check for every `NN-*` example and prints a summary.
It auto-detects a Python with `urirun` (prefers `../app/.venv`; override with
`PYTHON=...`) and skips the Docker-only demos (08, 11 and the full 09 flow).
Current host run: **20 passed, 0 failed, 4 skipped**.

## Related repositories

- `github.com/if-uri/app`
- `github.com/if-uri/docs`
- `github.com/if-uri/connect.ifuri.com`
- `github.com/if-uri/get`
- `github.com/if-uri/urirun-connector-browser-control`
- `github.com/if-uri/urirun-connector-http-check`
- `github.com/if-uri/urirun-connector-time-tools`
- `github.com/if-uri/urirun`
- `roadmap.ifuri.com` / `github.com/if-uri/roadmap`

Current cross-repository implementation summary:
[`if-uri/docs/work-summary-2026-06-20.md`](https://github.com/if-uri/docs/blob/main/work-summary-2026-06-20.md).

Repository notes: [TODO.md](TODO.md) · [CHANGELOG.md](CHANGELOG.md)

## License

Released under the terms in [LICENSE](LICENSE).
