# if-uri ecosystem coverage

Generated from the paginated GitHub organization repository list on 2026-07-13
and checked against `ci/ecosystem-coverage.yml`.

## Summary

- Total repositories reviewed: 127
- Active repositories: 91
- Complete coverage: 14
- Partial coverage: 61
- Missing coverage: 29
- Not applicable: 18
- Deprecated: 5
- Current numbered examples: 65
- New catalog/audit example: `53-ecosystem-coverage-audit`

Important P0 gaps:

- `human-connector`: first-class `human://` flow example is still missing.
- `pc1`, `pc2`, `ifuri-buyer`, `ifuri-customer`: the cross-repository buyer/customer digital-persona journey needs a dedicated example in `examples`.

Important P1 gaps:

- Browser extension coverage for `chrome-plugin` and `firefox-plugin`.
- API adapters: `urirun-api-mcp`, `urirun-api-a2a`; REST/OpenAI proxy: `llm-urirun-com`.
- Connector generation, fleet/node administration and headless document/PDF examples.
- Session report generation from the digital-twin event bus.

## Capability map

| Area | Repositories | Examples today | Gap |
| --- | --- | --- | --- |
| URI runtime, bindings, registry, validation | `urirun`, `urirun-runtime`, `urirun-connectors-toolkit` | `01-json`, `04-python`, `05-generators`, `07-transports` | Mostly covered; keep aligned with current CLI. |
| Flow, router, contracts, recovery | `urirun-flow`, `urirun-contract`, `urirun-connector-router`, `urirun-connector-urifix` | `17-flows`, `23-llm-flow-repair`, `50-contract-guarded-flow`, `51-router-guarded-autonomy` | Add focused urifix retry/recovery example. |
| Host, node, mesh, relay | `urirun-node`, `mesh-urirun-com`, `urirun-connector-get-node`, `urirun-connector-nodeadmin` | `30-mesh-no-rdp`, `32-host-ask-over-relay`, `46-connect-anything` | Add nodeadmin upgrade/rollback and get-node doctor examples. |
| Browser, CDP, KVM, noVNC, RDP | `urirun-cdp`, `urirun-connector-kvm`, `urirun-connector-browser-control`, `urirun-uinput` | `28-llm-novnc-desktop`, `36-remote-browser-cdp`, `37-closed-loop-automation`, `52-office-vm-rdp-novnc` | Add browser extension node example. |
| Digital twin | `pc1`, `pc2`, `pc-user-pl`, `net-user-pl`, `mobile-user-pl`, `ifuri-buyer`, `ifuri-customer`, `report` | `12-full_e2e_connect_lab` | Add customer/buyer/persona/report journey. |
| Human-in-the-loop | `human-connector` | none dedicated | P0: add `human-task-provider`. |
| LLM and autonomy | `urirun-connector-llm`, `urirun-llm-runtime`, `urirun-reasoner`, `urirun-mind`, `urirun-work`, `urirun-inquiry` | `14-llm-uri-agent`, `15-llm-yaml-repair`, `23-llm-flow-repair`, `38-self-managing` | Add reasoner and work-scheduler examples. |
| Documents, office, accounting | `urirun-connector-document`, `urirun-connector-pdf`, `urirun-connector-sheet`, `urirun-connector-invoice`, `urirun-connector-ksef` | `33-office-automation-mcp`, `44-ksef-token-via-browser`, `45-ksef-send-faktura` | Add offline document/PDF/sheet/invoice fixtures. |
| Devices | `urirun-android-node-app`, `urirun-service-android-node`, `urirun-connector-adb`, `urirun-connector-camera`, `urirun-connector-usb` | `43-camera-usb-ocr-inspection`, `47-android-nexus7-node` | Hardware examples remain P3/self-hosted. |
| Websites and installers | `get-ifuri-com`, `get-urirun-com`, `connect.ifuri.com`, `web-urirun-com`, `js-urirun-com` | `46-connect-anything`, `53-ecosystem-coverage-audit` | Add installer and website event-ingest smoke. |

## Coverage table

The machine-readable complete table is `ci/ecosystem-coverage.yml`. This human
report lists the main active and high-risk entries.

| Repository | Status | Main function | urirun relation | Current example | Coverage | Missing example | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `if-uri/urirun` | active | Core URI runtime, host/node, CLI | core | `01-json`, `04-python`, `07-transports`, `17-flows` | complete | keep CLI current | P1 |
| `if-uri/examples` | active | Runnable catalog | catalog | `53-ecosystem-coverage-audit` | complete | none | P0 |
| `if-uri/human-connector` | active | Human task provider over `human://` | connector | none dedicated | partial | `human-task-provider` | P0 |
| `digitaltwin-run/pc1` | active | Digital twin orchestration | E2E lab | `12-full_e2e_connect_lab` | partial | `pc1-pc2-customer-buyer-human` | P0 |
| `digitaltwin-run/pc2` | active | Operator host for twin | E2E lab | none | missing | `pc1-pc2-customer-buyer-human` | P0 |
| `digitaltwin-run/ifuri-buyer` | active | Buyer persona | digital persona | none | partial | `buyer-customer-digital-personas` | P0 |
| `digitaltwin-run/ifuri-customer` | active | Customer persona | digital persona | none | partial | `buyer-customer-digital-personas` | P0 |
| `digitaltwin-run/net-user-pl` | active | Offline virtual internet | service/twin | `12-full_e2e_connect_lab` | complete | none | P1 |
| `digitaltwin-run/pc-user-pl` | active | Desktop node | node/twin | `12-full_e2e_connect_lab` | complete | none | P1 |
| `digitaltwin-run/mobile-user-pl` | active | SMS phone twin | node/twin | `12-full_e2e_connect_lab` | complete | none | P1 |
| `digitaltwin-run/urirun-twin-human` | active | Human actors exposed as URI processes | actor/twin | none | missing | `human-twin-actor` | P1 |
| `digitaltwin-run/report` | active | Session reports from event bus | evidence/reporting | none | missing | `eventbus-session-report` | P1 |
| `if-uri/urirun-api-rest` | archived | Retired duplicate of `llm-urirun-com` | none | — | deprecated | none | — |
| `if-uri/urirun-contract-{capture-click,filepair,kvstore,windowpair}` | archived | Completed contract-package experiments; descriptors moved to `urirun-capability/contracts` | capability migration fixtures | — | deprecated | none | — |
| `if-uri/urirun-api-mcp` | active | MCP API adapter | API surface | `29-mcp-desktop-agent` | partial | `api-mcp-adapter` | P1 |
| `if-uri/urirun-api-a2a` | active | A2A API adapter | API surface | `04-python` | partial | `api-a2a-adapter` | P1 |
| `if-uri/urirun-connector-kvm` | active | KVM input/screen | connector | `28`, `37`, `52` | complete | none | P1 |
| `if-uri/urirun-connector-router` | active | Routing guard | connector | `51-router-guarded-autonomy` | complete | none | P1 |
| `if-uri/urirun-contract` | active | Route contracts | contract layer | `50`, `51` | complete | none | P1 |
| `if-uri/urirun-flow` | active | Typed flow authoring | flow layer | `17`, `25`, `34` | complete | none | P1 |
| `if-uri/urirun-connector-document` | active | Headless docs | connector | none | missing | `headless-document-create` | P1 |
| `if-uri/urirun-connector-pdf` | active | PDF rendering | connector | none | missing | `markdown-to-pdf` | P1 |
| `if-uri/urirun-connector-sheet` | active | CSV/XLSX | connector | `33-office-automation-mcp` | partial | `sheet-csv-xlsx-roundtrip` | P1 |
| `if-uri/urirun-connector-invoice` | active | Invoice extraction | connector | `45-ksef-send-faktura` | partial | `invoice-folder-to-sheet` | P1 |
| `if-uri/urirun-connector-llm` | active | LLM routes | connector | `14`, `15`, `23` | complete | none | P1 |
| `if-uri/urirun-reasoner` | active | Intent to URI plan | autonomy | none | missing | `reasoner-intent-to-uri-plan` | P1 |
| `if-uri/urirun-fleet` | active | Fleet reconciliation | node ops | none | missing | `fleet-reconcile-readiness` | P1 |
| `if-uri/urirun-multiplatform-test` | test-only | Cross-platform CI | QA | `46-connect-anything` | partial | `multiplatform-install-smoke` | P1 |

## Notes

- Five retired repositories are marked `deprecated`; their maintained code or
  data has an explicit replacement recorded in the machine-readable inventory.
- Website/documentation/infrastructure repos are classified as `not-applicable`
  when they have no direct URI runtime surface.
- Hardware and external-secret examples stay in the backlog unless they can be
  tested deterministically in ordinary CI.
