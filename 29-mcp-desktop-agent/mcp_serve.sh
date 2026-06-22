#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The zero-code MCP surface: urirun projects the desktop connector's routes to MCP
# tools (and an A2A agent card) with no extra code — each tool is name + inputSchema,
# which is exactly what an MCP client (Claude, etc.) needs to call it.
set -Eeuo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${HERE}/generated"; mkdir -p "$OUT"
export PYTHONPATH="${HERE}/../28-llm-novnc-desktop:${HERE}/../../urirun/adapters/python:${PYTHONPATH:-}"

# 1) serialize the connector's bindings to a file (no live handler needed to LIST tools)
python3 -c "
import json
from novnc_connector.core import conn
json.dump(conn.bindings(), open('${OUT}/desktop.bindings.json','w'), indent=2)
print('wrote ${OUT}/desktop.bindings.json')
"

echo "== MCP tools/list (what an MCP client sees) =="
python3 -m urirun.v2_mcp tools "${OUT}/desktop.bindings.json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f\"  {t['name']:42} {list((t.get('inputSchema') or {}).get('properties',{}).keys())}  — {t['description']}\") for t in d['tools']]"

echo ""
echo "== A2A agent card (same schema, agent discovery) =="
python3 -m urirun.v2_mcp card "${OUT}/desktop.bindings.json" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('  name:', d['name'], '| skills:', len(d['skills']))"

cat <<EOF

== to run a live MCP server (stdio JSON-RPC: initialize / tools/list / tools/call) ==
  # against the installed connector's runnable registry (so tools/call EXECUTES):
  python3 -m urirun.v2_mcp serve <registry> --execute

A Claude / MCP client then lists these tools and calls them — driving the desktop
with no custom planner. mcp_agent.py does exactly that loop in-process.
EOF
