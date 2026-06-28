#!/usr/bin/env bash
# The runtime side: install urirun + the connector, compile the connector's
# bindings into a registry, and serve it over HTTP under an allow-list.
set -euo pipefail
rm -rf /tmp/urirun-contract /tmp/urirun /tmp/connector
cp -r /src/urirun-contract /tmp/urirun-contract && cp -r /src/urirun /tmp/urirun && cp -r /src/connector /tmp/connector
rm -rf /tmp/urirun-contract/{build,dist,*.egg-info} /tmp/urirun/{build,dist,*.egg-info} /tmp/connector/{build,dist,*.egg-info}
pip install --quiet --force-reinstall /tmp/urirun-contract
pip install --quiet "jsonschema>=4.18" "pydantic>=2"
pip install --quiet --force-reinstall --no-deps /tmp/urirun
pip install --quiet --force-reinstall --no-deps /tmp/connector
python -c "import json,urirun_connector_domain_monitor as c; json.dump(c.urirun_bindings(), open('/tmp/b.json','w'))"
urirun validate /tmp/b.json
urirun compile /tmp/b.json --out /tmp/registry.json
echo "[node] serving domain-monitor over HTTP :8765  (allow: monitor://*, log://*)"
exec urirun node serve --registry /tmp/registry.json --host 0.0.0.0 --port 8765 \
  --execute --allow 'monitor://*' --allow 'log://*'
