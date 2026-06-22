# 32 — YAML task scenarios + a live event stream from the node

Two things in one example:

1. **Describe computer tasks as YAML scenarios** and run them against a urirun node over
   the mesh — login to a site, drive the desktop, write an office document, audit a box.
2. **Receive the node's logs/errors live, as URIs** — the runner subscribes to the
   node's **SSE event stream** (`GET /events`) and prints each `run`/`error` event the
   node emits *while* the steps dispatch, so you see both sides in real time.

```txt
 HOST                                           NODE
 ────                                           ────
 run_scenarios.py  ──POST /run {uri,payload}──►  executes a step
        │   (one per YAML step)                       │ emits an event
        ▼                                             ▼
   ◄─────────────── GET /events (SSE) ───────────  run://…  /  error://local/E-…
   prints  "░ node-event: run  him://lab/… ok"   (logs + errors as URIs, immediately)
```

## Run

```bash
./run_scenarios.sh                                   # every scenarios/*.yaml
./run_scenarios.sh scenarios/web-login.yaml          # one scenario
NODE_URL=http://192.168.188.201:8765 ./run_scenarios.sh scenarios/system-audit.yaml
```

A live run against a mock office node (4 scenarios) interleaves dispatch + node events:

```
  [1] him://lab/keyboard/command/type-text
      -> ok: {"typed": "jan@firma.pl", ...}
      ░ node-event: run   him://lab/keyboard/command/type-text ok
  [5] browser://lab/page/command/screenshot
      -> FAIL: "HTTP 400"
      ░ node-event: error error://local/E-1ebc9205/query/info  INVALID_ARGUMENT
== 4 scenario(s): 15/18 steps ok; 21 live node-events received ==
```

`system-audit.yaml` works on **any** node (even the default 7-route one), so it runs
against the live remote node too; the others need the office surface (`him`/`kvm`/
`browser`/`urioffice`) — see [example 31](../31-llm-remote-office).

## Scenario format

```yaml
name: web-login
description: ...
steps:
  - uri: browser://{host}/page/command/open    # {host}/{monitor}/{session} are resolved
    payload: {url: "https://example.com/login"}
    why: open the login page
  - uri: him://{host}/keyboard/command/type-text
    payload: {text: "$ref:0.title"}            # thread an earlier step's output
```

- `{host}` → the node's name, `{monitor}` → `0`, etc. (also handles the
  percent-encoded `%7B…%7D` that `/routes` emits).
- `$ref:<step>.<field>` pulls a value from an earlier step's result.
- No PyYAML required — a tiny built-in parser covers this subset (PyYAML is used if present).

## The live event channel (`GET /events`, SSE)

Any urirun node now exposes a one-way **node→host** Server-Sent Events stream. Each
dispatched route publishes a `run` event, and every failure an `error` event whose
`uri` is the `error://local/E-…` address — so the controller receives **logs and errors
as URIs** the instant they happen, without polling `/errors`.

```bash
urirun host watch lab                  # or: urirun host watch http://NODE_IP:8765
curl -N http://NODE_IP:8765/events     # raw SSE
```

```
run    him://lab/keyboard/command/type-text  ok
run    browser://lab/page/command/screenshot  FAIL  INVALID_ARGUMENT
error  error://local/E-1ebc9205/query/info  INVALID_ARGUMENT
```

### Fan out events to MQTT (many subscribers / a UI)

For more than one consumer — a dashboard, several operators, automations — republish the
node's events to an MQTT broker. `urirun host watch` does it inline:

```bash
urirun host watch lab --mqtt-broker localhost:1883            # node events -> MQTT
urirun host watch lab --mqtt-broker localhost:1883 --scheme error   # only errors

# any number of subscribers then consume, wildcarding by node or kind:
mosquitto_sub -t 'urirun/events/lab/#'        # everything from node 'lab'
mosquitto_sub -t 'urirun/events/+/error/#'    # every node's errors
```

Topic layout: `urirun/events/<node>/<event>/<uri-scheme>` (e.g.
`urirun/events/lab/run/him`, `urirun/events/lab/error/error`). Needs `paho-mqtt` on the
watcher (`pip install paho-mqtt`) and a reachable broker. The same publish point can feed
the `urirun-connector-mqtt` device bridge or any MQTT-native dashboard.

See [`NOTES-bidirectional.md`](NOTES-bidirectional.md) for why SSE (not WebSocket) and
whether a fuller two-way channel needs a package refactor.

## Files

- `scenarios/*.yaml` — task scenarios (web login, desktop control, office doc, audit).
- `run_scenarios.py` / `run_scenarios.sh` — dispatch steps + watch the event stream.
- `test_scenarios.py` — offline test (parse, thread, run against a fake node).
- `NOTES-bidirectional.md` — design assessment of the live channel.

## Test

```bash
python3 -m pytest test_scenarios.py -q     # or: python3 test_scenarios.py
```
