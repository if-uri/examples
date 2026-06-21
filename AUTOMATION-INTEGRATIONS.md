# ifURI — automation-era integrations (research + plan)

How to use `urirun` as the **action/query layer for LLM-driven automation**: every
capability is a validated URI route in one registry, an LLM picks routes, the
policy layer gates execution, and the result feeds the next decision.

This is research + a concrete plan, grounded in the connectors that already
exist (`http-check`, `time-tools`, `browser-control`, `sqlite-context`,
`domain-monitor`, `planfile`, `mqtt`, `llm`, …) and the runtime as it stands
after the layered refactor (`urirun.runtime / connectors / host / node`).

---

## 1. State of `examples/` after the runtime update

**Nothing is broken.** Examples consume the public surface (`import urirun`,
`from urirun import v2`) and the back-compat shims keep every old path working
(`urirun.v2` → `urirun.runtime.v2`, etc.). Verified: `02-decorators` runs,
`urirun validate/compile` work, `13-simple_defaults` loads.

Simplification opportunities for users (no breakage, just nicer):

| Now | Simpler with current runtime |
| --- | --- |
| `from urirun import _registry as reglib` (internal) | use public `urirun.compile_registry` / `urirun.list_routes` / `urirun.run` |
| hand-written `connector.manifest.json` + CLI boilerplate | `urirun connectors new <id> --lang …` scaffolds it |
| bespoke per-example smoke (validate→compile→run→mcp) | `… bindings \| urirun connectors smoke -` |
| connectors copying host logic | reuse `urirun.host.*` (see `connector-authoring.md` §7) |

**Recommended example refactors:** drop the `_registry` internal import in 04/07;
add a "scaffold a connector in 30 seconds" example using `urirun connectors new`;
show `connectors smoke` as the canonical one-line check.

---

## 2. The pattern: URI registry as an LLM action space

```
connectors  ──▶  one compiled registry  ──▶  projection        ──▶  LLM picks
(bindings)       (urirun compile)            (MCP tools / A2A)      a URI + payload
                                                                          │
                                       policy gate (allow/deny, execute)  ▼
                                              urirun run '<uri>' --execute  ──▶ result
                                                                          │
                                                        result feeds next decision ◀┘
```

Why this is a good substrate for automation + LLMs:

- **Uniform contract.** Email, e-invoicing, a browser, a DNS change — all become
  `scheme://target/resource/op/action` with a JSON Schema input. The LLM sees one
  shape, not N bespoke SDKs.
- **Validated + typed.** Each route has an `inputSchema`; bad LLM arguments are
  rejected before anything runs.
- **Policy-gated.** `--allow '<scheme>://*'`, `--execute` vs dry-run, and the
  `query` vs `command` split let you give an agent read access broadly and write
  access narrowly.
- **Projectable.** The same registry is already MCP tools and an A2A card, so any
  MCP/A2A-speaking model can discover and call it with no extra glue.
- **Auditable.** Every action is a URI + payload + policy decision — trivially
  logged (see `sqlite-context` `log://` routes) and replayable.

Convention that makes LLM decisions safe by construction:
`query` actions are read-only; `command` actions mutate and default to dry-run.
An agent can freely call `…/query/…`, and only `…/command/…` needs `--execute`.

---

## 3. High-value integrations for the automation era

Each is expressed as a connector (URI scheme + routes). `query` = safe/read,
`command` = mutating/gated.

### 3.1 Chrome browser (`browser://`) — see §4, the flagship

### 3.2 Email (`email://`) — IMAP read + SMTP send
- **API:** Python stdlib `imaplib` (read) + `smtplib`/`email` (send); or Gmail/MS
  Graph for hosted.
- **Routes:** `email://host/inbox/query/list`, `email://host/message/query/read`,
  `email://host/message/command/send` (gated), `…/command/reply`.
- **Why:** triage, auto-reply drafting, extract invoices/attachments → feed other
  routes. Sending is a `command` (explicit `--execute` + confirm).

### 3.3 KSeF (`ksef://`) — Polish national e-invoicing
- **API:** REST at `ksef.mf.gov.pl` (test: `ksef-test.mf.gov.pl`). Token/challenge
  auth, online session, send invoice XML (FA(2)), poll UPO/status, query received.
- **Routes:** `ksef://host/session/command/open`, `ksef://host/invoice/command/send`
  (gated), `ksef://host/invoice/query/status`, `ksef://host/invoices/query/list`.
- **Why:** e-invoicing is mandatory; an agent can submit, poll UPO, and reconcile.
  Secrets (token) belong in the connector package, never in core.

### 3.4 Government / e-delivery (`gov://`)
- **API:** PL — ePUAP/login.gov.pl, **e-Doręczenia** (e-Delivery, qualified),
  Biznes.gov.pl. EU — eIDAS. Mostly REST/SOAP + qualified signatures.
- **Routes:** `gov://host/case/query/status`, `gov://host/inbox/query/list`,
  `gov://host/document/command/submit` (gated, signature required).
- **Why:** status polling and document intake are safe `query` automations; submission
  stays a guarded `command`.

### 3.5 Others worth a connector
- **Calendar** (`cal://`, CalDAV/Google) — schedule from a flow.
- **Filesystem** (`fs://`) — already shipped (`mcp-filesystem`).
- **Payments/banking** (`bank://`, read-only statements via PSD2/nordigen) — `query` only.
- **CRM / issue trackers** (`crm://`, `issue://`) — query + gated create.
- **Cloud/infra** (`cloud://`) — read inventory; gated apply.

---

## 4. Flagship: controlling Chrome through URI, driven by an LLM

### 4.1 Which Chrome API
The robust programmatic surface is the **Chrome DevTools Protocol (CDP)**:
start Chrome with `--remote-debugging-port=9222 --headless=new`, then drive it
over the DevTools HTTP/WebSocket endpoint:

| CDP method | URI route | kind |
| --- | --- | --- |
| `Page.navigate` | `browser://chrome/page/command/navigate` | command |
| `Page.captureScreenshot` | `browser://chrome/page/command/screenshot` | command |
| `Runtime.evaluate` (read) | `browser://chrome/page/query/eval` | query |
| `DOM.getDocument` + outerHTML | `browser://chrome/page/query/dom` | query |
| `Input.dispatchMouseEvent` (click) | `browser://chrome/page/command/click` | command |

`query` routes (eval/dom) are safe to read; `command` routes (navigate/click)
mutate the page and stay dry-run unless `--execute`. A headless one-shot fallback
(`chrome --headless --dump-dom <url>` / `--screenshot`) needs no port and is great
for CI. This complements the existing `urirun-connector-browser-control`, which
*forwards* `browser://` to a remote noVNC node — CDP is the *local* driver.

### 4.2 The decision loop (LLM over the registry)
1. Compile a registry from the installed connectors (browser + http-check + time
   + sqlite-context for logging).
2. Project to MCP tools / route list — that's the agent's action space.
3. Give the LLM the goal + the route list; it returns one `{uri, payload}`.
4. `urirun run` it under a policy (`--allow 'browser://chrome/*' --allow 'http*'`),
   `query` freely, `command` only with `--execute`.
5. Feed the JSON result back; repeat until done; log each step via `log://`.

Worked example: **`14-llm-uri-agent/`** in this repo implements exactly this loop
with a deterministic planner (so it runs in CI), and documents swapping in Claude
via the `llm` connector. The agent: checks a site is up (`httpcheck://`), opens it
in Chrome (`browser://chrome/page/command/navigate`), reads the DOM
(`…/query/dom`), and logs the run (`log://`).

---

## 5. Can urirun be simpler / better for many use cases?

Already shipped that helps: `connector_sdk`, `connectors new/smoke/check`,
entry-point discovery, the layered backend (reuse `urirun.host.*`).

Proposed next, in priority order:

1. **`urirun agent` command** — built-in decision loop: load registry → ask an LLM
   (via the `llm` connector) → run the chosen route under policy → repeat. Turns
   the §2 pattern into one command instead of per-example glue.
2. **Declarative connectors (no Python)** — author a connector from a single
   `connector.toml` (routes + argv + schema) so non-Python users ship a connector
   with zero code. The runtime already accepts the JSON contract; add a TOML→bindings
   loader.
3. **Capability profiles** — named policy bundles (`--profile read-only`,
   `--profile browser-agent`) so users grant an agent a curated action space in one
   flag instead of many `--allow` globs.
4. **`fetch`/HTTP adapter as first-class** — many integrations (KSeF, gov, calendar)
   are "call an HTTP API with auth + map response". A declarative `http` adapter
   (url template + auth ref + response jq) would let those connectors be config,
   not code.
5. **Secret references** — a `secret://` indirection (`{token}` → `secret://env/KSEF_TOKEN`)
   so connectors declare *which* secret they need without ever embedding it.

These keep the core small while making the long tail of integrations
**configuration, not code** — the main lever for "many use cases, simply".
