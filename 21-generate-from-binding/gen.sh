#!/usr/bin/env bash
# The generator graduated from this example into urirun core: `urirun gen`.
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "import json,urirun_connector_domain_monitor as c; json.dump(c.urirun_bindings(),open('/tmp/dm.json','w'))"
urirun compile /tmp/dm.json --out /tmp/dm.reg.json >/dev/null
mkdir -p generated
urirun gen proto   /tmp/dm.reg.json --out generated/service.proto
urirun gen openapi /tmp/dm.reg.json --out generated/openapi.json
urirun gen client  /tmp/dm.reg.json --out generated/client.py
echo "generated/ ←  urirun gen proto|openapi|client (from one binding spec)"
