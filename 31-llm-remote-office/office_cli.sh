#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# RUN THIS ON THE HOST. Thin wrapper: pick a python with liteLLM, then drive the node.
#
#   ./office_cli.sh "open https://example.com and screenshot it" --yes
#   NODE_URL=http://192.168.188.201:8765 ./office_cli.sh "type 'hello'" --yes
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

PY="${PY:-$HERE/../venv/bin/python}"
[ -x "$PY" ] || PY="python3"

export NODE_URL="${NODE_URL:-http://192.168.188.201:8765}"
exec "$PY" "$HERE/office_agent.py" "$@"
