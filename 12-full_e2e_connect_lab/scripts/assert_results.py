# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    base = Path(sys.argv[1] if len(sys.argv) > 1 else "generated")
    nodes = load(base / "nodes.json")
    routes_doc = load(base / "routes.json")
    agents = load(base / "agents.json")
    registry = load(base / "registry-runtime.json")
    flow = load(base / "flow-result.json")
    connectors = load(base / "connectors-result.json")
    page = (base / "ifuri-test-page.html").read_text(encoding="utf-8")
    installer_routes = (base / "connectors-install-routes.txt").read_text(encoding="utf-8")

    node_items = nodes.get("nodes") or nodes
    assert len(node_items) >= 2, node_items
    reachable = {node["name"] for node in node_items if node.get("reachable")}
    assert {"pc1", "pc2"}.issubset(reachable), reachable

    routes = routes_doc.get("routes") or []
    route_uris = {route["uri"] for route in routes}
    for target in ("pc1", "pc2"):
        assert f"env://{target}/runtime/query/health" in route_uris
        assert f"proc://{target}/process/query/list" in route_uris
        assert f"shell://{target}/command/date" in route_uris

    registry_bindings = registry.get("bindings") or {}
    assert "env://pc1/runtime/query/health" in registry_bindings
    assert "env://pc2/runtime/query/health" in registry_bindings

    assert agents.get("nodes"), agents
    assert "ifuri.com test page" in page.lower(), page[:200]

    assert flow.get("ok") is True, flow
    timeline = flow.get("timeline") or []
    assert len(timeline) >= 4, timeline
    assert all(item.get("ok") for item in timeline), timeline
    assert {"pc1", "pc2"}.issubset({item.get("target") for item in timeline}), timeline

    assert connectors.get("ok") is True, connectors.get("failures")
    for uri in (
        "httpcheck://host/http/query/status",
        "time://host/clock/query/now",
        "data://host/records/query/search",
        "monitor://host/http/query/status",
        "dns://host/records/command/plan",
        "task://host/ticket/command/create",
        "planfile://host/dsl/command/run",
        "browser://desktop/page/command/open",
        "browser://desktop/page/command/screenshot",
    ):
        assert uri in installer_routes, (uri, installer_routes)
    catalog = connectors.get("catalog") or {}
    available = set(catalog.get("available") or [])
    assert {"planfile", "sqlite-context", "domain-monitor", "http-check", "time-tools", "namecheap-dns", "grpc-transport", "browser-control"}.issubset(available), available
    assert {"mqtt"}.issubset(set(catalog.get("plannedSkipped") or [])), catalog
    route_results = connectors.get("routeResults") or {}
    for key in (
        "http_check",
        "time_now",
        "browser_open",
        "browser_screenshot",
        "domain_monitor_http",
        "domain_monitor_dns_current",
        "domain_flow",
        "namecheap_plan",
        "namecheap_backup",
        "namecheap_apply_mock",
        "sqlite_dataset_create",
        "sqlite_record_upsert",
        "artifact_register",
        "artifact_list",
        "check_add",
        "check_recent",
        "task_create",
        "planfile_dsl",
        "task_complete",
        "logs_recent",
    ):
        assert route_results.get(key, {}).get("ok") is True, (key, route_results.get(key))
    assert connectors.get("mcp", {}).get("toolCount", 0) >= 10, connectors.get("mcp")
    assert connectors.get("a2a", {}).get("skillCount", 0) >= 10, connectors.get("a2a")
    assert connectors.get("grpc", {}).get("ok") is True, connectors.get("grpc")

    print(
        json.dumps(
            {
                "ok": True,
                "nodes": sorted(reachable),
                "routes": len(routes),
                "flowSteps": len(timeline),
                "registryBindings": len(registry_bindings),
                "installerRegistryRoutes": len([line for line in installer_routes.splitlines() if "://" in line]),
                "connectorRoutes": len(route_results),
                "connectorMcpTools": connectors.get("mcp", {}).get("toolCount"),
                "connectorA2aSkills": connectors.get("a2a", {}).get("skillCount"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
