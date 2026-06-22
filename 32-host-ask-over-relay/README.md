# 32 — drive a NAT'd node from natural language, through the relay

The capstone of the mesh story: a host turns **natural language** into a URI flow
and runs it on a node that has **no inbound port** — entirely through the
[`mesh.urirun.com`](../../mesh-urirun-com) relay.

```
urirun host ask "<NL>"
   │  discover    GET /routes on the proxy  ── auto from the relay (bridge published them)
   │  plan        NL -> URI flow            ── heuristic (--no-llm) or an LLM
   │  execute     each step: serviceMap -> proxy /run -> relay -> node
   ▼
node (behind NAT)  runs it under its own --allow, returns the envelope
```

Both sides only make **outbound** HTTP to the relay; the host never reaches the
node directly — discovery *and* execution ride the relay.

## Run

```bash
./run.sh
```

With a real model (key + `LLM_MODEL` from [`examples/.env`](../.env)):

```bash
USE_LLM=1 ./run.sh     # plan with the LLM instead of the heuristic
```

```
== 4) ... [plan: LLM (openrouter/google/gemini-3.1-flash-image-preview)] ==
  planner:    {"fallback":false,"provider":"litellm"}
  flow steps: ["env://office/runtime/query/health","shell://office/command/date"]
  timeline:   [{...,"ok":true},{...,"ok":true}]
PASS
```

(litellm 1.89.x segfaults in an atexit cleanup *after* returning the result, so the
LLM run sets `PYTHONUNBUFFERED=1` to flush `host ask`'s JSON before that crash and
strips litellm's `Provider List` stdout banner — the plan is still produced.)

`run.sh` stands up the whole chain on localhost (the relay/proxy stand in for the
internet) and drives it with `urirun host ask --no-llm` by default, so it is
deterministic and needs no API key:

```
== 4) NL -> urirun host ask -> plan -> execute, all over the relay ==
  flow steps: ["env://office/runtime/query/health","shell://office/command/date"]
  timeline:   [{"uri":"env://office/runtime/query/health","ok":true},
               {"uri":"shell://office/command/date","ok":true}]
PASS: drove a NAT'd node from natural language end-to-end through the relay
```

## The real-world version

On the node (e.g. `192.168.188.201`, SSH closed, behind NAT) — bridge it once:

```bash
MESH_RELAY=https://mesh.urirun.com MESH_NODE=lenovo MESH_TOKEN=$SECRET \
  LOCAL_NODE=http://127.0.0.1:8765 ../../mesh-urirun-com/clients/mesh-node.sh
```

On your host — proxy + a mesh config that points the node at the proxy:

```bash
MESH_RELAY=https://mesh.urirun.com MESH_TOKEN=$SECRET \
  python3 ../../mesh-urirun-com/clients/mesh-proxy.py --node lenovo --port 8090 &   # routes auto-discovered
cat > .urirun/mesh.json <<'JSON'
{"name":"relay-host","nodes":[{"name":"lenovo","url":"http://127.0.0.1:8090"}]}
JSON

urirun host ask --node lenovo "list the top processes and read the screen" --execute
# or with a real model: drop --no-llm and set LLM_MODEL / OPENROUTER_API_KEY (see examples/.env)
```

## Why it works (and the pieces)

- **Discovery over the relay** — the bridge publishes the node's `/routes` to the
  relay at registration; the proxy serves them as its own `/routes`, so
  `urirun host` builds the action space without touching the node.
- **Execution over the relay** — `host ask` sets `URI_SERVICE_MAP` from the mesh
  `serviceMap`; with the node's URL pointed at the proxy, every step's `/run`
  enqueues on the relay, the node's bridge runs it locally (its `--allow` still
  gates), and the result comes back.
- **Token ≥ 8 chars** — the relay rejects shorter ones; the clients fail fast.

Token-free, port-free, RDP-free remote control — driven by natural language.

## See also

[Example 33](../33-office-automation-mcp) builds the richer half: six office tasks
(email, browser, files, calendar, windows…) as ≥10-step flows an LLM plans over an
MCP tool surface, each **verified** against the resulting system state. Those same
office URIs run on a remote NAT'd node through this relay.
