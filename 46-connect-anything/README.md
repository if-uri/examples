# 46 — connect anything through URI adoption

This example shows the intended first step for reusing an existing application,
library, service, Docker project, desktop app, mobile app or URI capability pack
through urirun.

The connector is:

```text
urirun-connector-adopt
```

It exposes:

```text
adopt://host/project/query/inspect
adopt://host/project/query/plan
adopt://host/projects/query/scan
```

## Why this exists

The goal is not to hardcode every integration into urirun. The goal is to make a
local project describe itself enough that urirun can choose the smallest wrapper:

```text
project metadata -> adopt:// plan -> connector/service/widget/artifact flow -> contract check
```

## Try real local projects

```bash
cd /home/tom/github/if-uri/urirun-connector-adopt
PYTHONPATH=. /home/tom/github/if-uri/urirun/venv/bin/python -c \
  'from urirun_connector_adopt.core import main; raise SystemExit(main(["inspect","--path","/home/tom/github/tellmesh/uriimg2nl"]))'

PYTHONPATH=. /home/tom/github/if-uri/urirun/venv/bin/python -c \
  'from urirun_connector_adopt.core import main; raise SystemExit(main(["plan","--path","/home/tom/github/wronai/ocr"]))'
```

Expected groups:

- `tellmesh/uriimg2nl` -> `uri-pack`, `desktop-app`, `library`
- `wronai/ocr` -> `docker`, `cli`, `service`, `api`, `library`
- `semcod/imgl` -> `cli`, `service`, `desktop-app`, `api`, `library`

## Run all examples

```bash
bash /home/tom/github/if-uri/examples/46-connect-anything/run_examples.sh
```

The script demonstrates:

- inspecting a tellmesh URI capability pack
- planning a wronai OCR connector/service/docker wrapper
- inspecting semcod `imgl` as desktop/OCR/library surface
- scanning `tellmesh`, `wronai` and `semcod`
- executing the connector through a generated bindings file
- executing the connector through installed `urirun.bindings` entry points

## Direct Commands

Inspect an existing URI pack:

```bash
/home/tom/github/if-uri/urirun/venv/bin/urirun-adopt inspect \
  --path /home/tom/github/tellmesh/uriimg2nl
```

Plan OCR reuse:

```bash
/home/tom/github/if-uri/urirun/venv/bin/urirun-adopt plan \
  --path /home/tom/github/wronai/ocr
```

Inspect a desktop screenshot/OCR library:

```bash
/home/tom/github/if-uri/urirun/venv/bin/urirun-adopt inspect \
  --path /home/tom/github/semcod/imgl
```

Use a generated bindings file:

```bash
/home/tom/github/if-uri/urirun/venv/bin/urirun-adopt bindings > /tmp/adopt.bindings.json
/home/tom/github/if-uri/urirun/venv/bin/urirun run \
  adopt://host/project/query/inspect \
  /tmp/adopt.bindings.json \
  --execute \
  --payload '{"path":"/home/tom/github/tellmesh/uriimg2nl"}'
```

Use installed connector entry points:

```bash
/home/tom/github/if-uri/urirun/venv/bin/urirun run \
  adopt://host/project/query/plan \
  --entry-points \
  --execute \
  --payload '{"path":"/home/tom/github/wronai/ocr"}'
```

## Example NL Intents

These are the user-facing prompts the chat layer can turn into `adopt://` flows:

```text
Podlacz lokalny projekt ~/github/wronai/ocr jako usluge OCR przez URI.
Sprawdz, czy ~/github/tellmesh/uriimg2nl ma gotowe trasy URI i pokaz je.
Znajdz w ~/github/semcod projekty, ktore da sie uruchamiac jako CLI connector.
Przygotuj plan podlaczenia aplikacji desktopowej z OCR i screenshotami.
Wygeneruj kontrakty dla projektu Docker, zanim zostanie uruchomiony.
```

The intended flow is:

```yaml
task:
  id: connect-local-project
steps:
  - id: inspect
    uri: adopt://host/project/query/inspect
    payload:
      path: /home/tom/github/wronai/ocr
  - id: plan
    uri: adopt://host/project/query/plan
    payload:
      path: /home/tom/github/wronai/ocr
  - id: choose-runtime
    decision:
      from: "${steps.plan.project.groups}"
      prefer:
        - uri-pack
        - connector
        - service
        - docker
        - cli
  - id: generate-or-select-connector
    uri: connector://host/generated/command/create
    payload:
      plan: "${steps.plan.plan}"
  - id: verify-contract
    uri: connector://host/generated/command/verify
    payload:
      contract: "${steps.plan.plan.contracts}"
```

## Group Meaning

- `api` -> declarative HTTP/OpenAPI connector
- `cli` -> command connector with exit-code/stdout/artifact contracts
- `library` -> local function connector
- `service` -> lifecycle routes: start, stop, restart, health
- `docker` -> compose/container lifecycle plus health contract
- `desktop-app` -> screen/OCR/CDP/KVM observation and guarded actions
- `mobile-app` -> ADB/iOS/WebRTC/mobile browser observation and guarded actions
- `browser-js` -> page SDK / JS action queue
- `mcp` -> MCP tool list and call routes
- `uri-pack` -> existing manifest adopted by `urirun adopt-pack`

## Rule

`adopt://` discovers and plans. It should not run unknown software. After
inspection, generate or select a concrete connector/service, attach a realization
contract, then execute through a domain URI route.

## Verify

```bash
# live demo against real local repos (tellmesh / wronai / semcod):
bash run_examples.sh

# self-contained, no external checkouts (CI-safe) — inspect + plan + scan on tmp fixtures:
python -m pytest examples/46-connect-anything/test_connect_anything.py -q
```
