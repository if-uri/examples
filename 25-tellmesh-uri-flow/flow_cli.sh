#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The same kvm -> ocr -> llm flow as flow.py, but driven entirely by the `urirun`
# CLI from bash — no Python flow runner. Each step is a `urirun run ... --execute`
# call; `jq` threads each step's result.value into the next step's payload, and the
# per-step --allow glob is the policy gate.
#
# This works because `urirun adopt-pack` now emits a re-importable handler descriptor,
# so an adopted route EXECUTES from a plain file registry (no Python orchestration).
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERE}/generated"
HOST="${HOST:-host1}"
MON="${MONITOR:-0}"

# handler packages + in-repo urirun on the path the urirun process will import from
export PYTHONPATH="${HERE}/packs:${HERE}/../../urirun/adapters/python:${PYTHONPATH:-}"
U() { python3 -m urirun.runtime.v2 "$@"; }

command -v jq >/dev/null 2>&1 || { echo "this CLI flow needs jq"; exit 1; }
rm -rf "$OUT"; mkdir -p "$OUT"

echo "== adopt 3 packs -> one registry (CLI) =="
for p in flow_kvm flow_ocr flow_llm; do
  U adopt-pack "${HERE}/packs/${p}/manifest.yaml" --out "${OUT}/${p}.bindings.json" >/dev/null
done
U compile "${OUT}"/flow_*.bindings.json --out "${OUT}/flow.registry.json" >/dev/null
echo "registry: ${OUT}/flow.registry.json"

run_step() { # <uri> <payload-json> <allow-glob>
  U run "$1" "${OUT}/flow.registry.json" --payload "$2" --execute --allow "$3"
}

echo "== run the chain (urirun run per step, jq threads the data) =="

# (1) capture -> image_id
env1="$(run_step "kvm://${HOST}/monitor/command/capture" "$(jq -nc --argjson m "$MON" '{monitor:$m}')" 'kvm://**')"
image_id="$(jq -r '.result.value.image_id' <<<"$env1")"
echo "  [1] kvm capture            -> image_id=${image_id}"

# (2) ocr that exact image_id -> text
env2="$(run_step "ocr://${HOST}/image/query/text" "$(jq -nc --arg id "$image_id" '{image_id:$id}')" 'ocr://**')"
text="$(jq -r '.result.value.text' <<<"$env2")"
echo "  [2] ocr image=${image_id}    -> text=\"${text}\""

# (3) summarize the text -> summary
prompt="Summarize this scanned text:
${text}"
env3="$(run_step "llm://${HOST}/chat/command/complete" "$(jq -nc --arg p "$prompt" '{prompt:$p}')" 'llm://**')"
summary="$(jq -r '.result.value.summary' <<<"$env3")"
echo "  [3] llm complete           -> summary=\"${summary}\""

echo ""
echo "flow result: ${summary}"

# the chain is only correct if step 3's summary carries data that originated in step 1
case "$summary" in
  *42.00*2026-07-01*) echo "end-to-end (kvm->ocr->llm) threaded correctly via the CLI: ok" ;;
  *) echo "FAIL: data did not thread end to end"; exit 1 ;;
esac
