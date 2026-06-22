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
| 15 | [`15-declarative-http/`](15-declarative-http/) | declarative HTTP/REST connectors from a TOML spec (httpbin + KSeF 2.0), templated url/headers/body | ✅ host run |
| 16 | [`16-secrets/`](16-secrets/) | `secret://` / `getv://` — credentials by reference, execute-only, deny-by-default, redacted, no leak | ✅ `pytest` |
| 17 | [`17-flows/`](17-flows/) | usage scenarios as flows in txt / bash / YAML; `run_flow.py` runner with policy + result chaining | ✅ `pytest` |
| 18 | [`18-connector-transport/`](18-connector-transport/) | docker-compose: serve any connector (domain-monitor) over HTTP via `urirun node serve`; a client with no connector drives it over the URI contract | ✅ `docker compose up` |
| 19 | [`19-all-connectors/`](19-all-connectors/) | check all 17 connectors (Python/PHP/Go/JS) through one contract: bindings→validate→compile→run | ✅ `pytest` |
| 20 | [`20-runtime-transport-matrix/`](20-runtime-transport-matrix/) | the thesis: connectors in Go/PHP/JS/Python × transports inprocess/queue(MQTT)/HTTP/MCP — identical output | ✅ `pytest` |
| 21 | [`21-generate-from-binding/`](21-generate-from-binding/) | generate protobuf/gRPC + OpenAPI + a typed client from one URI binding spec (typed `inputSchema`) | ✅ `pytest` |
| 22 | [`22-warm-worker/`](22-warm-worker/) | warm-worker pool: amortize the interpreter cold start for argv-template connectors (268ms→4ms, 69×) | ✅ host run |
| 14 | [`14-llm-uri-agent/`](14-llm-uri-agent/) | LLM-over-URI agent loop: registry as action space, drive Chrome + tools by URI under policy | ✅ `pytest` |
| 15 | [`15-llm-yaml-repair/`](15-llm-yaml-repair/) | NL → LLM builds a YAML flow → execute → on failure feed the error back → corrected flow (self-repair) | ✅ `pytest` |
| 32 | [`32-host-ask-over-relay/`](32-host-ask-over-relay/) | drive a NAT'd node from natural language end-to-end through the `mesh.urirun.com` relay (discover + plan + execute) | ✅ `run.sh` |
| 33 | [`33-office-automation-mcp/`](33-office-automation-mcp/) | 6 office tasks from NL over an MCP tool surface (windows/browser/email/files/calendar) — ≥10-step flows, each **verified** | ✅ `pytest` |
| 34 | [`34-all-connectors-flow/`](34-all-connectors-flow/) | install AND use every connector via two YAML flows (`pkg://` install step + a route per connector); 7 ran · 8 config-gated · 0 broken | ✅ `pytest` |
| 35 | [`35-deploy-lenovo-surface/`](35-deploy-lenovo-surface/) | deploy a browser/office/tools surface onto a remote node over POST /deploy (no SSH); real headless-Chrome control from the host | ✅ live on a node |
| 36 | [`36-remote-browser-cdp/`](36-remote-browser-cdp/) | control a remote browser over Chrome DevTools Protocol (`browser://<node>/cdp/*`) — launch/navigate/eval-JS/screenshot/tabs; Wayland-safe, no input tools | ✅ `e2e.sh` (local) + live on a node |
| 37 | [`37-closed-loop-automation/`](37-closed-loop-automation/) | three closed-loop automation patterns (self-repair · goal-verify · agent) — NL→YAML flow→execute→feedback→re-plan, pluggable LLM/heuristic/stub planner | ✅ `pytest` (offline) + live on a node |
| 38 | [`38-self-managing/`](38-self-managing/) | proposal + resolver prototype for a SELF-managing urirun: map a needed capability (scheme/route/NL) to a connector + install spec across local `~/github/*`, git, hub | ✅ `resolver.py` (19 local connectors indexed) |

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
