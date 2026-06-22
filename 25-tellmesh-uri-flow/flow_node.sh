#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The same kvm -> ocr -> llm flow, but over a NETWORK TRANSPORT: the registry is
# served by `urirun node serve` (HTTP), and each step is a POST /run to the node.
# The node's `--allow` globs are its security boundary; jq threads each step's
# result.value into the next step's request. Same URIs, same data flow — now remote.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERE}/generated"
HOST="${HOST:-host1}"
MON="${MONITOR:-0}"

export PYTHONPATH="${HERE}/packs:${HERE}/../../urirun/adapters/python:${PYTHONPATH:-}"
U() { python3 -m urirun.runtime.v2 "$@"; }
command -v jq >/dev/null 2>&1 || { echo "this flow needs jq"; exit 1; }
command -v curl >/dev/null 2>&1 || { echo "this flow needs curl"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT"
PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1]);s.close()')"

echo "== adopt 3 packs -> one registry =="
for p in flow_kvm flow_ocr flow_llm; do
  U adopt-pack "${HERE}/packs/${p}/manifest.yaml" --out "${OUT}/${p}.bindings.json" >/dev/null
done
U compile "${OUT}"/flow_*.bindings.json --out "${OUT}/flow.registry.json" >/dev/null

echo "== serve the registry as a node on 127.0.0.1:${PORT} (execute, allow kvm/ocr/llm) =="
U node init --config "${OUT}/node.json" --name flownode --registry "${OUT}/flow.registry.json" \
  --host 127.0.0.1 --port "$PORT" --execute >/dev/null
U node serve --config "${OUT}/node.json" --execute \
  --allow 'kvm://**' --allow 'ocr://**' --allow 'llm://**' > "${OUT}/node.log" 2>&1 &
NODE_PID=$!
trap 'kill "$NODE_PID" >/dev/null 2>&1 || true; wait "$NODE_PID" 2>/dev/null || true' EXIT

# wait for the node to be healthy
up=0
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null 2>&1; then up=1; break; fi
  sleep 0.25
done
[ "$up" = 1 ] || { echo "FAIL: node did not become healthy"; cat "${OUT}/node.log"; exit 1; }
echo "node healthy: $(curl -s "http://127.0.0.1:${PORT}/health" | jq -c '{name,execute,routeCount}')"

post() { curl -s -X POST "http://127.0.0.1:${PORT}/run" -H 'Content-Type: application/json' -d "$1"; }
run_step() { # <uri> <payload-json>
  post "$(jq -nc --arg u "$1" --argjson pl "$2" '{uri:$u, payload:$pl}')"
}

echo "== run the chain over HTTP (POST /run per step, jq threads the data) =="

env1="$(run_step "kvm://${HOST}/monitor/command/capture" "$(jq -nc --argjson m "$MON" '{monitor:$m}')")"
image_id="$(jq -r '.result.value.image_id' <<<"$env1")"
echo "  [1] POST kvm capture       -> image_id=${image_id}"

env2="$(run_step "ocr://${HOST}/image/query/text" "$(jq -nc --arg id "$image_id" '{image_id:$id}')")"
text="$(jq -r '.result.value.text' <<<"$env2")"
echo "  [2] POST ocr image=${image_id} -> text=\"${text}\""

prompt="Summarize this scanned text:
${text}"
env3="$(run_step "llm://${HOST}/chat/command/complete" "$(jq -nc --arg p "$prompt" '{prompt:$p}')")"
summary="$(jq -r '.result.value.summary' <<<"$env3")"
echo "  [3] POST llm complete      -> summary=\"${summary}\""

echo ""
echo "flow result (over the node): ${summary}"
case "$summary" in
  *42.00*2026-07-01*) echo "end-to-end (kvm->ocr->llm) threaded correctly over HTTP: ok" ;;
  *) echo "FAIL: data did not thread end to end over the node"; exit 1 ;;
esac
