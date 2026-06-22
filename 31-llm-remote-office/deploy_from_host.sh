#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# RUN THIS ON THE HOST. Provision the office surface onto a running node OVER THE MESH
# (no SSH): build the office bindings locally, then push the bindings + the bridge code
# + the handler env to the node's POST /deploy. The node hot-swaps what it serves — its
# route count jumps from 7 (base) to 34 (office) without a restart.
#
# Prerequisite (one time): the node must already run urirun started with an admin token
#   URIRUN_NODE_TOKEN=… ./node_serve.sh        # on the node, OR any urirun node started
#                                              # with --admin-token in a tellmesh-capable env
#
#   URIRUN_NODE_TOKEN=secret ./deploy_from_host.sh
#   NODE_URL=http://192.168.188.201:8765 URIRUN_NODE_TOKEN=secret ./deploy_from_host.sh
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
NODE_NAME="${NODE_NAME:-lenovo}"
ALLOW_REAL="${ALLOW_REAL:-1}"
# On the NODE the handlers import the tellmesh packs from here; adjust if the node's
# checkout differs (this path is interpreted on the node).
REMOTE_TELLMESH="${REMOTE_TELLMESH:-$HOME/github/tellmesh}"
PY="${PY:-$HERE/../venv/bin/python}"; [ -x "$PY" ] || PY="python3"

: "${URIRUN_NODE_TOKEN:?set URIRUN_NODE_TOKEN to the node admin token}"
export PYTHONPATH="$HERE:$HERE/../../urirun/adapters/python:${PYTHONPATH:-}"

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
  --token "$URIRUN_NODE_TOKEN"

echo "== verify =="
curl -s "$NODE_URL/health"
echo
echo "done — now drive it:  ./office_cli.sh \"open https://example.com and screenshot\" --yes"
