#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-$HERE/../venv/bin/python}"; [ -x "$PY" ] || PY="python3"
export NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
exec "$PY" "$HERE/run_scenarios.py" "$@"
