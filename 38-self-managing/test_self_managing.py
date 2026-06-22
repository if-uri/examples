# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline CI proof of the self-managing loop: a node starts WITHOUT a needed
# capability; the loop detects the gap, "provisions" the connector (here a stub that
# deploys its bindings, standing in for an install), re-discovers the surface, and
# completes — no LLM, no remote node.

from __future__ import annotations

import json
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "37-closed-loop-automation"))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

import urirun
from urirun.node import mesh
from urirun.node.client import NodeClient

import self_managing

NOTES = Path(tempfile.gettempdir()) / "cl-selfmanage-notes.txt"
_WRITE = (f"import sys,pathlib; p=pathlib.Path({str(NOTES)!r}); "
          "p.open('a').write(sys.argv[1]+chr(10)); print('{\"ok\": true}')")
_INFO = "import json; print(json.dumps({'ok': True, 'hostname': 'testhost'}))"


def _note_bindings():
    py = sys.executable
    b = urirun.tool_binding("note://local/log/command/write", [py, "-c", _WRITE, "{text}"],
                            {"text": {"type": "string"}}, required=["text"])
    return {"version": "urirun.bindings.v2", "bindings": b}


class SelfManagingTest(unittest.TestCase):
    def setUp(self):
        if NOTES.exists():
            NOTES.unlink()
        # node starts serving ONLY sys:// — note:// is missing on purpose
        reg = urirun.compile_registry({"version": "urirun.bindings.v2",
            "bindings": urirun.tool_binding("sys://local/host/query/info", [sys.executable, "-c", _INFO], {})})
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        self.server = mesh.serve_node("local", reg, "127.0.0.1", self.port, execute=True,
                                      allow=["sys://**", "note://**"], admin_token="t")
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.port}"
        for _ in range(80):
            try:
                if urllib.request.urlopen(self.base + "/health", timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(0.1)
        self.client = NodeClient(self.base)

    def tearDown(self):
        self.server.shutdown()

    def test_loop_provisions_missing_capability_then_completes(self):
        # planner always wants to write a note (note:// is not served at first)
        def planner(goal, routes, prev_error, observation):
            return {"steps": [{"id": "w", "uri": "note://local/log/command/write",
                               "payload": {"text": "self-managed"}}]}

        # resolver maps the 'note' scheme to a connector candidate (with its bindings)
        def resolver(scheme):
            if scheme != "note":
                return []
            return [{"package": "urirun-connector-note", "schemes": ["note"],
                     "source": "stub", "install": {"local": "/stub/note"}}]

        # provision stands in for "install + serve": deploy the note bindings (--merge)
        provisioned_calls = {"n": 0}

        def provision(client, candidate):
            provisioned_calls["n"] += 1
            res = mesh.deploy_to_node(client.base, bindings=_note_bindings(),
                                      allow=["note://**"], merge=True, token="t")
            return bool(res.get("ok"))

        # before: note:// is NOT served
        self.assertNotIn("note", self_managing.served_schemes(self.client))

        out = self_managing.self_managing_loop(self.client, "write a note", planner, resolver, provision)

        self.assertTrue(out["ok"], out)
        self.assertEqual(provisioned_calls["n"], 1)                       # installed exactly once
        self.assertEqual(out["provisioned"][0]["scheme"], "note")
        self.assertIn("note", self_managing.served_schemes(self.client))  # surface self-extended
        self.assertIn("self-managed", NOTES.read_text())                  # and the goal was achieved

    def test_loop_reports_unresolvable_capability(self):
        def planner(goal, routes, prev_error, observation):
            return {"steps": [{"id": "x", "uri": "exotic://local/thing/query/y", "payload": {}}]}

        out = self_managing.self_managing_loop(self.client, "do exotic thing", planner,
                                               resolver=lambda s: [], provision=lambda c, k: True)
        self.assertFalse(out["ok"])
        self.assertIn("exotic", out["reason"])


if __name__ == "__main__":
    unittest.main()
