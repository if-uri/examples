#!/usr/bin/env bash
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

set -euo pipefail

cd "$(dirname "$0")/.."

export FLOW_MODE="${FLOW_MODE:-basic}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-18192}"
export PC1_NOVNC_PORT="${PC1_NOVNC_PORT:-17901}"
export PC2_NOVNC_PORT="${PC2_NOVNC_PORT:-17902}"
export PC3_NOVNC_PORT="${PC3_NOVNC_PORT:-17903}"
export PC4_NOVNC_PORT="${PC4_NOVNC_PORT:-17904}"
export PC1_API_PORT="${PC1_API_PORT:-19001}"
export PC2_API_PORT="${PC2_API_PORT:-19002}"
export PC3_API_PORT="${PC3_API_PORT:-19003}"
export PC4_API_PORT="${PC4_API_PORT:-19004}"
export PC1_API_URL="http://127.0.0.1:${PC1_API_PORT}"
export PC2_API_URL="http://127.0.0.1:${PC2_API_PORT}"
export PC3_API_URL="http://127.0.0.1:${PC3_API_PORT}"
export PC4_API_URL="http://127.0.0.1:${PC4_API_PORT}"
export PC1_REGISTRY_URL="${PC1_REGISTRY_URL:-http://127.0.0.1:9001}"
export PC2_REGISTRY_URL="${PC2_REGISTRY_URL:-http://127.0.0.1:9002}"
export PC3_REGISTRY_URL="${PC3_REGISTRY_URL:-http://127.0.0.1:9003}"
export PC4_REGISTRY_URL="${PC4_REGISTRY_URL:-http://127.0.0.1:9004}"

cleanup() {
  docker compose --profile full down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

mkdir -p generated/screenshots
rm -f generated/flow-result.json generated/smoke-output.json generated/screenshots/*.png

if [[ "$FLOW_MODE" == "full" ]]; then
  docker compose --profile full up -d --build \
    dashboard \
    pc1-browser pc1-api pc2-browser pc2-api \
    pc3-browser pc3-api pc4-browser pc4-api
else
  docker compose up -d --build dashboard pc1-browser pc1-api pc2-browser pc2-api
fi
python3 orchestrator/run_flow.py > generated/smoke-output.json

python3 - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

base = Path("generated")
mode = os.environ.get("FLOW_MODE", "basic")
result = json.loads((base / "flow-result.json").read_text(encoding="utf-8"))
assert result.get("ok") is True, result
timeline = result.get("timeline") or []
assert len(timeline) >= (16 if mode == "full" else 6), timeline
assert all(item.get("ok") for item in timeline), timeline
routes = (base / "routes.txt").read_text(encoding="utf-8")
expected_routes = [
    "browser://pc1/page/command/open",
    "browser://pc1/page/command/screenshot",
    "browser://pc2/page/command/open",
    "browser://pc2/page/command/screenshot",
]
expected_screenshots = ["pc1-example.png", "pc2-ifuri.png"]
if mode == "full":
    expected_routes.extend([
        "app://pc1/notes/command/add",
        "app://pc1/notes/query/list",
        "app://pc2/orders/command/create",
        "app://pc2/orders/query/list",
        "app://pc3/reports/command/render",
        "app://pc3/reports/query/latest",
        "app://pc4/monitor/command/check",
        "app://pc4/monitor/query/status",
        "browser://pc3/page/command/open",
        "browser://pc4/page/command/open",
    ])
    expected_screenshots.extend(["pc3-example-org.png", "pc4-example-net.png"])
for route in expected_routes:
    assert route in routes, route
for name in expected_screenshots:
    path = base / "screenshots" / name
    assert path.is_file() and path.stat().st_size > 1000, str(path)
print(json.dumps({
    "ok": True,
    "mode": mode,
    "steps": len(timeline),
    "routes": len([line for line in routes.splitlines() if line.strip()]),
    "screenshots": sorted(p.name for p in (base / "screenshots").glob("*.png")),
}, indent=2))
PY
