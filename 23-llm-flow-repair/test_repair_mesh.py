# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline proof of the MESH path: discover a node's routes, let a fake LLM emit a
# flow, forward each step to the node over HTTP, and self-repair on failure.
# A tiny in-process HTTP server stands in for the remote `officepc` node.

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from urirun.node import mesh as meshlib

import repair_flow
import repair_flow_mesh

NODE_ROUTES = [
    {
        "uri": "demo://officepc/text/query/echo",
        "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}},
        "adapter": "local-function-subprocess",
        "safe": True,
    }
]

BAD = "steps:\n  - id: s\n    uri: other://officepc/x/query/y\n    payload: {}\n"   # not served -> fails
GOOD = "```yaml\nsteps:\n  - id: s\n    uri: demo://officepc/text/query/echo\n    payload: {text: hi}\n```"


class _FakeNode(BaseHTTPRequestHandler):
    seen: list = []

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send({"ok": True, "name": "officepc"})
        elif self.path == "/routes":
            self._send({"routes": NODE_ROUTES})
        elif self.path == "/mcp/tools":
            self._send({"tools": []})
        elif self.path == "/a2a/card":
            self._send({"skills": []})
        else:
            self._send({"ok": False}, 404)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        body = json.loads(self.rfile.read(length).decode() or "{}")
        if self.path == "/run":
            self.__class__.seen.append(body)
            text = (body.get("payload") or {}).get("text", "")
            # mimic the node executing an isolated handler: result under result.value
            self._send({"ok": True, "result": {"value": {"ok": True, "echo": text}}})
        else:
            self._send({"ok": False}, 404)

    def log_message(self, *_a):
        return


def _start_node():
    _FakeNode.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeNode)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _fake_llm():
    def ask(_reg, prompt, *, model, base_url):
        return GOOD if "FAILED" in prompt else BAD
    return ask


def test_mesh_generate_forward_repair():
    server, url = _start_node()
    old_map = os.environ.get("URI_SERVICE_MAP")
    try:
        config = {"nodes": [{"name": "officepc", "url": url}]}
        discovered = meshlib.discover_mesh(config)
        assert any(r["uri"] == "demo://officepc/text/query/echo" for r in discovered["routes"])
        registry = meshlib.registry_from_routes(discovered["routes"])
        os.environ["URI_SERVICE_MAP"] = json.dumps(discovered["serviceMap"])

        report = repair_flow.generate_run_repair(
            "echo hi on the node", registry, llm_registry={}, model="fake", base_url="fake",
            allow=["demo://*"], max_attempts=3, ask=_fake_llm(), runner=repair_flow_mesh.mesh_runner,
        )

        assert report["ok"] is True
        assert report["attempts"] == 2                      # bad route -> repaired
        assert report["results"]["s"] == {"ok": True, "echo": "hi"}   # came back from the node
        # the corrected step was actually forwarded to the node (POST /run)
        assert _FakeNode.seen and _FakeNode.seen[-1]["uri"] == "demo://officepc/text/query/echo"
        assert _FakeNode.seen[-1]["payload"] == {"text": "hi"}
    finally:
        server.shutdown()
        if old_map is None:
            os.environ.pop("URI_SERVICE_MAP", None)
        else:
            os.environ["URI_SERVICE_MAP"] = old_map
