#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Adopt a whole tree of tellmesh-style capability packs into ONE urirun registry.
# `urirun adopt-pack <dir>` now walks every manifest.yaml under the tree and merges
# them, so the old per-pack loop + compile collapses to a single command.
#
# Usage:  ./adopt.sh [TELLMESH_DIR]      # default: ../../../tellmesh
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
TELLMESH="${1:-${TELLMESH_DIR:-${HERE}/../../../tellmesh}}"
OUT="${OUT_DIR:-${HERE}/generated}"
REPO_URIRUN="${HERE}/../../urirun/adapters/python"
[ -d "$REPO_URIRUN" ] && export PYTHONPATH="${REPO_URIRUN}:${PYTHONPATH:-}"
U() { "${PYTHON:-python3}" -m urirun.runtime.v2 "$@"; }

SRC="$TELLMESH"; [ -d "$SRC" ] || SRC="${HERE}/manifests"
rm -rf "$OUT"; mkdir -p "$OUT"

# 1) ONE command: adopt the whole tree -> merged bindings + compiled registry.
echo "== adopt every pack under ${SRC} =="
U adopt-pack "$SRC" --out "$OUT/tellmesh.bindings.json" \
  --registry-out "$OUT/tellmesh.registry.json" --on-conflict keep

# 2) report + validate.
U validate "$OUT/tellmesh.bindings.json" >/dev/null && echo "merged document is valid"
"${PYTHON:-python3}" - "$OUT/tellmesh.bindings.json" "$OUT/tellmesh.registry.json" <<'PY'
import json, sys
b = json.load(open(sys.argv[1]))["bindings"]
r = json.load(open(sys.argv[2]))
schemes = sorted({u.split("://", 1)[0] for u in b})
print(f"merged: {len(b)} routes across {len(schemes)} packs -> {r.get('count') or len(r.get('index', {}))} compiled")
print("schemes:", ", ".join(schemes))
PY
echo "done — one merged dispatch surface over all packs: $OUT/tellmesh.registry.json"
