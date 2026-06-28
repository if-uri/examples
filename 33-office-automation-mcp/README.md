# 33 — office automation from natural language (MCP tools → URI flow → verify)

A user asks for an **office task in plain language**; a planner turns it into a
**multi-step URI flow** over an office **MCP tool surface** (windows, apps,
browser, email, files, clipboard, calendar, screen/OCR, notifications — each a
URI route with a JSON Schema); urirun **executes** the flow step by step; then a
**verification step checks the system state** to confirm the task is actually
done.

```
NL request ──► action space = 26 MCP tools (URIs + JSON Schemas)
          ──► plan: [{uri, payload}, …]   (≥10 steps; deterministic, or --llm)
          ──► urirun.run each step (policy-gated) ──► mutate the office state
          ──► verify(state): did the task really happen?
```

Eight tasks, each a **≥10-step** flow that drives "the whole computer" — opening
apps and windows, a browser, an email client, the file system, the calendar:

| # | task | what it does (verified) |
|---|------|--------------------------|
| `report`   | Q2 report → email | write 2 files, compose, attach both, send → **sent has 1 mail, 2 attachments** |
| `research` | web research → notes | open browser, read page, screenshot, copy, open editor, save 2 notes → **notes + screenshot exist** |
| `tidy`     | tidy the desktop | open 4 apps, list windows, focus, close 2, quit an app → **windows ≤ 2, calculator gone** |
| `invoice`  | OCR → web form | OCR an invoice image, fill 3 fields, submit, save record → **form submitted + record saved** |
| `meeting`  | schedule + invites | create a calendar event, compose & send 2 invites → **1 event, 2 mails sent** |
| `backup`   | daily backup | write 3 docs, copy each to `backup/`, list & read back → **3 files in backup/** |
| `expenses` | receipts → finance | OCR 2 receipts, write a reconciliation, email finance with the summary → **summary saved, 1 mail to finance, 1 attachment** |
| `approval` | decide → reply → schedule | read the inbox, record a decision, reply to the boss, schedule a follow-up → **decision saved, 1 reply sent, 1 event** |

## Run

```bash
python3 run.py                 # all 8 scenarios, deterministic plans, with verification
python3 run.py --scenario invoice
python3 run.py --json          # machine-readable
```

```
office MCP tool surface: 26 URI tools (schemes: app, browser, calendar, clipboard, email, fs, notify, screen, window)
✓ [report] 11 steps — Prepare a Q2 report and email it to the boss with attachments
    executed 11/11 ok=True  ·  verified: True (sent=1 attachments=2)
...
RESULT: 8/8 office tasks completed AND verified
```

## Plan with a real LLM

`--llm` sends the NL request **plus the MCP tool schemas** to a model
(`LLM_MODEL` + key from [`examples/.env`](../.env)) and executes the plan it
returns, then verifies:

```bash
python3 run.py --scenario report --llm
```

The verification is the point: a weak model that mis-plans is reported as
`verified: False`, not silently "done". The bundled `gemini-…-image-preview`
model plans short flows but **struggles with 10-step office tasks** — point
`URIRUN_LLM_MODEL` at a stronger model (e.g. a Claude/GPT/DeepSeek tier) for real
LLM planning. The deterministic flows in `scenarios.py` are the reference of what
a capable model produces.

## How it maps to MCP and to a real machine

- **MCP tools** — `office_system.bindings()` is a urirun registry; urirun projects
  routes to MCP tools (`uri` + `inputSchema`). The planner chooses among them
  exactly as an MCP client would. `run.py` prints the tool surface; the schemas
  are what the LLM fills.
- **Simulated, but real transitions** — `office_system.py` keeps a JSON state
  (windows, sent mail, files, calendar, …). Every route mutates it, so step N sees
  step N-1 and `verify()` checks the real outcome. Swap these routes for the
  tellmesh desktop connectors (`him`/`kvm`/`browser`/`urioffice`/`uriscreen` — see
  [example 31](../31-llm-remote-office)) and the same flows drive an actual desktop.
- **Over the relay** — these office URIs are ordinary routes, so they run on a
  remote, NAT'd node through `mesh.urirun.com` exactly like
  [example 32](../32-host-ask-over-relay): the user asks on the host, the node
  executes.

## Files

- `office_system.py` — the office computer simulator + the 26-route MCP tool surface.
- `scenarios.py` — the 8 NL tasks: request, the ≥10-step flow, and `verify(state)`.
- `run.py` — planner (deterministic or `--llm`) → execute → verify → report.
- `test_office.py` — every task plans ≥10 steps, executes, and verifies (offline).

## Test

```bash
python3 -m pytest test_office.py -q
```
