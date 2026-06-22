#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline end-to-end test of the host agent: a FAKE node (in-memory, no network, no
# tellmesh) serves an office action space, and the heuristic planner drives it. Proves
# the loop — concretize, plan, $ref threading, dispatch, value-unwrap, both-sides log —
# without an API key, a live node, or Docker.

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import office_agent as oa

# force the offline heuristic planner regardless of the developer's environment
os.environ.pop("OPENROUTER_API_KEY", None)
os.environ.pop("LLM_MODEL", None)
os.environ.pop("URIRUN_OFFICE_MODEL", None)


class FakeNode:
    """Mimic a served office node: /routes (percent-encoded braces, like the real one),
    /run for a few handlers, and a persistent log so we can read it back."""

    name = "lenovo"
    ROUTES = [
        {"uri": "browser://%7Bsession%7D/page/open", "kind": "command",
         "title": "browser open", "inputSchema": {"properties": {"url": {"type": "string"}}}},
        {"uri": "him://%7Bhost%7D/keyboard/command/type-text", "kind": "command",
         "title": "type text", "inputSchema": {"properties": {"text": {"type": "string"}}}},
        {"uri": "kvm://%7Bhost%7D/monitor/%7Bmonitor%7D/query/screenshot", "kind": "query",
         "title": "screenshot", "inputSchema": {"properties": {}}},
        {"uri": "log://lenovo/session/command/write", "kind": "command", "title": "log write",
         "inputSchema": {"properties": {"text": {"type": "string"}}}},
        {"uri": "log://lenovo/session/query/recent", "kind": "command", "title": "log read",
         "inputSchema": {"properties": {"limit": {"type": "integer"}}}},
    ]

    def __init__(self) -> None:
        self.log_lines: list[str] = []

    # the bits office_agent.Node would do over HTTP, served from memory instead
    concretize = oa.Node.concretize
    action_space = oa.Node.action_space

    def run(self, uri: str, payload: dict) -> dict:
        import json
        if uri.startswith("browser://") and uri.endswith("/page/open"):
            return {"ok": True, "result": {"value": {"url": payload.get("url"), "title": "Mock page"}}}
        if "keyboard/command/type-text" in uri:
            return {"ok": True, "result": {"value": {"typed": payload.get("text"), "driver": "mock"}}}
        if "query/screenshot" in uri:
            return {"ok": True, "result": {"value": {"image_id": "shot-0", "monitor": 0}}}
        if uri.endswith("/session/command/write"):
            self.log_lines.append(json.dumps({"text": payload["text"]}))
            return {"ok": True, "result": {"value": {"wrote": payload["text"]}}}
        if uri.endswith("/session/query/recent"):
            return {"ok": True, "result": {"stdout": json.dumps({"logs": self.log_lines})}}
        return {"ok": False, "error": f"no fake handler for {uri}"}

    def log(self, text: str) -> None:
        self.run(f"log://{self.name}/session/command/write", {"text": text})

    recent_log = oa.Node.recent_log

    @property
    def routes(self) -> list[dict]:
        return self.ROUTES


def test_concretize_handles_percent_encoded_placeholders():
    n = FakeNode()
    assert n.concretize("kvm://%7Bhost%7D/monitor/%7Bmonitor%7D/query/screenshot") == \
        "kvm://lenovo/monitor/0/query/screenshot"
    assert n.concretize("browser://%7Bsession%7D/page/open") == "browser://lenovo/page/open"


def test_value_unwrap_both_shapes():
    assert oa._value({"result": {"value": {"a": 1}}}) == {"a": 1}
    assert oa._value({"result": {"stdout": '{"b": 2}'}}) == {"b": 2}


def test_ref_threading():
    out = oa.resolve_refs({"image_id": "$ref:0.image_id", "n": 5}, [{"image_id": "shot-0"}])
    assert out == {"image_id": "shot-0", "n": 5}


def test_heuristic_plan_covers_office_verbs():
    n = FakeNode()
    space = n.action_space()
    plan = oa.heuristic_plan(
        "open https://example.com and type 'Faktura 07/2026', then screenshot", space)
    uris = [s["uri"] for s in plan]
    assert any(u.startswith("browser://lenovo/page/open") for u in uris)
    assert any("keyboard/command/type-text" in u for u in uris)
    assert any("query/screenshot" in u for u in uris)


def test_end_to_end_loop_logs_both_sides():
    """Drive the fake node through the agent's dispatch loop and confirm the node's own
    log captured the delegated task + every step (the 'both sides see it' guarantee)."""
    n = FakeNode()
    space = n.action_space()
    plan = oa.heuristic_plan("open https://example.com and type 'hello', then screenshot", space)

    n.log(f"[host] new task ({len(plan)} steps)")
    results: list[dict] = []
    for i, step in enumerate(plan):
        uri = n.concretize(step["uri"])
        payload = oa.resolve_refs(step.get("payload", {}), [r["_value"] for r in results])
        n.log(f"[host->node] step {i}: {uri}")
        env = n.run(uri, payload)
        val = oa._value(env)
        results.append({"_value": val})
        n.log(f"[node] step {i} ok: {val}")

    tail = n.recent_log(limit=50)
    joined = " ".join(tail)
    assert "[host] new task" in joined
    assert "[host->node] step 0" in joined
    assert "[node] step 0 ok" in joined
    assert sum(1 for l in tail if "[host->node]" in l) == len(plan)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
