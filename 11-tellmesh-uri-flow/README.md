# 11 · tellmesh packs as a URI flow

Adopt existing **tellmesh capability packs** as URIs with no code change, then run a
`uri2flow`-style DAG across them — entirely through **urirun**.

## The flow

`flow.yaml` is a DAG of pack URIs (the same `task`/`steps` shape urirun and uri2flow
use). It reads the screen, reasons about it, and alerts:

```
ocr://host/image/latest/query/text  ─┐
                                      ├─►  llm://host/vision/query/analyze  ─►  message://local/alert/command/send
vql://host/ui/latest/query/detect   ─┘
```

Each step's output feeds the next through `*_from` payload references
(`text_from: read_text.text`, `summary_from: analyze.summary`).

## How it works

1. **Adopt** — every manifest in `packs/` is mapped 1:1 to `bindings.v2` by
   `urirun.runtime.adopt_pack` and merged into one registry. The packs are vendored
   here so the example is self-contained; in practice you would
   `urirun adopt-pack <installed-pack>`.
2. **Hydrate** — handlers are filled with canned stubs so the flow runs anywhere.
   Install the real tellmesh packs to swap in live handlers (the URIs do not change).
3. **Run** — `run.py` executes the DAG step by step, resolving `*_from` references and
   dispatching each step through urirun.

```bash
pip install urirun pyyaml
make run      # run the flow
make test     # adopt + validate + dispatch every vendored pack
```

Sample run:

```
adopted 10 routes across 4 packs: llm, message, ocr, vql
flow: tellmesh-screen-understand-alert — 4 steps
  [read_text  ] ocr://host/image/latest/query/text   -> {"text": "Invoice #4471 …"}
  [detect_ui  ] vql://host/ui/latest/query/detect     -> {"elements": [{"label": "Pay now", …}]}
  [analyze    ] llm://host/vision/query/analyze        -> {"summary": "An overdue invoice …", "action": "notify"}
  [alert      ] message://local/alert/command/send     -> {"sent": true, "to": "ops"}
flow ok: True
```

## Why this matters

Pointed at the tellmesh packs unchanged, urirun adopted **27 packs · 116 routes** via
their manifests; **26 packs are fully green** and **113/116 routes dispatch** through the
runtime with concrete param values. Any green route is composable in a flow like the one
above — see [docs.ifuri.com/adopt-as-uri](https://docs.ifuri.com/adopt-as-uri.html).

### Known characterisation

- **Mid-path `{param}` routing** — patterns like `kvm://{host}/monitor/{monitor}/query/screenshot`
  now resolve from a concrete URI (`…/monitor/2/…`): urirun falls back from an exact segment
  to a single `{param}` key, binds the value and passes it to the handler. Exact matches still
  win over the param.
- **`shell://{command}`** — only an authority, no resource/operation segments; rejected by the
  bindings.v2 grammar. Such a pattern must add segments to be adopted.
- **Handler-less patterns** — a few packs declare a `uri_pattern` with no `handlers.python`
  entry; those routes adopt but have nothing to hydrate.
