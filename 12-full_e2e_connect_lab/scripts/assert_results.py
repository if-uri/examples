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
    page = (base / "ifuri-test-page.html").read_text(encoding="utf-8")

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

    print(
        json.dumps(
            {
                "ok": True,
                "nodes": sorted(reachable),
                "routes": len(routes),
                "flowSteps": len(timeline),
                "registryBindings": len(registry_bindings),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
