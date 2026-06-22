# 25 — a multi-step URI flow across tellmesh packs (executed, not just resolved)

Example 24 adopted ~20 tellmesh libraries into one URI registry. This one shows the
payoff: **chaining several of those URIs into one flow and running it in action**,
where each step's real output feeds the next.

```txt
kvm://{host}/monitor/command/capture  ──image_id──►  ocr://{host}/image/query/text
                                                              │ text
                                                              ▼
                                          llm://{host}/chat/command/complete ──► summary
```

Three schemes — `kvm` (capture), `ocr` (read), `llm` (summarize) — live in **one
registry**. The flow runner calls `urirun.run(uri, registry, mode="execute")` for each
step under a policy that allows only those three schemes, and threads the result of
each step into the next step's payload.

## Run it

```bash
python3 flow.py
pytest test_flow.py -q
```

```
== one registry, 3 routes across 3 adopted packs (kvm, ocr, llm) ==

  [1] kvm://host1/monitor/command/capture
      -> {"image_id": "shot-mon0", "monitor": 0, "width": 1920, "height": 1080}
  [2] ocr://host1/image/query/text
      -> {"image_id": "shot-mon0", "text": "INVOICE  Acme Corp  TOTAL DUE: 42.00 USD  due 2026-07-01", ...}
  [3] llm://host1/chat/command/complete
      -> {"model": "mock-llm", "summary": "Invoice for 42.00 USD, due 2026-07-01.", ...}

flow result: 'Invoice for 42.00 USD, due 2026-07-01.'
end-to-end data threaded correctly: True
```

`image_id` from step 1 is the input to step 2; the `text` from step 2 is the prompt
for step 3. Change the capture (`monitor=1`) and a *different* scanned document flows
all the way to a *different* summary — the data really moves through the URIs.

## Run it from the CLI (no Python runner)

The same chain, driven entirely by the `urirun` CLI from bash — `jq` threads each
step's `result.value` into the next step's payload:

```bash
./flow_cli.sh
```

```
  [1] kvm capture            -> image_id=shot-mon0
  [2] ocr image=shot-mon0    -> text="INVOICE  Acme Corp  TOTAL DUE: 42.00 USD  due 2026-07-01"
  [3] llm complete           -> summary="Invoice for 42.00 USD, due 2026-07-01."
end-to-end (kvm->ocr->llm) threaded correctly via the CLI: ok
```

This works because `urirun adopt-pack` emits a re-importable handler descriptor, so an
adopted route **executes from a plain file registry** — `urirun run <uri> <registry>
--execute` — with no Python orchestration. The per-step `--allow <scheme>://**` is the
policy gate.

## Run it over a network transport (a served node)

The same chain, but the registry is served by `urirun node serve` (HTTP) and each step
is a `POST /run` to the node — the URIs interoperate *remotely*:

```bash
./flow_node.sh
```

```
node healthy: {"name":"flownode","execute":true,"routeCount":3}
  [1] POST kvm capture       -> image_id=shot-mon0
  [2] POST ocr image=shot-mon0 -> text="INVOICE  Acme Corp  TOTAL DUE: 42.00 USD  due 2026-07-01"
  [3] POST llm complete      -> summary="Invoice for 42.00 USD, due 2026-07-01."
end-to-end (kvm->ocr->llm) threaded correctly over HTTP: ok
```

The node's `--allow kvm/ocr/llm` globs are its security boundary — a `POST /run` for any
other URI is denied at the node. Same three URIs, same data flow, now across a socket:
in-process (`flow.py`), local CLI (`flow_cli.sh`) and remote node (`flow_node.sh`) are
three transports over **one** registry.

## What's real and what's a stand-in

- **Real:** the URI schemes/operations (the actual tellmesh `kvm`/`ocr`/`llm`
  contracts), the adoption (`adopt-pack` manifest → bindings), compiling them into one
  registry, in-process **execution** of each route via the `local-function` adapter,
  the **policy gate** around the chain, and the data threaded between steps.
- **Stand-in:** the handler bodies in `packs/*/handlers.py`. The real tellmesh handlers
  need the whole monorepo installed (`uriocr` imports `uri_control.edge`, …), so this
  example ships small deterministic handlers that honour the same URI contracts. Swap
  in the real packages (install tellmesh, point the manifests at `uriocr.handlers:…`)
  and the same flow runs against them unchanged — that is the point of adoption.

## How a route becomes executable

`adopt-pack` emits a `ref` string (`"flow_ocr.handlers:extract_text"`). To **execute**
(not just dry-run), `flow.py` turns that into a re-importable descriptor
(`python: {module, export}`) so urirun hydrates and calls the handler in-process. Each
handler receives the step's **payload** as keyword arguments and returns a dict, which
urirun wraps as `result.value` — that value is what the next step consumes.

## Files

- `flow.py` — adopt 3 packs → one registry → execute the chain in-process, threading outputs.
- `flow_cli.sh` — the same flow driven by `urirun run` + `jq` from bash (no Python runner).
- `flow_node.sh` — the same flow over HTTP: `urirun node serve` + `POST /run` per step.
- `packs/flow_kvm|flow_ocr|flow_llm/` — manifest + deterministic handler per scheme.
- `test_flow.py` — asserts the threading, a branch (`monitor=1`), policy gating, and the
  CLI and node flows end to end.
