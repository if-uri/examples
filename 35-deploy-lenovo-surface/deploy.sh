#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Push a self-contained office/browser/tools surface onto a remote urirun node
# over POST /deploy — no SSH, no pip on the node. Both: enrolls your SSH key
# (trust-on-first-use / signed) and hot-swaps the node's served registry.
#
#   NODE_URL=http://192.168.188.201:8765 ./deploy.sh
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
IDENTITY="${IDENTITY:-$HOME/.ssh/id_ed25519}"
PY="${PY:-$ROOT/urirun/venv/bin/python3}"
[ -x "$PY" ] || PY=python3
export PYTHONPATH="$ROOT/urirun/adapters/python:$HERE:${PYTHONPATH:-}"

echo "== generate bindings (local-function, deployable) =="
"$PY" -c "import json,lenovo_node; open('$HERE/node-surface.bindings.json','w').write(json.dumps(lenovo_node.urirun_bindings()))"

echo "== enroll SSH key on $NODE_URL (TOFU / signed) =="
"$PY" -m urirun.runtime.v2 host copy-id "$NODE_URL" --identity "$IDENTITY" || true

echo "== deploy the surface =="
"$PY" -m urirun.runtime.v2 host deploy "$NODE_URL" \
  --bindings "$HERE/node-surface.bindings.json" --code "$HERE/lenovo_node.py" \
  --allow 'browser://**' --allow 'sys://**' --allow 'fs://**' --allow 'codec://**' \
  --allow 'hash://**' --allow 'uuid://**' --allow 'httpcheck://**' --allow 'office://**' \
  --identity "$IDENTITY"

echo "== verify =="
NODE_URL="$NODE_URL" "$PY" "$HERE/verify.py"
