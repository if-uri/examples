# Examples backlog

These examples are useful but were not implemented in this pass because they
need hardware, secrets, a self-hosted runner, or a larger product fix.

## `54-human-task-provider`

- Repositories: `urirun-connectors/urirun-connector-human`, `if-uri/urirun-flow`
- Goal: demonstrate `human://{node}/task/command/request`, poll, resolve,
  decline and cancel as first-class URI flow steps.
- Scenario: local task store, deterministic operator resolve, event trace.
- Requirements: Python only; no real human in CI.
- Class: `host`
- Dependencies: install `human-connector` from sibling checkout or package.
- Acceptance: tests cover `done`, `declined`, `cancel`, timeout and per-env
  recall without caching per-instance decisions.
- Not done now: needs a stable package install path for standalone `examples`
  CI, otherwise the example would depend on a private sibling checkout.

## `55-pc1-pc2-customer-buyer-human`

- Repositories: `pc1`, `pc2`, `pc-user-pl`, `net-user-pl`, `mobile-user-pl`,
  `ifuri-buyer`, `ifuri-customer`, `human-connector`, `report`
- Goal: end-to-end buyer/customer digital-persona journey.
- Scenario: customer creates an order, buyer reviews it, human approval is
  captured, report renders the event bus trace.
- Requirements: Docker, noVNC, local CA, multiple nodes.
- Class: `docker`
- Dependencies: the digital-twin repositories and local images.
- Acceptance: pc1 and pc2 have distinct node IDs, ports and profiles; report
  contains screenshots, DOM/OCR evidence, JUnit and Markdown summary.
- Not done now: the real `pc2`, `ifuri-buyer` and `ifuri-customer` repositories
  were discovered during this task but are not checked out locally.

## `56-browser-extension-node`

- Repositories: `chrome-plugin`, `firefox-plugin`, `urirun-connector-browser-control`
- Goal: show browser extension as a URI node.
- Scenario: extension registers a browser tab, host sends observe/query command.
- Requirements: browser automation with extension support.
- Class: `self-hosted`
- Dependencies: Chrome/Firefox extension packaging.
- Acceptance: CI artifact contains browser logs and a verified DOM observation.
- Not done now: GitHub-hosted headless browser extension testing needs extra
  setup and stable extension build artifacts.

## `57-document-pdf-sheet-office`

- Repositories: `urirun-connector-document`, `urirun-connector-pdf`,
  `urirun-connector-sheet`, `urirun-connector-invoice`
- Goal: offline office pipeline from invoice text to spreadsheet and PDF report.
- Scenario: parse fixture invoice, write CSV/XLSX, render Markdown report to PDF.
- Requirements: Python; optional pure-Python XLSX/PDF dependencies.
- Class: `host`
- Dependencies: connector packages must have compatible public bindings.
- Acceptance: generated CSV/PDF are compared to expected fixtures.
- Not done now: several connector repos are not locally installed; avoid copying
  production handlers into examples.

## `58-fleet-nodeadmin-reconcile`

- Repositories: `urirun-fleet`, `urirun-connector-nodeadmin`
- Goal: desired-vs-actual node reconciliation with readiness gate.
- Scenario: fake node reports drift, fleet computes plan, nodeadmin applies a
  dry-run rollback-safe action.
- Requirements: local fake node server.
- Class: `host`
- Dependencies: stable fleet CLI/API.
- Acceptance: idempotent second run reports no drift.
- Not done now: needs the product API surface to be finalized.

## `59-android-node-service`

- Repositories: `urirun-android-node-app`, `urirun-service-android-node`,
  `urirun-connector-adb`
- Goal: Android device as a URI node.
- Scenario: build/install app, register node, execute ADB-backed query.
- Requirements: physical Android device or emulator with ADB.
- Class: `hardware`
- Dependencies: Android SDK/Buildozer/ADB.
- Acceptance: device health and one URI command pass with captured logs.
- Not done now: requires hardware or an Android-capable self-hosted runner.

## `60-website-event-uri-ingest`

- Repositories: `js-urirun-com`, `web-urirun-com`
- Goal: browser page emits website events as URIs and PHP panel ingests them.
- Scenario: local static page sends event to local PHP endpoint, dashboard reads it.
- Requirements: PHP built-in server and Node or Playwright.
- Class: `host`
- Dependencies: web collector API.
- Acceptance: test verifies stored URI event and redaction of sensitive fields.
- Not done now: collector authentication contract needs to be checked against
  the current PHP implementation.
