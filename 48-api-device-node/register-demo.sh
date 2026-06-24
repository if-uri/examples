#!/usr/bin/env bash
set -euo pipefail

URIRUN="${URIRUN:-/home/tom/github/if-uri/urirun/venv/bin/urirun}"
CONFIG="${CONFIG:-/tmp/urirun-api-device.mesh.json}"

"$URIRUN" host init --config "$CONFIG" --name api-device-demo >/dev/null

"$URIRUN" host add-node crm-api https://api.example.test/v1 \
  --config "$CONFIG" \
  --kind api \
  --api-id main \
  --api-kind rest

"$URIRUN" host add-node rpi-camera http://rpi.local \
  --config "$CONFIG" \
  --kind device \
  --api '{"id":"panel","kind":"web","url":"http://rpi.local"}' \
  --api '{"id":"stream","kind":"rtsp","role":"camera","url":"rtsp://rpi.local/live"}' \
  --api '{"id":"share","kind":"smb","url":"smb://rpi.local/share"}' \
  --api '{"id":"ssh","kind":"ssh","url":"ssh://pi@rpi.local"}'

echo "Wrote demo mesh: $CONFIG"
