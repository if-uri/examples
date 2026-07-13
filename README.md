# ifURI examples

Runnable examples for `urirun` and ifURI-style URI workflows.

This repository was split out from:

```text
tellmesh/urihandler/v2/examples
```

## Examples

Numbered roughly from basics to advanced. Each folder is `NN-name/` with its own
`README.md`.

CI classification lives in `ci/examples-manifest.yml`. Every `NN-*` directory
must be listed there as `host`, `docker`, `service`, `hardware`, `self-hosted`,
`manual` or `external-secret`. Runnable classes need a command; skipped classes
need a concrete technical reason. Operators can run:

```bash
make ci-classification
make ci-host
make ci-docker
```

An unclassified new directory fails with
`Unclassified example: NN-example-name` and asks to add it to the manifest.
Ecosystem-wide repository coverage is tracked in `ci/ecosystem-coverage.yml`
and summarized in [`docs/ECOSYSTEM_COVERAGE.md`](docs/ECOSYSTEM_COVERAGE.md).

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
| 11 | [`11-novnc_lan_flow/`](11-novnc_lan_flow/) | multi-computer noVNC LAN workflow | Docker/noVNC `make test-full` |
| 11 | [`11-tellmesh-uri-flow/`](11-tellmesh-uri-flow/) | adopt tellmesh capability packs as URIs with no code change, then run | ✅ `test_packs.py` |
| 12 | [`12-full_e2e_connect_lab/`](12-full_e2e_connect_lab/) | get/connect/ifuri public smoke + pc1/pc2 Docker E2E + connector/MCP/A2A checks | ✅ public smoke; full flow needs Docker |
| 13 | [`13-simple_defaults/`](13-simple_defaults/) | convention-based connector defaults in Python and JS | ✅ python/js validate |
| 14 | [`14-llm-uri-agent/`](14-llm-uri-agent/) | LLM-over-URI agent loop: registry as action space, drive Chrome + tools by URI under policy | ✅ `pytest` |
| 15 | [`15-declarative-http/`](15-declarative-http/) | declarative HTTP/REST connectors from a TOML spec (httpbin + KSeF 2.0), templated url/headers/body | ✅ host run |
| 15 | [`15-llm-yaml-repair/`](15-llm-yaml-repair/) | NL → LLM builds a YAML flow → execute → on failure feed the error back → corrected flow (self-repair) | ✅ `pytest` |
| 16 | [`16-secrets/`](16-secrets/) | `secret://` / `getv://` — credentials by reference, execute-only, deny-by-default, redacted, no leak | ✅ `pytest` |
| 17 | [`17-flows/`](17-flows/) | usage scenarios as flows in txt / bash / YAML; `run_flow.py` runner with policy + result chaining | ✅ `pytest` |
| 18 | [`18-connector-transport/`](18-connector-transport/) | docker-compose: serve any connector (domain-monitor) over HTTP via `urirun node serve`; a client with no connector drives it over the URI contract | `docker compose up` |
| 18 | [`18-openapi-import/`](18-openapi-import/) | OpenAPI → URI routes, secured by reference (`run.py`) | demo `run.py` |
| 19 | [`19-all-connectors/`](19-all-connectors/) | check all connectors (Python/PHP/Go/JS) through one contract: bindings→validate→compile→run | ✅ `pytest` |
| 19 | [`19-uri-tree/`](19-uri-tree/) | install a set of connectors with one line, then view their URIs as a tree | scripts |
| 20 | [`20-runtime-transport-matrix/`](20-runtime-transport-matrix/) | the thesis: connectors in Go/PHP/JS/Python × transports inprocess/queue(MQTT)/HTTP/MCP — identical output | ✅ `pytest` |
| 21 | [`21-generate-from-binding/`](21-generate-from-binding/) | generate protobuf/gRPC + OpenAPI + a typed client from one URI binding spec (typed `inputSchema`) | ✅ `pytest` |
| 22 | [`22-warm-worker/`](22-warm-worker/) | warm-worker pool: amortize the interpreter cold start for argv-template connectors (268ms→4ms, 69×) | host run |
| 23 | [`23-embedded-urirun/`](23-embedded-urirun/) | embed the urirun layer directly instead of installing a connector | ✅ `pytest` |
| 23 | [`23-llm-flow-repair/`](23-llm-flow-repair/) | self-repairing LLM flow over `llm://` (pick model + provider) | ✅ `pytest` |
| 24 | [`24-adopt-existing-stack/`](24-adopt-existing-stack/) | adopt urirun into an existing multi-language stack (real services + functions) | ✅ `pytest` |
| 24 | [`24-adopt-tellmesh-packs/`](24-adopt-tellmesh-packs/) | adopt ~50 tellmesh libraries into one URI registry (reuse, don't rewrite) | ✅ `pytest` |
| 25 | [`25-tellmesh-uri-flow/`](25-tellmesh-uri-flow/) | a multi-step URI flow across tellmesh packs (executed, not just resolved) | ✅ `pytest` |
| 26 | [`26-agent-uri-flow/`](26-agent-uri-flow/) | an agent composes a URI flow from the action space | ✅ `pytest` |
| 27 | [`27-agent-llm-rdp/`](27-agent-llm-rdp/) | a real LLM agent drives a computer-control task over tellmesh URIs | ✅ `pytest` |
| 28 | [`28-llm-novnc-desktop/`](28-llm-novnc-desktop/) | an LLM drives a real noVNC desktop from a natural-language intent | ✅ `pytest`; live needs noVNC/Docker |
| 29 | [`29-mcp-desktop-agent/`](29-mcp-desktop-agent/) | the desktop as MCP tools: an LLM drives it with native tool-calling | ✅ `pytest`; live needs noVNC + LLM |
| 30 | [`30-mesh-no-rdp/`](30-mesh-no-rdp/) | control one computer from another without RDP (urirun mesh, least privilege) | ✅ `pytest` |
| 31 | [`31-llm-remote-office/`](31-llm-remote-office/) | drive a remote computer's office work from natural language (LLM → URI → mesh) | ✅ `pytest` |
| 32 | [`32-host-ask-over-relay/`](32-host-ask-over-relay/) | drive a NAT'd node from natural language end-to-end through the `mesh.urirun.com` relay (discover + plan + execute) | `run.sh` |
| 32 | [`32-task-scenarios/`](32-task-scenarios/) | YAML task scenarios + a live event stream from the node | ✅ `pytest` |
| 33 | [`33-office-automation-mcp/`](33-office-automation-mcp/) | 6 office tasks from NL over an MCP tool surface (windows/browser/email/files/calendar) — ≥10-step flows, each **verified** | ✅ `pytest` |
| 34 | [`34-all-connectors-flow/`](34-all-connectors-flow/) | install AND use every connector via two YAML flows (`pkg://` install step + a route per connector) | ✅ `pytest` |
| 35 | [`35-deploy-lenovo-surface/`](35-deploy-lenovo-surface/) | deploy a browser/office/tools surface onto a remote node over POST /deploy (no SSH); real headless-Chrome control from the host | live on a node |
| 36 | [`36-remote-browser-cdp/`](36-remote-browser-cdp/) | control a remote browser over Chrome DevTools Protocol (`browser://<node>/cdp/*`) — launch/navigate/eval-JS/screenshot/tabs; Wayland-safe | ✅ `e2e.sh` + live on a node |
| 37 | [`37-closed-loop-automation/`](37-closed-loop-automation/) | three closed-loop automation patterns (self-repair · goal-verify · agent) — NL→YAML flow→execute→feedback→re-plan | ✅ `pytest` (offline) + live |
| 38 | [`38-self-managing/`](38-self-managing/) | self-managing urirun: capability→connector resolver + a loop that installs a missing connector mid-run (gap→resolve→provision→re-plan) | ✅ `pytest` + `resolver.py` |
| 39 | [`39-browser-observe/`](39-browser-observe/) | autonomous READ-ONLY browser observation: portal screen-capture + vision-LLM as URIs; hard gate refuses publish/DM/login/payment | live (capture + vision) |
| 39 | [`39-local-social-autonomy/`](39-local-social-autonomy/) | controlled LinkedIn-shaped site with `.env` login + full autonomous browser publication on locally mapped `linkedin.com:<port>` | ✅ `pytest` + local Chrome CDP |
| 40 | [`40-wordpress-article/`](40-wordpress-article/) | create a WordPress article over a URI via the REST API + Application Password (by reference); draft by default | ✅ `pytest` (fake WP) |
| 40 | [`40-local-portals-suite/`](40-local-portals-suite/) | local CRM/support/shop/docs portals for prompt-driven autonomous browser tests over `portal://*.local` | ✅ `pytest` + local Chrome CDP |
| 41 | [`41-invoice-audit-flow/`](41-invoice-audit-flow/) | invoice audit and filesystem cleanup over a urirun node | ✅ `pytest` |
| 42 | [`42-host-compute-node-ocr/`](42-host-compute-node-ocr/) | use the stronger host/NVIDIA machine for OCR while the documents stay on a node | ✅ `pytest` |
| 43 | [`43-camera-usb-ocr-inspection/`](43-camera-usb-ocr-inspection/) | USB camera discovery + audible pre-scan beep + camera OCR/inspection/alert URI flows | ✅ `pytest` (static) + optional live node |
| 44 | [`44-ksef-token-via-browser/`](44-ksef-token-via-browser/) | assisted KSeF token capture via the browser (Aplikacja Podatnika) | ✅ `pytest` |
| 44 | [`44-phone-webrtc-scanner-dashboard/`](44-phone-webrtc-scanner-dashboard/) | phone camera scanner through dashboard `/scanner`, chat attachments and OCR metadata | dashboard API tests |
| 45 | [`45-ksef-send-faktura/`](45-ksef-send-faktura/) | send a KSeF FA(2) invoice — the last leg of the office pipeline (plan-ready) | ✅ `pytest` |
| 46 | [`46-connect-anything/`](46-connect-anything/) | connect anything through URI adoption (`adopt://` inspect/plan/scan) | ✅ `pytest` |
| 47 | [`47-android-nexus7-node/`](47-android-nexus7-node/) | an Android tablet (Nexus 7) as a urirun node | needs adb device |
| 47 | [`47-nl-desktop-control/`](47-nl-desktop-control/) | NL → `ui://` plan → execute (autonomous desktop control via `kvm://.../ui/*`) | scripts; needs node |
| 48 | [`48-api-device-node/`](48-api-device-node/) | register external APIs and multi-interface devices as nodes | demo scripts |
| 49 | [`49-linkedin-compose-cdp/`](49-linkedin-compose-cdp/) | compose a LinkedIn post over Chrome DevTools Protocol (`run.py`) | demo `run.py` |
| 50 | [`50-contract-guarded-flow/`](50-contract-guarded-flow/) | reuse a connector in a flow, its **contract** guards every step (honest passes, drift caught); same `contracts.json` drives the JS/Go SDK guards | ✅ `pytest` |
| 51 | [`51-router-guarded-autonomy/`](51-router-guarded-autonomy/) | the autonomy safety stack: agent decides a plan → **router** diagnoses WHERE each step runs (blocks unroutable pre-flight) → **contract** guards executed envelopes | ✅ `pytest` |
| 52 | [`52-office-vm-rdp-novnc/`](52-office-vm-rdp-novnc/) | office work on a **virtual machine over RDP**, surfaced through a **noVNC** HTML5 canvas: NL → ≥10-step flow (vm/rdp/novnc/desktop/fs/clipboard) → verify the task happened **and** RDP/noVNC tore down cleanly; `--live` drives a real noVNC desktop | ✅ `pytest` |
| 53 | [`53-ecosystem-coverage-audit/`](53-ecosystem-coverage-audit/) | audits the full if-uri repository inventory against the examples coverage map | ✅ `pytest` |

See [`AUTOMATION-INTEGRATIONS.md`](AUTOMATION-INTEGRATIONS.md) for the URI→registry→LLM
pattern and a plan for browser/email/KSeF/government connectors.

The fast host smoke passes with `urirun` installed (e.g. from
`github.com/if-uri/urirun`). The full host pytest suite covers the broader
offline examples. Docker-based demos (08, 11 and the full 09/12 flows) require
Docker.

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

## Run tests

```bash
make connectors    # one-time: install urirun + every sibling connector editable
make test          # fast smoke, or: ./run_tests.sh
make test-all      # full host pytest suite
make audit         # show smoke coverage gaps
```

`make test-all` imports the sibling connector packages (e.g. `urirun_declarative`,
`urirun_connector_invoice`, `urirun_connector_time_tools`), so run `make connectors`
once first — or point `PYTHON=` at an already-provisioned venv such as `examples/venv`.
Without them those example modules fail to import (collection errors), even though the
examples themselves are fine.

`make test` auto-detects a Python with `urirun` (prefers `../app/.venv`;
override with `PYTHON=...`) and skips the Docker-only demos (08, 11 and the
full 09/12 flows). It is a smoke runner, not a complete sweep of every pytest-based
example; the built-in audit reports that distinction. Current smoke run:
**21 passed, 0 failed, 4 skipped** (Docker-only demos skipped). Current full
host pytest run: **271 passed, 2 skipped**.

## Related repositories

- `github.com/if-uri/app`
- `github.com/if-uri/docs`
- `github.com/if-uri/connect.ifuri.com`
- `github.com/if-uri/get-ifuri-com`
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
