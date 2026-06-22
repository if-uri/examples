#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Self-contained proof: spin a LOCAL urirun node, deploy the CDP browser surface
# (browser-control connector's cdp-flat-handler.py) onto it over signed /deploy,
# then drive a real local Chrome through it with drive_cdp.py — no remote node, no
# SSH. Needs a Chrome/Chromium on this machine.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
ADP="$ROOT/urirun/adapters/python"
PY="${PY:-$ROOT/urirun/venv/bin/python3}"; [ -x "$PY" ] || PY=python3
HANDLER="$ROOT/urirun-connector-browser-control/examples/cdp-flat-handler.py"

command -v google-chrome chromium chromium-browser google-chrome-stable >/dev/null 2>&1 || \
  { echo "SKIP: no Chrome/Chromium on this machine"; exit 0; }
[ -f "$HANDLER" ] || { echo "SKIP: cdp-flat-handler.py not found ($HANDLER)"; exit 0; }

TMP="$(mktemp -d)"; export HOME="$TMP"; mkdir -p "$TMP/.ssh"
export PYTHONPATH="$ADP"
PIDS=(); cleanup(){ for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done
  pkill -f 'remote-debugging-port=9222' 2>/dev/null || true; rm -rf "$TMP"; }
trap cleanup EXIT

ssh-keygen -t ed25519 -f "$TMP/.ssh/id_ed25519" -N "" -q
PORT="$($PY -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"
N="http://127.0.0.1:$PORT"

echo "== bindings for node 'local' =="
sed 's/NODE/local/g' "$HERE/cdp-bindings.json" > "$TMP/cdp.bindings.json"
cp "$HANDLER" "$TMP/cdp-flat-handler.py"

echo "== start a local node (key-auth + deploy) =="
echo '{"version":"urirun.bindings.v2","bindings":{}}' > "$TMP/empty.json"
$PY -m urirun.runtime.v2 compile "$TMP/empty.json" --out "$TMP/reg.json" >/dev/null 2>&1
$PY -m urirun.runtime.v2 node init --config "$TMP/n.json" --name local --registry "$TMP/reg.json" \
   --host 127.0.0.1 --port "$PORT" --execute >/dev/null 2>&1
$PY -m urirun.runtime.v2 node serve --config "$TMP/n.json" --execute --key-auth --allow 'browser://**' \
   >"$TMP/node.log" 2>&1 & PIDS+=($!)
for _ in $(seq 1 40); do curl -fsS "$N/health" >/dev/null 2>&1 && break; sleep 0.25; done

echo "== enroll key + deploy the CDP surface =="
$PY -m urirun.runtime.v2 host copy-id "$N" --identity "$TMP/.ssh/id_ed25519" >/dev/null 2>&1
$PY -m urirun.runtime.v2 host deploy "$N" --bindings "$TMP/cdp.bindings.json" --code "$TMP/cdp-flat-handler.py" \
   --allow 'browser://**' --identity "$TMP/.ssh/id_ed25519" \
   | $PY -c 'import sys,json;d=json.load(sys.stdin);print("  deploy ok=",d.get("ok"),"routeCount=",d.get("routeCount"))'

echo "== drive the local browser over CDP =="
NODE_URL="$N" NODE=local $PY "$HERE/drive_cdp.py" "${1:-https://example.com}"
