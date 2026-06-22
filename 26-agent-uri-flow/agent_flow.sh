#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# An AGENT composes and runs the kvm -> ocr -> llm flow from the available URIs,
# entirely through the `urirun agent` CLI:
#   1. `urirun agent space`  — the action space (routes the agent may choose)
#   2. `urirun agent run --planner planner:plan`  — the planner picks {uri,payload}
#      steps (with $ref threading); each runs under the --allow policy.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PACKS="${HERE}/../25-tellmesh-uri-flow/packs"   # reuse the adopted flow packs
OUT="${HERE}/generated"

# planner module + handler packages + in-repo urirun on the import path
export PYTHONPATH="${HERE}:${PACKS}:${HERE}/../../urirun/adapters/python:${PYTHONPATH:-}"
U() { python3 -m urirun.runtime.v2 "$@"; }
command -v jq >/dev/null 2>&1 || { echo "this demo needs jq"; exit 1; }

rm -rf "$OUT"; mkdir -p "$OUT"

echo "== adopt the flow packs -> one registry =="
for p in flow_kvm flow_ocr flow_llm; do
  U adopt-pack "${PACKS}/${p}/manifest.yaml" --out "${OUT}/${p}.bindings.json" >/dev/null
done
U compile "${OUT}"/flow_*.bindings.json --out "${OUT}/flow.registry.json" >/dev/null

echo "== action space the agent sees =="
U agent space "${OUT}/flow.registry.json" | jq -c '.[] | {uri, kind, inputs}'

echo ""
echo "== agent run (planner composes + executes the chain under policy) =="
U agent run "${OUT}/flow.registry.json" \
  --goal "capture the screen, read its text, and summarize it" \
  --planner planner:plan \
  --allow 'kvm://**' --allow 'ocr://**' --allow 'llm://**' --allow-commands \
  > "${OUT}/agent.report.json"

jq -r '.steps[] | "  [\(.uri)]\n      why: \(.why)\n      out: \(.data | tojson)"' "${OUT}/agent.report.json"
summary="$(jq -r '.steps[-1].data.summary' "${OUT}/agent.report.json")"
ok="$(jq -r '.ok' "${OUT}/agent.report.json")"
echo ""
echo "agent goal satisfied (ok=${ok}); final summary: ${summary}"
case "$summary" in
  *42.00*2026-07-01*) echo "agent composed kvm->ocr->llm from the action space and ran it: ok" ;;
  *) echo "FAIL: agent flow did not produce the expected summary"; exit 1 ;;
esac
