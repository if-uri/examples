#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# RUN THIS ON THE NODE (the machine being controlled, e.g. 192.168.188.201).
#
# (Re)serve a urirun node on the DEFAULT urirun port (8765) that exposes the tellmesh
# office/desktop URI surface — him (mouse/keyboard), kvm, browser, urioffice, screen,
# shell — plus health + node-logging, so a host can drive it over the urirun mesh.
#
#   ./node_serve.sh                 # name=lenovo, 0.0.0.0:8765, drives the real machine
#   NODE_NAME=officepc NODE_PORT=8765 ./node_serve.sh
#   ALLOW_REAL=0 ./node_serve.sh    # mock mode (no real mouse/keyboard/browser)
#
# Override paths if your checkout differs:
#   IFURI_DIR=~/github/if-uri TELLMESH_DIR=~/github/tellmesh ./node_serve.sh
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

NODE_NAME="${NODE_NAME:-lenovo}"
NODE_HOST="${NODE_HOST:-0.0.0.0}"
NODE_PORT="${NODE_PORT:-8765}"
ALLOW_REAL="${ALLOW_REAL:-1}"
# POST /deploy lets the host re-provision this node over the mesh (new bindings / code /
# allow) WITHOUT touching it again. Enabled by default with SSH-key auth: from the host
# run `uri-copy-id <this-host>` once (no shared secret), then `host deploy --identity`.
# Set URIRUN_NODE_TOKEN to also accept a token, KEYAUTH=0 to drop key-auth, DEPLOY=0 off.
DEPLOY="${DEPLOY:-1}"
KEYAUTH="${KEYAUTH:-1}"
ADMIN_TOKEN="${URIRUN_NODE_TOKEN:-}"
AUTH_ARGS=()
if [ "$DEPLOY" = "1" ]; then
  [ "$KEYAUTH" = "1" ] && AUTH_ARGS+=(--key-auth)
  [ -n "$ADMIN_TOKEN" ] && AUTH_ARGS+=(--admin-token "$ADMIN_TOKEN")
fi
IFURI_DIR="${IFURI_DIR:-$(cd "$HERE/../.." && pwd)}"
TELLMESH_DIR="${TELLMESH_DIR:-$(cd "$IFURI_DIR/.." && pwd)/tellmesh}"

# Prefer the tellmesh node venv: it has urirun + uricontrol + the connectors installed.
PY="${PY:-$TELLMESH_DIR/urisys-node/.venv/bin/python}"
[ -x "$PY" ] || PY="$IFURI_DIR/examples/venv/bin/python"
[ -x "$PY" ] || PY="python3"

export TELLMESH_DIR
export URISYS_ALLOW_REAL="$ALLOW_REAL"
# tellmesh_bridge (this dir) + urirun adapters must be importable; the bridge adds the
# individual tellmesh pack source dirs to sys.path itself.
export PYTHONPATH="$HERE:$IFURI_DIR/urirun/adapters/python:${PYTHONPATH:-}"

echo "== urirun office node =="
echo "  python      : $PY"
echo "  ifuri dir   : $IFURI_DIR"
echo "  tellmesh dir: $TELLMESH_DIR"
echo "  serving     : $NODE_NAME on $NODE_HOST:$NODE_PORT  (allow_real=$ALLOW_REAL)"
if [ "$DEPLOY" = "1" ]; then
  echo "  deploy /api : ENABLED${KEYAUTH:+ (ssh-key: run 'uri-copy-id' from the host)}${ADMIN_TOKEN:+ + pinned token}"
else
  echo "  deploy /api : off (DEPLOY=0)"
fi
echo

CFG="$HERE/generated/${NODE_NAME}.node.json"
REG="$HERE/generated/node-office.registry.json"

echo "-- building registry (tellmesh office surface + base) --"
"$PY" "$HERE/build_node_registry.py" --name "$NODE_NAME"

echo "-- stopping any node already on :$NODE_PORT --"
systemctl --user stop urirun-node 2>/dev/null || true
# kill a previous office node we started (match this registry), and free the port
pkill -f "urirun.runtime.v2 node serve.*${NODE_NAME}.node.json" 2>/dev/null || true
if command -v fuser >/dev/null 2>&1; then fuser -k "${NODE_PORT}/tcp" 2>/dev/null || true; fi
sleep 1

echo "-- init + serve --"
"$PY" -m urirun.runtime.v2 node init --config "$CFG" --name "$NODE_NAME" \
  --registry "$REG" --host "$NODE_HOST" --port "$NODE_PORT" --execute >/dev/null

# --manage exposes admin-gated node:// URIs (pip install into the node venv, etc.) so the
# office surface (tellmesh) can be provisioned over the mesh — set MANAGE=0 to drop it.
MANAGE_ARGS=(); [ "${MANAGE:-1}" = "1" ] && [ "$DEPLOY" = "1" ] && MANAGE_ARGS=(--manage)

# Open policy (your choice): every office scheme may execute, including arbitrary shell.
exec "$PY" -m urirun.runtime.v2 node serve --config "$CFG" --execute \
  "${AUTH_ARGS[@]}" "${MANAGE_ARGS[@]}" \
  --allow "him://${NODE_NAME}/**" \
  --allow "kvm://${NODE_NAME}/**" \
  --allow "browser://${NODE_NAME}/**" \
  --allow "screen://${NODE_NAME}/**" \
  --allow "shell://${NODE_NAME}/**" \
  --allow "urioffice://${NODE_NAME}/**" \
  --allow "log://${NODE_NAME}/**" \
  --allow "env://${NODE_NAME}/**" \
  --allow "proc://${NODE_NAME}/**"
