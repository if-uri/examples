#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p .state
ROOT="$(cd ../.. && pwd)"
URIRUN_PY="${URIRUN_PY:-$ROOT/urirun/adapters/python}"

PYTHONPATH="$URIRUN_PY:${PYTHONPATH:-}" \
  python3 -m urirun.runtime.v2 compile bindings.json --out .state/local-portals.registry.json >/dev/null

PYTHONPATH="$URIRUN_PY:$PWD:$ROOT/examples/39-local-social-autonomy:${PYTHONPATH:-}" \
  python3 -m urirun.runtime.v2 agent run .state/local-portals.registry.json \
    --planner portal_autonomy:planner \
    --allow 'portal://**' \
    --allow-commands \
    --goal "$*"
