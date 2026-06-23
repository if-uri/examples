#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p .state
ROOT="$(cd ../.. && pwd)"
URIRUN_PY="${URIRUN_PY:-$ROOT/urirun/adapters/python}"
ENV_FILE="${ENV_FILE:-$PWD/.env}"
ROUTE="browser://local/linkedin/session/query/find"

PYTHONPATH="$URIRUN_PY:$PWD:${PYTHONPATH:-}" \
  python3 session_probe.py --write-bindings .state/session-probe.bindings.json

PYTHONPATH="$URIRUN_PY:${PYTHONPATH:-}" \
  python3 -m urirun.runtime.v2 compile .state/session-probe.bindings.json \
    --out .state/session-probe.registry.json >/dev/null

PYTHONPATH="$URIRUN_PY:$PWD:${PYTHONPATH:-}" \
  python3 -m urirun.runtime.v2 run "$ROUTE" .state/session-probe.registry.json \
    --allow 'browser://**' \
    --payload "{\"env\": \"$ENV_FILE\"}" \
    --execute
