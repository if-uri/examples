# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# END-TO-END proof of the whole self-managing trilogy with a REAL connector (not a
# stub): a local node serves only sys://; the loop is asked for the time; it
#   resolve()s  the 'time' scheme to urirun-connector-time-tools (real, from ~/github),
#   governs    the provision (trusted local source + connectors verify),
#   provisions it (serves the real time-tools bindings), re-discovers, and executes.

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

import governance
import resolver
import self_managing

_INFO = "import json; print(json.dumps({'ok': True, 'hostname': 'testhost'}))"


class E2ESelfManagingTest(unittest.TestCase):
    def setUp(self):
        reg = urirun.compile_registry({"version": "urirun.bindings.v2",
            "bindings": urirun.tool_binding("sys://local/host/query/info", [sys.executable, "-c", _INFO], {})})
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        self.server = mesh.serve_node("local", reg, "127.0.0.1", self.port, execute=True,
                                      allow=["sys://**", "time://**"], admin_token="t")
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

    def test_full_trilogy_real_connector(self):
        idx = resolver.index_local()
        hits = resolver.resolve("time", idx)
        if not hits or "time-tools" not in hits[0]["package"]:
            self.skipTest("urirun-connector-time-tools not found under ~/github")

        audit = []

        def install_fn(client, candidate):
            # the connector is importable in this venv; "serve" it by deploying its bindings
            import urirun_connector_time_tools as tt
            res = mesh.deploy_to_node(client.base, bindings=tt.urirun_bindings(),
                                      allow=["time://**"], merge=True, token="t")
            return bool(res.get("ok"))

        provision = governance.governed_provision(
            install_fn, verify_fn=governance.make_verify_fn(), audit=audit.append)

        # the time route the real connector serves
        def planner(goal, routes, prev_error, observation):
            return {"steps": [{"id": "t", "uri": "time://host/clock/query/now", "payload": {}}]}

        self.assertNotIn("time", self_managing.served_schemes(self.client))   # before: no time

        out = self_managing.self_managing_loop(self.client, "what time is it",
                                               planner, lambda s: resolver.resolve(s, idx), provision)

        self.assertTrue(out["ok"], out)
        self.assertEqual(out["provisioned"][0]["connector"], "urirun-connector-time-tools")
        self.assertIn("time", self_managing.served_schemes(self.client))       # surface self-extended
        # governance recorded a trusted install that passed verify
        self.assertTrue(any(a["ok"] and a["decision"] == "installed" for a in audit), audit)
        # and the goal actually executed: the time route ran
        last = out["trace"][-1]
        self.assertTrue(last["ok"] and last["uri"].startswith("time://"))


if __name__ == "__main__":
    unittest.main()
