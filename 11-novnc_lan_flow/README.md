# 11-novnc_lan_flow - noVNC computers controlled by URI flow

Docker demo where URI commands control real Chromium browsers running inside
virtual noVNC desktops. The browser opens inside the container, not on the host.

## What runs

- `pc1-browser`..`pc4-browser` - Selenium Chromium desktops with noVNC.
- `pc1-api`..`pc4-api` - small URI node APIs exposing `browser://`, `app://` and `log://`.
- `dashboard` - browser view with noVNC iframes, logs and last flow result.
- `orchestrator/run_flow.py` - sends a multi-step URI flow to the computers.

Optional `pc3` and `pc4` services exist behind the Compose profile `full`.

## Run

```bash
make up
```

Open:

```text
Dashboard: http://127.0.0.1:8192/?pc1NovncPort=7901&pc2NovncPort=7902&pc1ApiPort=9001&pc2ApiPort=9002
pc1 noVNC: http://127.0.0.1:7901/?autoconnect=1&resize=scale
pc2 noVNC: http://127.0.0.1:7902/?autoconnect=1&resize=scale
```

If these ports are busy, run the same demo on another set of ports. The
dashboard URL accepts port overrides in the query string:

```bash
DASHBOARD_PORT=18192 \
PC1_NOVNC_PORT=17901 PC2_NOVNC_PORT=17902 \
PC1_API_PORT=19001 PC2_API_PORT=19002 \
make up
```

Run the URI flow:

```bash
make flow
```

The basic flow opens pages and captures screenshots through these URI commands:

```text
browser://pc1/page/command/open
browser://pc1/page/command/screenshot
browser://pc2/page/command/open
browser://pc2/page/command/screenshot
log://pc1/session/command/write
log://pc2/session/query/recent
```

## Four-computer flow

The full scenario starts four noVNC computers and gives every computer a small
local service:

```bash
make up-full
make flow-full
```

The dashboard URL printed by `make up-full` includes the query parameters needed
to show all four iframes:

```text
?pcs=pc1,pc2,pc3,pc4&pc1NovncPort=7901&pc2NovncPort=7902&pc3NovncPort=7903&pc4NovncPort=7904
```

The full flow uses these extra application routes:

```text
app://pc1/notes/command/add
app://pc1/notes/query/list
app://pc2/orders/command/create
app://pc2/orders/query/list
app://pc3/reports/command/render
app://pc3/reports/query/latest
app://pc4/monitor/command/check
app://pc4/monitor/query/status
```

It also drives browser screenshots on all four machines:

```text
browser://pc1/page/command/screenshot
browser://pc2/page/command/screenshot
browser://pc3/page/command/screenshot
browser://pc4/page/command/screenshot
```

Artifacts are written to:

```text
generated/flow-result.json
generated/registry.json
generated/routes.txt
generated/screenshots/*.png
```

## Manual URI call

```bash
curl -fsS http://127.0.0.1:9001/run \
  -H 'content-type: application/json' \
  -d '{"uri":"browser://pc1/page/command/open","payload":{"url":"https://example.com/"}}' \
  | python3 -m json.tool
```

Screenshot:

```bash
curl -fsS http://127.0.0.1:9001/run \
  -H 'content-type: application/json' \
  -d '{"uri":"browser://pc1/page/command/screenshot","payload":{"url":"https://example.com/","output":"manual.png"}}' \
  | python3 -m json.tool
```

Application command:

```bash
curl -fsS http://127.0.0.1:9001/run \
  -H 'content-type: application/json' \
  -d '{"uri":"app://pc1/notes/command/add","payload":{"text":"Manual note from shell"}}' \
  | python3 -m json.tool
```

## Test

```bash
make test
make test-full
```

The smoke tests start Docker, run the URI flow, verify generated routes and
check that screenshots were produced. `make test-full` also checks the
`app://` routes and the four-computer screenshot set.

> Needs Docker and pulls the public `selenium/standalone-chromium` image.
