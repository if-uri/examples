#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# One script for the whole chain: drive a urirun node that sits behind NAT from
# NATURAL LANGUAGE, entirely through the mesh.urirun.com relay.
#
#   urirun host ask  ──► discover routes (proxy /routes, auto from relay)
#                    ──► heuristic plan: NL -> URI flow
#                    ──► execute each step: serviceMap -> proxy /run -> relay -> node
#
# Everything runs on localhost here (the relay/proxy stand in for the internet),
# with --no-llm so it is deterministic and needs no API key. The node publishes
# NO inbound port to the host — the host reaches it only via the relay.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
MESH="$ROOT/mesh-urirun-com"
TMP="$(mktemp -d)"; PIDS=()
cleanup() { for p in "${PIDS[@]:-}"; do [ -n "${p:-}" ] && kill "$p" >/dev/null 2>&1 || true; done; rm -rf "$TMP"; }
trap cleanup EXIT
for t in php jq curl python3; do command -v "$t" >/dev/null 2>&1 || { echo "SKIP: needs $t"; exit 0; }; done
[ -d "$MESH/clients" ] || { echo "SKIP: mesh-urirun-com not checked out beside the examples repo"; exit 0; }
[ -d "$ROOT/urirun/adapters/python" ] && export PYTHONPATH="$ROOT/urirun/adapters/python:${PYTHONPATH:-}"
[ -d "$ROOT/urirun-flow" ] && export PYTHONPATH="$ROOT/urirun-flow:${PYTHONPATH:-}"
[ -d "$ROOT/urirun-connector-router" ] && export PYTHONPATH="$ROOT/urirun-connector-router:${PYTHONPATH:-}"
python3 -c "import urirun.runtime.v2" >/dev/null 2>&1 || { echo "SKIP: a current urirun is not importable (pip install urirun)"; exit 0; }
U() { python3 -m urirun.runtime.v2 "$@"; }
free_port() { python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'; }

# USE_LLM=1 plans with a real model (LLM_MODEL + key from examples/.env); default
# is the deterministic heuristic (--no-llm) so the example runs in CI without a key.
LLM_FLAG="--no-llm"; PLAN_MODE="heuristic (--no-llm)"
if [ "${USE_LLM:-0}" = "1" ]; then
  [ -f "$HERE/../.env" ] && { set -a; . "$HERE/../.env" 2>/dev/null || true; set +a; }
  if [ -n "${URIRUN_LLM_MODEL:-${LLM_MODEL:-}}" ]; then
    LLM_FLAG=""; PLAN_MODE="LLM (${URIRUN_LLM_MODEL:-$LLM_MODEL})"
    # litellm 1.89.x segfaults in an atexit async-client cleanup AFTER returning the
    # result; unbuffered stdout flushes host ask's JSON before that crash so the
    # (exit-139) process still yields a usable plan. Harmless in heuristic mode.
    export PYTHONUNBUFFERED=1
  else
    echo "  (USE_LLM=1 but no LLM_MODEL/OPENROUTER key — staying on heuristic)"
  fi
fi

NODE=office; TOKEN=meshsecret123
NP="$(free_port)"; RP="$(free_port)"; PP="$(free_port)"
RELAY="http://127.0.0.1:$RP"

echo "== 1) a urirun 'office' node (health + date routes), behind NAT (no host access) =="
cat > "$TMP/bindings.json" <<JSON
{"version":"urirun.bindings.v2","bindings":{
  "env://$NODE/runtime/query/health":{"kind":"command","adapter":"argv-template",
    "inputSchema":{"type":"object","additionalProperties":false,"properties":{}},
    "argv":["python3","-c","import json;print(json.dumps({'ok':True,'status':'healthy','via':'mesh-relay'}))"],
    "policy":{"allowExecute":true,"maxArgs":8}},
  "shell://$NODE/command/date":{"kind":"command","adapter":"argv-template",
    "inputSchema":{"type":"object","additionalProperties":false,"properties":{}},
    "argv":["python3","-c","import json,subprocess;print(json.dumps({'ok':True,'date':subprocess.run(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],capture_output=True,text=True).stdout.strip(),'via':'mesh-relay'}))"],
    "policy":{"allowExecute":true,"maxArgs":8}}}}
JSON
U compile "$TMP/bindings.json" --out "$TMP/reg.json" >/dev/null
U node init --config "$TMP/node.json" --name "$NODE" --registry "$TMP/reg.json" --host 127.0.0.1 --port "$NP" --execute >/dev/null
U node serve --config "$TMP/node.json" --execute --allow "env://$NODE/**" --allow "shell://$NODE/**" >"$TMP/node.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 40); do curl -fsS "http://127.0.0.1:$NP/health" >/dev/null 2>&1 && break; sleep 0.25; done

echo "== 2) the relay + the node bridge (publishes routes) + the host proxy (auto-discovers them) =="
MESH_DATA="$TMP/data" php -S "127.0.0.1:$RP" "$MESH/public/relay.php" >"$TMP/relay.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 40); do curl -fsS "$RELAY/healthz" >/dev/null 2>&1 && break; sleep 0.25; done
MESH_RELAY="$RELAY" MESH_NODE="$NODE" MESH_TOKEN="$TOKEN" LOCAL_NODE="http://127.0.0.1:$NP" \
  MESH_POLL_INTERVAL=1 bash "$MESH/clients/mesh-node.sh" >"$TMP/bridge.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 40); do curl -fsS "$RELAY/nodes" | grep -q "$NODE" && break; sleep 0.25; done
MESH_RELAY="$RELAY" MESH_TOKEN="$TOKEN" MESH_NODE="$NODE" MESH_POLL_INTERVAL=0.5 \
  python3 "$MESH/clients/mesh-proxy.py" --port "$PP" >"$TMP/proxy.log" 2>&1 & PIDS+=("$!")
for _ in $(seq 1 40); do curl -fsS "http://127.0.0.1:$PP/routes" 2>/dev/null | grep -q "$NODE" && break; sleep 0.25; done
echo "  proxy /routes: $(curl -fsS "http://127.0.0.1:$PP/routes" | jq -c '.routes|map(.uri)')"

echo "== 3) host mesh config points 'office' at the PROXY (never at the node directly) =="
mkdir -p "$TMP/.urirun"
cat > "$TMP/.urirun/mesh.json" <<JSON
{"name":"relay-host","nodes":[{"name":"$NODE","url":"http://127.0.0.1:$PP"}]}
JSON

echo "== 4) NL -> urirun host ask -> plan -> execute, all over the relay  [plan: $PLAN_MODE] =="
raw="$(cd "$TMP" && U host ask --config .urirun/mesh.json $LLM_FLAG --node "$NODE" "check the node health and show me the current date" --execute 2>"$TMP/ask.err" || true)"
# litellm prints a 'Provider List' banner to stdout; keep only the JSON document
out="$(printf '%s\n' "$raw" | sed -n '/^{/,$p')"
echo "  planner:    $(jq -c '.generator' <<<"$out" 2>/dev/null || echo '?')"
echo "  flow steps: $(jq -c '[.flow.steps[].uri]' <<<"$out" 2>/dev/null || echo '?')"
echo "  timeline:   $(jq -c '[.timeline[]|{uri,ok}]' <<<"$out" 2>/dev/null || echo '?')"

echo "== 5) assertions =="
jq -e '.ok == true' <<<"$out" >/dev/null || { echo "FAIL: host ask not ok"; echo "$out" | head -40; cat "$TMP/ask.err"; exit 1; }
jq -e '(.flow.steps | length) >= 1' <<<"$out" >/dev/null || { echo "FAIL: no steps planned"; echo "$out"; exit 1; }
echo "$out" | grep -q 'mesh-relay' || { echo "FAIL: results did not round-trip through the relay"; exit 1; }
if [ "$LLM_FLAG" = "--no-llm" ]; then
  jq -e '[.flow.steps[].uri] | any(. == "shell://'"$NODE"'/command/date")' <<<"$out" >/dev/null \
    || { echo "FAIL: the date route was not planned (heuristic)"; echo "$out"; exit 1; }
fi

echo "PASS: drove a NAT'd node from natural language end-to-end through the relay (discover + plan [$PLAN_MODE] + execute via mesh-proxy)"
