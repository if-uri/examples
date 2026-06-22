# 34 — install AND use every connector, driven by YAML flows

Two ready [urirun flows](flows/) that together exercise the whole connector set:

1. **[`flows/install.flow.yaml`](flows/install.flow.yaml)** — installing each
   connector is itself a URI step (`pkg://host/connector/command/install`), so the
   flow makes sure every `urirun-connector-*` is present.
2. **[`flows/smoke.flow.yaml`](flows/smoke.flow.yaml)** — one representative route
   per connector, so running the flow *uses* every connector and shows it works.

```
install.flow.yaml ──► pip install -e each connector  (pkg:// route)
       ▼
one registry compiled from every connector's bindings
       ▼
smoke.flow.yaml ──► call a route per connector ──► RAN ✓ | config-gated | broken
```

## Run

```bash
python3 run.py               # generate + run both flows, then report
python3 run.py --no-install  # skip the install flow (use what's already installed)
python3 run.py --json
```

```
15 connectors — install via flows/install.flow.yaml, use via flows/smoke.flow.yaml

  connector         installed  status
  ----------------------------------------------------------------
  time-tools        yes        RAN ✓  (current time)
  mcp-filesystem    yes        RAN ✓  (list a dir)
  http-check        yes        RAN ✓  (HTTP status)
  domain-monitor    yes        RAN ✓  (DNS diff)
  get-node          yes        RAN ✓  (installer script)
  sqlite-context    yes        RAN ✓  (recent logs)
  browser-control   yes        RAN ✓  (read page)
  email/mqtt/ksef/planfile/namecheap-dns/llm/kvm/flow-repair  installed + valid (config-gated)
  ----------------------------------------------------------------
  7 ran a route · 8 installed+valid (config-gated) · 0 broken
```

## How it works

- **Install as a URI step** — `pkg_connector.py` exposes `pkg://host/connector/command/install`
  `{name}` (→ `pip install -e urirun-connector-<name>`, `--no-deps` so it never
  re-pulls the editable `urirun`) and `pkg://host/connector/query/installed`
  `{module}`. That is what lets *installation* live inside a flow.
- **One registry, every connector** — after the install flow, `run.py` imports each
  connector's `urirun_bindings()` and compiles them into a single registry; the
  smoke flow's steps are dispatched against it (`importlib.invalidate_caches()`
  picks up anything the install flow just added).
- **Config-gated vs. run** — connectors that need creds / a broker / a device / an
  API key / a project (email, mqtt, ksef, planfile, namecheap-dns, llm, kvm,
  flow-repair) are *installed and validated* but not executed; the flow checks they
  are importable instead. The other seven run a real route.

## The polyglot three

`base64` (PHP), `hash` (Go) and `uuid` (JS) aren't pip packages — they ship their
own `bindings` CLI. [Example 19](../19-all-connectors) builds and sweeps all four
languages through the same contract; this example focuses on the pip-installable
Python set so the *install* step is a clean `pip install -e` URI.

## Files

- `pkg_connector.py` — the `pkg://` install/check connector (install as a URI).
- `connectors.py` — the connector table (module, representative route, gating).
- `run.py` — generate the two YAML flows, run them, report.
- `flows/{install,smoke}.flow.yaml` — the generated, runnable flows.
- `test_connectors.py` — every connector imports, compiles, and runs-or-is-gated.

## Test

```bash
python3 -m pytest test_connectors.py -q
```
