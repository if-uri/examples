# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
# Offline test: a fake WordPress REST endpoint; no real blog, no real credentials.

from __future__ import annotations

import base64
import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

import urirun
import wp_connector


class FakeWP(BaseHTTPRequestHandler):
    seen: dict = {}

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode() or "{}")
        FakeWP.seen = {"path": self.path, "auth": self.headers.get("Authorization"), "payload": payload}
        self._send(201, {"id": 42, "status": payload.get("status", "draft"),
                         "link": "http://blog.test/?p=42", "title": {"rendered": payload.get("title", "")}})

    def log_message(self, *_a):
        return


def _server():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeWP)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


class WordPressConnectorTest(unittest.TestCase):
    def test_missing_credentials_is_clean_error(self):
        for k in ("WP_URL", "WP_USER", "WP_APP_PASSWORD"):
            __import__("os").environ.pop(k, None)
        res = wp_connector.create_post(title="x", content="y")
        self.assertFalse(res["ok"])
        self.assertIn("Application Password", res["error"])

    def test_create_post_defaults_to_draft_with_app_password_auth(self, ):
        import os
        srv, url = _server()
        os.environ.update({"WP_URL": url, "WP_USER": "tom", "WP_APP_PASSWORD": "abcd efgh ijkl"})
        try:
            res = wp_connector.create_post(title="Hello", content="<p>Body</p>")
        finally:
            srv.shutdown()
        self.assertTrue(res["ok"])
        self.assertEqual(res["id"], 42)
        self.assertEqual(res["status"], "draft")                       # default: not published
        self.assertEqual(FakeWP.seen["path"], "/wp-json/wp/v2/posts")  # REST API, not wp-login
        self.assertEqual(FakeWP.seen["payload"]["status"], "draft")
        # Basic auth uses the app password by reference (never typed into a login form)
        user, pw = base64.b64decode(FakeWP.seen["auth"].split()[1]).decode().split(":")
        self.assertEqual(user, "tom")
        self.assertEqual(pw, "abcd efgh ijkl")

    def test_bindings_compile(self):
        doc = wp_connector.urirun_bindings()
        reg = urirun.compile_registry(doc)
        uris = {r["uri"] for r in urirun.list_routes(reg)}
        self.assertIn("wordpress://blog/post/command/create", uris)
        self.assertIn("wordpress://blog/post/query/list", uris)


if __name__ == "__main__":
    unittest.main()
