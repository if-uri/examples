# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline test of the run_live mechanism (minus the LLM): the stdlib uuid/hash/codec
# handlers from deployable_handlers.py, pushed as --code onto a node by the self-
# managing loop's provision step, actually serve and execute. No LLM, no remote node.

from __future__ import annotations

import socket
import sys
import threading
import time
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

import urirun
from urirun.node import mesh
from urirun.node.client import NodeClient

import deployable_handlers as dh
import governance
import self_managing

_INFO = "import json; print(json.dumps({'ok': True}))"


class DeployableHandlersTest(unittest.TestCase):
    def setUp(self):
        reg = urirun.compile_registry({"version": "urirun.bindings.v2",
            "bindings": urirun.tool_binding("sys://local/host/query/info", [sys.executable, "-c", _INFO], {})})
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        self.server = mesh.serve_node("local", reg, "127.0.0.1", self.port, execute=True,
                                      allow=["sys://**", "uuid://**", "hash://**", "codec://**"], admin_token="t")
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

    def _provision(self):
        def install_fn(client, candidate):
            spec = candidate["_spec"]
            res = mesh.deploy_to_node(client.base, bindings=spec["bindings"], code=spec["code"],
                                      allow=[f"{s}://**" for s in spec["schemes"]], merge=True, token="t")
            return bool(res.get("ok"))
        # The test itself is the standing ALLOW for this exact checkout. Keeping the
        # resolved path explicit makes it portable across local and GitHub runners.
        return governance.governed_provision(install_fn, allowlist=(str(HERE.resolve()),))

    def _resolver(self, scheme):
        spec = dh.for_scheme(scheme, "local")
        return [{"package": f"handler-{scheme}", "schemes": spec["schemes"], "_spec": spec,
                 "install": {"local": str(HERE)}}] if spec else []

    def _run(self, goal, step):
        out = self_managing.self_managing_loop(self.client, goal,
            planner=lambda g, r, e, o: {"steps": [step]}, resolver=self._resolver, provision=self._provision())
        self.assertTrue(out["ok"], out)
        return out["trace"][-1]["data"]

    def test_uuid_handler_provisions_and_runs(self):
        data = self._run("ids", {"id": "g", "uri": "uuid://local/id/query/v4", "payload": {"count": 3}})
        self.assertEqual(len(data["ids"]), 3)
        self.assertIn("uuid", self_managing.served_schemes(self.client))

    def test_hash_handler_provisions_and_runs(self):
        data = self._run("hash", {"id": "h", "uri": "hash://local/text/query/sha256", "payload": {"text": "ifuri"}})
        self.assertEqual(len(data["sha256"]), 64)

    def test_codec_handler_provisions_and_runs(self):
        data = self._run("b64", {"id": "c", "uri": "codec://local/text/query/base64", "payload": {"text": "lenovo"}})
        self.assertEqual(data["result"], "bGVub3Zv")   # base64('lenovo')


if __name__ == "__main__":
    unittest.main()
