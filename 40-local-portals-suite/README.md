# 40 — local portals suite for autonomous browser testing

This example adds several local-only portals for testing autonomous browser work:

| Host | Portal | Action route |
|------|--------|--------------|
| `crm.local` | fake CRM | `portal://crm.local/lead/command/create` |
| `support.local` | fake support desk | `portal://support.local/ticket/command/create` |
| `shop.local` | fake shop admin | `portal://shop.local/order/command/create` |
| `docs.local` | fake docs/wiki | `portal://docs.local/doc/command/create` |

Every portal has a login page backed by `.env`, a form, a records panel, and an
`/api/records` endpoint for verification. Chrome maps the selected `*.local` host to
`127.0.0.1`, so no `/etc/hosts` edit is needed.

## One Prompt

```bash
./run_prompt.sh 'crm: utwórz lead "Acme z promptu NL"'
```

Other prompts:

```bash
./run_prompt.sh 'support: zgłoszenie "Nie działa lokalny worker"'
./run_prompt.sh 'shop: zamów produkt "URI Test Subscription" qty 3'
./run_prompt.sh 'docs: dokument "Notatka z testu lokalnej autonomii"'
```

Run all four:

```bash
./run_all.sh
```

## What It Uses

The wrapper uses built-in urirun pieces:

```bash
python3 -m urirun.runtime.v2 compile bindings.json --out .state/local-portals.registry.json

python3 -m urirun.runtime.v2 agent run .state/local-portals.registry.json \
  --planner portal_autonomy:planner \
  --allow 'portal://**' \
  --allow-commands \
  --goal 'support: zgłoszenie "Nie działa lokalny worker"'
```

`portal_autonomy:planner` maps NL text to one typed `portal://...` route and payload.
The handler starts the local portal server, logs in with `.env`, fills the form in a
real local Chrome session over CDP, submits, then verifies through `/api/records`.

## Files

- `portal_server.py` — local multi-portal HTTP server.
- `portal_autonomy.py` — NL planner + URI handlers.
- `bindings.json` — typed `portal://...` command routes.
- `run_prompt.sh` — one-prompt runner.
- `run_all.sh` — smoke test for all local portals.
- `.env.example` — credentials and default payloads.
- `test_portals.py` — offline tests.

## Boundary

These portals are intentionally local fixtures. They are for testing selectors,
closed-loop repair, OCR, and NL-to-URI planning without external side effects.
