# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def nodes() -> dict[str, str]:
    result = {}
    for raw in os.getenv("NODES", "").split(","):
        if not raw.strip() or "=" not in raw:
            continue
        name, url = raw.split("=", 1)
        result[name.strip()] = url.rstrip("/")
    return result


def get_json(url: str, timeout: float = 2.5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def discover() -> dict:
    discovered = []
    route_items = []
    for name, base in nodes().items():
        node = {"name": name, "url": base, "reachable": False, "routes": [], "error": None}
        try:
            node["health"] = get_json(f"{base}/health")
            node["routes"] = get_json(f"{base}/routes").get("routes", [])
            node["reachable"] = True
        except Exception as exc:  # noqa: BLE001 - runtime reports offline nodes.
            node["error"] = str(exc)
        for route in node["routes"]:
            item = dict(route)
            item["node"] = name
            item["nodeUrl"] = base
            route_items.append(item)
        discovered.append(node)
    return {"nodes": discovered, "routes": route_items}


def registry_document() -> dict:
    mesh = discover()
    bindings = {}
    service_map = {}
    for node in mesh["nodes"]:
        if node.get("reachable"):
            service_map[node["name"]] = node["url"]
    for route in mesh["routes"]:
        uri = route["uri"]
        bindings[uri] = {
            "kind": "service",
            "adapter": "http-service",
            "inputSchema": route.get("inputSchema") or {"type": "object"},
            "meta": {
                "node": route.get("node"),
                "sourceAdapter": route.get("adapter"),
                "source": "registry-runtime",
            },
        }
    return {
        "version": "urirun.bindings.v2",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "serviceMap": service_map,
        "bindings": bindings,
    }


def send(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            mesh = discover()
            send(self, {"ok": True, "nodes": len(mesh["nodes"]), "routes": len(mesh["routes"])})
            return
        if self.path in {"/routes", "/routes.json"}:
            send(self, {"ok": True, **discover()})
            return
        if self.path in {"/registry", "/registry.json"}:
            send(self, registry_document())
            return
        send(self, {"ok": False, "error": "not found"}, status=404)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8120), Handler).serve_forever()
