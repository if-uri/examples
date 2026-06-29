#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

set -euo pipefail

cd "$(dirname "$0")/.."

NO_UP=0
if [[ "${1:-}" == "--no-up" ]]; then
  NO_UP=1
fi

GET_BASE_URL="${GET_BASE_URL:-https://get.ifuri.com}"
CONNECT_BASE_URL="${CONNECT_BASE_URL:-https://connect.ifuri.com}"
URIRUN_REF="${URIRUN_REF:-v0.3.14}"
URIRUN_GIT_URL="${URIRUN_GIT_URL:-git+https://github.com/if-uri/urirun.git@${URIRUN_REF}#subdirectory=adapters/python}"
MESH_CONFIG="/tmp/ifuri-e2e-mesh.json"

mkdir -p generated
rm -f generated/*.json generated/*.html generated/*.txt

if [[ "$NO_UP" == "0" ]]; then
  docker compose up -d --build
fi

exec_pc() {
  local service="$1"
  shift
  docker compose exec -T "$service" bash -lc "$*"
}

wait_http_from_host() {
  local url="$1"
  local label="$2"
  exec_pc host "python3 - <<'PY'
import sys, time, urllib.request
url = '$url'
label = '$label'
last = None
for _ in range(90):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                print(label + ' ready')
                raise SystemExit(0)
    except Exception as exc:
        last = exc
    time.sleep(1)
raise SystemExit(f'{label} not ready: {last}')
PY"
}

install_node() {
  local name="$1"
  if exec_pc "$name" "curl -fsS http://127.0.0.1:8765/health >/dev/null 2>&1"; then
    echo "$name already running on 8765"
    return
  fi
  exec_pc "$name" "export URIRUN_GIT_URL='$URIRUN_GIT_URL'; curl -fsSL '$GET_BASE_URL/node.sh' | bash -s -- --name '$name' --port 8765 --bind 0.0.0.0 --background"
}

echo "==> Install pc1 and pc2 from $GET_BASE_URL/node.sh"
install_node pc1
install_node pc2

wait_http_from_host "http://pc1:8765/health" "pc1"
wait_http_from_host "http://pc2:8765/health" "pc2"

CONNECTORS="${CONNECTORS:-planfile,sqlite-context,domain-monitor,http-check,time-tools,grpc-transport,namecheap-dns,browser-control}"
echo "==> Install host runtime/connectors from $CONNECT_BASE_URL ($CONNECTORS)"
exec_pc host "curl -fsSL '$CONNECT_BASE_URL/install?connectors=$CONNECTORS' | bash"
exec_pc host "test -s \"\$HOME/.ifuri/connectors.registry.json\"; cp \"\$HOME/.ifuri/connectors.registry.json\" /lab/generated/connectors-install-registry.json; urirun list \"\$HOME/.ifuri/connectors.registry.json\" > /lab/generated/connectors-install-routes.txt"

echo "==> Register nodes on host"
exec_pc host "rm -f '$MESH_CONFIG'; urirun host init --config '$MESH_CONFIG' --name e2e-host >/dev/null; urirun host add-node --config '$MESH_CONFIG' pc1 http://pc1:8765 >/dev/null; urirun host add-node --config '$MESH_CONFIG' pc2 http://pc2:8765 >/dev/null"

echo "==> Query ifuri test page and registry runtime"
exec_pc host "curl -fsSL http://ifuri-site/ > /lab/generated/ifuri-test-page.html"
exec_pc host "curl -fsSL http://registry-runtime:8120/registry.json > /lab/generated/registry-runtime.json"

echo "==> Discover mesh and execute URI flow"
exec_pc host "urirun host nodes --config '$MESH_CONFIG' --json > /lab/generated/nodes.json"
exec_pc host "urirun host routes --config '$MESH_CONFIG' --json > /lab/generated/routes.json"
exec_pc host "urirun host agents --config '$MESH_CONFIG' > /lab/generated/agents.json"
exec_pc host "urirun host ask --config '$MESH_CONFIG' --node pc1 --node pc2 --no-llm --execute 'sprawdz procesy system date pc1 pc2' > /lab/generated/flow-result.json"

echo "==> Build and execute connector registry, MCP tools and A2A skills"
exec_pc host "CONNECT_BASE_URL='$CONNECT_BASE_URL' CONNECTORS='$CONNECTORS' python3 /lab/scripts/connector_checks.py"

python3 scripts/assert_results.py generated
echo "full E2E scenario OK"
