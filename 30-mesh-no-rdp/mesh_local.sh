#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Control one computer from another WITHOUT RDP — using urirun's node/host mesh.
# Each "computer" runs `urirun node serve` exposing a few policy-gated routes over
# HTTP; a controller registers them and dispatches URIs. The node's --allow globs are
# its security boundary, so the controller can only call the *specific* routes the node
# exposes — least-privilege remote control, not a full remote desktop.
#
# This script simulates two computers as two local nodes (node-a, node-b) + a host,
# end to end: serve -> register -> dispatch -> shut down.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERE}/generated"
export PYTHONPATH="${HERE}/../../urirun/adapters/python:${PYTHONPATH:-}"
U() { python3 -m urirun.runtime.v2 "$@"; }
command -v jq >/dev/null 2>&1 || { echo "this demo needs jq"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "this demo needs curl"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT"
PIDS=()
cleanup() { for p in "${PIDS[@]:-}"; do [ -n "${p:-}" ] && kill "$p" >/dev/null 2>&1 || true; done; }
trap cleanup EXIT

free_port() { python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()'; }

start_node() {  # <name>
  local name="$1" port reg cfg
  port="$(free_port)"
  reg="${OUT}/${name}.registry.json"
  cfg="${OUT}/${name}.node.json"
  sed "s/NODE/${name}/g" "${HERE}/node.bindings.template.json" > "${OUT}/${name}.bindings.json"
  U compile "${OUT}/${name}.bindings.json" --out "$reg" >/dev/null
  U node init --config "$cfg" --name "$name" --registry "$reg" --host 127.0.0.1 --port "$port" --execute >/dev/null
  U node serve --config "$cfg" --execute \
    --allow "sys://${name}/**" --allow "sh://${name}/**" --allow "log://${name}/**" \
    > "${OUT}/${name}.log" 2>&1 &
  PIDS+=("$!")
  for _ in $(seq 1 40); do curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1 && break; sleep 0.25; done
  echo "$port"
}

dispatch() {  # <port> <uri> <payload-json>
  curl -s -X POST "http://127.0.0.1:$1/run" -H 'Content-Type: application/json' \
    -d "$(jq -nc --arg u "$2" --argjson p "$3" '{uri:$u, payload:$p}')"
}

echo "== 'install' + start two computers as urirun nodes =="
PORT_A="$(start_node node-a)"; echo "  node-a serving on 127.0.0.1:${PORT_A}"
PORT_B="$(start_node node-b)"; echo "  node-b serving on 127.0.0.1:${PORT_B}"

echo ""
echo "== register both nodes with the controller (host) =="
HOSTCFG="${OUT}/host.json"
U host init --config "$HOSTCFG" --name controller >/dev/null
U host add-node --config "$HOSTCFG" node-a "http://127.0.0.1:${PORT_A}" >/dev/null
U host add-node --config "$HOSTCFG" node-b "http://127.0.0.1:${PORT_B}" >/dev/null
U host nodes --config "$HOSTCFG" --json | jq -c '.nodes[] | {name, url, routes: (.routes|length)}'

echo ""
echo "== control node-b FROM the controller, over HTTP (no RDP) =="
echo "  [b] sys info     -> $(dispatch "$PORT_B" 'sys://node-b/runtime/query/info' '{}' | jq -c '.result.stdout|fromjson')"
echo "  [b] run 'uname -a' -> $(dispatch "$PORT_B" 'sh://node-b/command/run' '{"cmd":"uname -a"}' | jq -r '.result.stdout' | head -c 80)…"
echo "  [a] write log    -> $(dispatch "$PORT_A" 'log://node-a/session/command/write' '{"text":"hello from the controller"}' | jq -c '.result.stdout|fromjson')"
echo "  [a] read log     -> $(dispatch "$PORT_A" 'log://node-a/session/query/recent' '{"limit":3}' | jq -c '.result.stdout|fromjson')"

echo ""
echo "== least-privilege check: a non-whitelisted command is REFUSED by the node =="
deny="$(dispatch "$PORT_B" 'sh://node-b/command/run' '{"cmd":"rm -rf /"}' | jq -r '.ok, (.error.message // .error // "schema-rejected")' | paste -sd' ')"
echo "  rm -rf / -> ${deny}"

echo ""
echo "== discover running nodes on this machine ('urirun node list') =="
U node list --ports "${PORT_A},${PORT_B}" | sed 's/^/  /'

echo ""
echo "== shut them down with 'urirun node stop' (SIGTERM -> port freed) =="
U node stop --port "${PORT_A}" --port "${PORT_B}" | sed 's/^/  /' || true
cleanup; PIDS=()   # belt-and-suspenders: also reap by PID
echo "  on a real machine a --service node respawns: 'systemctl --user disable --now urirun-node'"
echo "done"
