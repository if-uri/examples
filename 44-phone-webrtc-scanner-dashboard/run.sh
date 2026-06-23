#!/usr/bin/env bash
set -euo pipefail

URIRUN="${URIRUN:-/home/tom/github/if-uri/urirun/venv/bin/urirun}"
PROJECT="${PROJECT:-/home/tom/github/if-uri/urirun}"
DB="${DB:-$HOME/.urirun/host.db}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8194}"
NODE_URL="${NODE_URL:-lenovo=http://192.168.188.201:8765}"
IDENTITY="${IDENTITY:-$HOME/.ssh/id_ed25519}"

args=(
  host dashboard serve
  --project "$PROJECT"
  --db "$DB"
  --node-url "$NODE_URL"
  --host "$HOST"
  --port "$PORT"
)

if [[ -f "$IDENTITY" ]]; then
  args+=(--identity "$IDENTITY")
fi

if [[ -n "${TLS_CERT:-}" && -n "${TLS_KEY:-}" ]]; then
  args+=(--tls-cert "$TLS_CERT" --tls-key "$TLS_KEY")
fi

exec "$URIRUN" "${args[@]}"
