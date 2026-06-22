#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# RUN THIS ON THE HOST. Provision the office surface onto a running node OVER THE MESH
# (no SSH): build the office bindings locally, then push the bindings + the bridge code
# + the handler env to the node's POST /deploy. The node hot-swaps what it serves — its
# route count jumps from 7 (base) to 34 (office) without a restart.
#
# Prerequisite (one time): the node runs urirun with /deploy enabled (node.sh does this
# by default with SSH-key auth). Auth is your SSH key — no shared secret:
#
#   ./deploy_from_host.sh                       # enrolls ~/.ssh/id_ed25519 (copy-id) then deploys
#   URIRUN_NODE_TOKEN=secret ./deploy_from_host.sh   # use a token instead of the SSH key
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
NODE_NAME="${NODE_NAME:-lenovo}"
ALLOW_REAL="${ALLOW_REAL:-1}"
IDENTITY="${IDENTITY:-$HOME/.ssh/id_ed25519}"
# On the NODE the handlers import the tellmesh packs from here; adjust if the node's
# checkout differs (this path is interpreted on the node).
REMOTE_TELLMESH="${REMOTE_TELLMESH:-$HOME/github/tellmesh}"
PY="${PY:-$HERE/../venv/bin/python}"; [ -x "$PY" ] || PY="python3"
export PYTHONPATH="$HERE:$HERE/../../urirun/adapters/python:${PYTHONPATH:-}"

# Auth: SSH key by default; --token if URIRUN_NODE_TOKEN is set.
if [ -n "${URIRUN_NODE_TOKEN:-}" ]; then
  AUTH=(--token "$URIRUN_NODE_TOKEN")
else
  echo "== enroll SSH key on $NODE_URL (uri-copy-id; trust-on-first-use) =="
  "$PY" -m urirun.runtime.v2 host copy-id "$NODE_URL" --identity "$IDENTITY" || true
  AUTH=(--identity "$IDENTITY")
fi

echo "== build office bindings locally =="
"$PY" "$HERE/build_node_registry.py" --name "$NODE_NAME"

echo "== push to $NODE_URL over the mesh =="
"$PY" -m urirun.runtime.v2 host deploy "$NODE_URL" \
  --bindings "$HERE/generated/node-office.bindings.json" \
  --code "$HERE/tellmesh_bridge.py" \
  --env "TELLMESH_DIR=$REMOTE_TELLMESH" \
  --env "URISYS_ALLOW_REAL=$ALLOW_REAL" \
  --allow "him://${NODE_NAME}/**" \
  --allow "kvm://${NODE_NAME}/**" \
  --allow "browser://${NODE_NAME}/**" \
  --allow "screen://${NODE_NAME}/**" \
  --allow "shell://${NODE_NAME}/**" \
  --allow "urioffice://${NODE_NAME}/**" \
  --allow "log://${NODE_NAME}/**" \
  --allow "env://${NODE_NAME}/**" \
  --allow "proc://${NODE_NAME}/**" \
  "${AUTH[@]}"

echo "== verify =="
curl -s "$NODE_URL/health"
echo
echo "done — now drive it:  ./office_cli.sh \"open https://example.com and screenshot\" --yes"
