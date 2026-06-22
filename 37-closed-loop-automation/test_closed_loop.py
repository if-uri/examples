# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline CI test: a local urirun node + deterministic STUB planners exercise all
# three closed-loop patterns (self-repair, goal-verify, agent) and `_from` chaining —
# no LLM, no remote node.

from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

import urirun
from urirun.node import mesh
from urirun.node.client import NodeClient

import closed_loop

NOTES = Path(tempfile.gettempdir()) / "cl-test-notes.txt"

_WRITE = (f"import sys,pathlib; p=pathlib.Path({str(NOTES)!r}); "
          "p.open('a').write(sys.argv[1]+chr(10)); print('{\"ok\": true}')")
_READ = (f"import pathlib,json; p=pathlib.Path({str(NOTES)!r}); "
         "print(json.dumps({'ok': True, 'notes': p.read_text().splitlines() if p.exists() else []}))")
_WHICH = "import sys; print('/usr/bin/' + (sys.argv[1] if len(sys.argv) > 1 else ''), end='')"
_INFO = "import json; print(json.dumps({'ok': True, 'hostname': 'testhost', 'kernel': 'Linux-test'}))"


def _registry():
    py = sys.executable
    b = {}
    b.update(urirun.tool_binding("sys://local/host/query/info", [py, "-c", _INFO], {}))
    b.update(urirun.tool_binding("bin://local/which/query/path", [py, "-c", _WHICH, "{binary}"],
                                 {"binary": {"type": "string"}}, required=["binary"]))
    b.update(urirun.tool_binding("note://local/log/command/write", [py, "-c", _WRITE, "{text}"],
                                 {"text": {"type": "string"}}, required=["text"]))
    b.update(urirun.tool_binding("note://local/log/query/read", [py, "-c", _READ], {}))
    return urirun.compile_registry({"version": "urirun.bindings.v2", "bindings": b})


class ClosedLoopTest(unittest.TestCase):
    def setUp(self):
        if NOTES.exists():
            NOTES.unlink()
        s = socket.socket(); s.bind(("127.0.0.1", 0)); self.port = s.getsockname()[1]; s.close()
        self.server = mesh.serve_node("local", _registry(), "127.0.0.1", self.port,
                                      execute=True, allow=["sys://**", "bin://**", "note://**"])
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.port}"
        for _ in range(80):
            try:
                import urllib.request
                if urllib.request.urlopen(self.base + "/health", timeout=2).status == 200:
                    break
            except Exception:
                time.sleep(0.1)
        self.client = NodeClient(self.base)

    def tearDown(self):
        self.server.shutdown()

    def test_execute_flow_chains_from(self):
        # which python3 -> feed its stdout into a note via `_from`
        flow = {"steps": [
            {"id": "find", "uri": "bin://local/which/query/path", "payload": {"binary": "python3"}},
            {"id": "log", "uri": "note://local/log/command/write",
             "payload": {"text_from": "find.result.stdout"}},
        ]}
        out = closed_loop.execute_flow(self.client, flow)
        self.assertTrue(out["ok"])
        notes = urirun.result_data(self.client.run("note://local/log/query/read"))["notes"]
        self.assertEqual(notes, ["/usr/bin/python3"])   # the REAL path, resolved — not a literal

    def test_self_repair_loop(self):
        # iteration 1 uses a wrong field (message) -> node schema error -> repaired to text
        calls = {"n": 0}

        def stub_planner(goal, routes, prev_error, observation):
            calls["n"] += 1
            field = "message" if prev_error is None else "text"   # repair after the node's error
            return {"steps": [{"id": "w", "uri": "note://local/log/command/write",
                               "payload": {field: "repaired note"}}]}

        out = closed_loop.self_repair_loop(self.client, "log a note", stub_planner)
        self.assertTrue(out["ok"])
        self.assertEqual(out["iterations"], 2)              # failed once, fixed on retry
        self.assertEqual(calls["n"], 2)

    def test_goal_verify_loop(self):
        # goal: have >= 2 notes. planner writes one per iteration; verify counts them.
        def stub_planner(goal, routes, prev_error, observation):
            n = (observation or {}).get("observed", {}).get("count", 0)
            return {"steps": [{"id": "w", "uri": "note://local/log/command/write",
                               "payload": {"text": f"note-{n}"}}]}

        def verify(client):
            notes = urirun.result_data(client.run("note://local/log/query/read"))["notes"]
            return (len(notes) >= 2, {"count": len(notes)})

        out = closed_loop.goal_verify_loop(self.client, "have two notes", stub_planner, verify)
        self.assertTrue(out["ok"])
        self.assertEqual(out["iterations"], 2)

    def test_agent_loop(self):
        # observe -> act -> repeat: read info, log it, then declare done.
        def decide(goal, routes, transcript):
            done_after = 2
            if len(transcript) >= done_after:
                return {"done": True, "reason": "info captured and logged"}
            if not transcript:
                return {"uri": "sys://local/host/query/info", "payload": {}}
            return {"uri": "note://local/log/command/write", "payload": {"text": "host audited"}}

        out = closed_loop.agent_loop(self.client, "audit and log", decide)
        self.assertTrue(out["ok"])
        self.assertEqual(out["steps"], 2)
        self.assertTrue(all(t["ok"] for t in out["transcript"]))

    def test_heuristic_planner_offline(self):
        # the no-LLM planner produces a runnable flow for a keyword goal
        from planners import heuristic_planner
        flow = heuristic_planner("show host info", self.client.routes(), None, None)
        self.assertIsInstance(flow.get("steps"), list)


if __name__ == "__main__":
    unittest.main()
