#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"

SERVICE_MAP = {
    "pc1": os.environ.get("PC1_API_URL", "http://127.0.0.1:9001").rstrip("/"),
    "pc2": os.environ.get("PC2_API_URL", "http://127.0.0.1:9002").rstrip("/"),
    "pc3": os.environ.get("PC3_API_URL", "http://127.0.0.1:9003").rstrip("/"),
    "pc4": os.environ.get("PC4_API_URL", "http://127.0.0.1:9004").rstrip("/"),
}

REGISTRY_SERVICE_MAP = {
    "pc1": os.environ.get("PC1_REGISTRY_URL", SERVICE_MAP["pc1"]).rstrip("/"),
    "pc2": os.environ.get("PC2_REGISTRY_URL", SERVICE_MAP["pc2"]).rstrip("/"),
    "pc3": os.environ.get("PC3_REGISTRY_URL", SERVICE_MAP["pc3"]).rstrip("/"),
    "pc4": os.environ.get("PC4_REGISTRY_URL", SERVICE_MAP["pc4"]).rstrip("/"),
}


BASIC_FLOW = {
    "task": {
        "id": "novnc_browser_demo",
        "title": "Open pages inside noVNC computers through URI commands",
        "source": "examples/11-novnc_lan_flow",
    },
    "steps": [
        {
            "id": "pc1_log",
            "uri": "log://pc1/session/command/write",
            "payload": {"event": "flow.started", "detail": {"target": "pc1"}},
            "depends_on": [],
        },
        {
            "id": "pc1_open",
            "uri": "browser://pc1/page/command/open",
            "payload": {"url": "https://example.com/"},
            "depends_on": ["pc1_log"],
        },
        {
            "id": "pc1_screenshot",
            "uri": "browser://pc1/page/command/screenshot",
            "payload": {"url": "https://example.com/", "output": "pc1-example.png"},
            "depends_on": ["pc1_open"],
        },
        {
            "id": "pc2_open",
            "uri": "browser://pc2/page/command/open",
            "payload": {"url": "https://ifuri.com/"},
            "depends_on": [],
        },
        {
            "id": "pc2_screenshot",
            "uri": "browser://pc2/page/command/screenshot",
            "payload": {"url": "https://ifuri.com/", "output": "pc2-ifuri.png"},
            "depends_on": ["pc2_open"],
        },
        {
            "id": "pc2_logs",
            "uri": "log://pc2/session/query/recent",
            "payload": {"limit": 20},
            "depends_on": ["pc2_screenshot"],
        },
    ],
}

FULL_FLOW = {
    "task": {
        "id": "novnc_four_computer_demo",
        "title": "Run a four-computer URI flow across browser, app and log routes",
        "source": "examples/11-novnc_lan_flow",
    },
    "steps": [
        {
            "id": "pc1_note_add",
            "uri": "app://pc1/notes/command/add",
            "payload": {"text": "Prepare URI flow demo", "tags": ["demo", "pc1"]},
            "depends_on": [],
        },
        {
            "id": "pc1_open",
            "uri": "browser://pc1/page/command/open",
            "payload": {"url": "https://example.com/"},
            "depends_on": ["pc1_note_add"],
        },
        {
            "id": "pc1_screenshot",
            "uri": "browser://pc1/page/command/screenshot",
            "payload": {"url": "https://example.com/", "output": "pc1-example.png"},
            "depends_on": ["pc1_open"],
        },
        {
            "id": "pc1_notes",
            "uri": "app://pc1/notes/query/list",
            "payload": {"limit": 5},
            "depends_on": ["pc1_note_add"],
        },
        {
            "id": "pc2_order_create",
            "uri": "app://pc2/orders/command/create",
            "payload": {"item": "connector-test", "quantity": 2},
            "depends_on": [],
        },
        {
            "id": "pc2_open",
            "uri": "browser://pc2/page/command/open",
            "payload": {"url": "https://ifuri.com/"},
            "depends_on": ["pc2_order_create"],
        },
        {
            "id": "pc2_screenshot",
            "uri": "browser://pc2/page/command/screenshot",
            "payload": {"url": "https://ifuri.com/", "output": "pc2-ifuri.png"},
            "depends_on": ["pc2_open"],
        },
        {
            "id": "pc2_orders",
            "uri": "app://pc2/orders/query/list",
            "payload": {"limit": 5},
            "depends_on": ["pc2_order_create"],
        },
        {
            "id": "pc3_report_render",
            "uri": "app://pc3/reports/command/render",
            "payload": {"title": "Daily automation report", "format": "html", "sections": ["summary", "screenshots"]},
            "depends_on": [],
        },
        {
            "id": "pc3_open",
            "uri": "browser://pc3/page/command/open",
            "payload": {"url": "https://example.org/"},
            "depends_on": ["pc3_report_render"],
        },
        {
            "id": "pc3_screenshot",
            "uri": "browser://pc3/page/command/screenshot",
            "payload": {"url": "https://example.org/", "output": "pc3-example-org.png"},
            "depends_on": ["pc3_open"],
        },
        {
            "id": "pc3_latest_report",
            "uri": "app://pc3/reports/query/latest",
            "payload": {},
            "depends_on": ["pc3_report_render"],
        },
        {
            "id": "pc4_monitor_check",
            "uri": "app://pc4/monitor/command/check",
            "payload": {"target": "ifuri.com"},
            "depends_on": [],
        },
        {
            "id": "pc4_open",
            "uri": "browser://pc4/page/command/open",
            "payload": {"url": "https://example.net/"},
            "depends_on": ["pc4_monitor_check"],
        },
        {
            "id": "pc4_screenshot",
            "uri": "browser://pc4/page/command/screenshot",
            "payload": {"url": "https://example.net/", "output": "pc4-example-net.png"},
            "depends_on": ["pc4_open"],
        },
        {
            "id": "pc4_monitor_status",
            "uri": "app://pc4/monitor/query/status",
            "payload": {},
            "depends_on": ["pc4_monitor_check"],
        },
    ],
}

FLOW_MODE = os.environ.get("FLOW_MODE", "basic").strip().lower()
FLOW = FULL_FLOW if FLOW_MODE == "full" else BASIC_FLOW


def target_from_uri(uri: str) -> str:
    rest = uri.split("://", 1)[1] if "://" in uri else uri
    return rest.split("/", 1)[0]


def fetch_json(url: str, payload: dict[str, Any] | None = None, timeout: float = 30.0) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def wait_health(target: str, timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    last: Exception | None = None
    while time.time() < deadline:
        try:
            health = fetch_json(f"{SERVICE_MAP[target]}/health", timeout=3)
            if health.get("ok"):
                return
        except Exception as exc:  # noqa: BLE001 - retry until container API is up
            last = exc
            time.sleep(1)
    raise RuntimeError(f"{target} API not ready at {SERVICE_MAP[target]}: {last}")


def collect_routes(targets: list[str]) -> None:
    bindings: dict[str, Any] = {}
    route_lines: list[str] = []
    for target in targets:
        routes = fetch_json(f"{SERVICE_MAP[target]}/routes")
        for route in routes.get("routes") or []:
            uri = route["uri"]
            route_lines.append(uri)
            bindings[uri] = {
                "kind": route.get("kind", "command"),
                "adapter": "http-service",
                "service": REGISTRY_SERVICE_MAP[target],
            }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "routes.txt").write_text("\n".join(sorted(route_lines)) + "\n", encoding="utf-8")
    (GENERATED / "registry.json").write_text(
        json.dumps({"version": "ifuri.novnc.registry.v1", "bindings": bindings}, indent=2) + "\n",
        encoding="utf-8",
    )


def run_step(step: dict[str, Any]) -> dict[str, Any]:
    uri = step["uri"]
    target = target_from_uri(uri)
    endpoint = SERVICE_MAP[target]
    started = time.perf_counter()
    response = fetch_json(f"{endpoint}/run", {"uri": uri, "payload": step.get("payload") or {}}, timeout=60)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    return {
        "id": step["id"],
        "uri": uri,
        "target": target,
        "ok": bool(response.get("ok")),
        "elapsedMs": elapsed_ms,
        "response": response,
    }


def main() -> int:
    GENERATED.mkdir(parents=True, exist_ok=True)
    targets = sorted({target_from_uri(step["uri"]) for step in FLOW["steps"]})
    for target in targets:
        wait_health(target)
    collect_routes(targets)

    results: dict[str, Any] = {}
    timeline: list[dict[str, Any]] = []
    for step in FLOW["steps"]:
        result = run_step(step)
        results[step["id"]] = result
        timeline.append({k: result[k] for k in ("id", "uri", "target", "ok", "elapsedMs")})

    output = {"ok": all(item["ok"] for item in timeline), "mode": FLOW_MODE, "flow": FLOW, "timeline": timeline, "results": results}
    (GENERATED / "flow-result.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
