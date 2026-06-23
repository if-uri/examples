#!/usr/bin/env bash
set -euo pipefail

URIRUN="${URIRUN:-/home/tom/github/if-uri/urirun/venv/bin/urirun}"
NODE="${NODE:-lenovo}"
NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
IDENTITY="${IDENTITY:-$HOME/.ssh/id_ed25519}"

node_args=(--node-url "${NODE}=${NODE_URL}")
auth_args=()
if [[ -f "${IDENTITY/#\~/$HOME}" ]]; then
  auth_args=(--identity "$IDENTITY")
fi

echo "== ensure URI capabilities on ${NODE} =="
"$URIRUN" host ensure "$NODE" usb "${node_args[@]}" "${auth_args[@]}"
"$URIRUN" host ensure "$NODE" camera "${node_args[@]}" "${auth_args[@]}"
"$URIRUN" host ensure "$NODE" ocr "${node_args[@]}" "${auth_args[@]}"

echo "== USB cameras =="
"$URIRUN" host run "$NODE" 'usb://host/cameras/query/list' "${node_args[@]}" "${auth_args[@]}" --timeout 30

echo "== camera devices =="
"$URIRUN" host run "$NODE" 'camera://host/devices/query/list' "${node_args[@]}" "${auth_args[@]}" --timeout 30

echo "== OCR backends =="
"$URIRUN" host run "$NODE" 'ocr://host/backend/query/probe' "${node_args[@]}" "${auth_args[@]}" --timeout 60

echo "== beep + scan + inspect =="
"$URIRUN" host run "$NODE" 'camera://host/photo/query/inspect' "${node_args[@]}" "${auth_args[@]}" --timeout 90 \
  --payload '{"output_dir":"~/.urirun/camera-scans/live","required_text":"","min_chars":1,"require_object":false,"beep":true,"beep_on_alert":true,"fail_on_alert":false,"lang":"eng+pol"}'
