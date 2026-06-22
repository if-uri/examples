#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline test: parse the YAML scenarios, thread $ref, and run a scenario against a fake
# node (no network) — proving the runner end-to-end without a live mesh.

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_scenarios as rs


def test_every_scenario_file_parses():
    files = sorted((HERE / "scenarios").glob("*.yaml"))
    assert files, "no scenario files"
    for f in files:
        doc = rs._load_yaml(f)
        assert doc.get("name") and isinstance(doc.get("steps"), list) and doc["steps"]
        for step in doc["steps"]:
            assert "uri" in step


def test_concretize_substitutes_placeholders():
    n = rs.Node.__new__(rs.Node)
    n.name = "lab"
    assert n.concretize("him://{host}/keyboard/command/type-text") == "him://lab/keyboard/command/type-text"
    assert n.concretize("kvm://%7Bhost%7D/monitor/%7Bmonitor%7D/query/screenshot") == \
        "kvm://lab/monitor/0/query/screenshot"


def test_ref_threading_and_value_unwrap():
    assert rs._resolve_refs({"id": "$ref:0.image_id"}, [{"image_id": "shot-0"}]) == {"id": "shot-0"}
    assert rs._value({"ok": True, "result": {"value": {"a": 1}}}) == {"a": 1}
    assert rs._value({"ok": True, "result": {"stdout": '{"b": 2}'}}) == {"b": 2}


def test_run_scenario_against_a_fake_node():
    n = rs.Node.__new__(rs.Node)
    n.name = "lab"
    calls = []

    def fake_run(uri, payload):
        calls.append((uri, payload))
        if uri.endswith("/page/command/open"):
            return {"ok": True, "result": {"value": {"url": payload.get("url"), "title": "Mock"}}}
        if "type-text" in uri:
            return {"ok": True, "result": {"value": {"typed": payload.get("text")}}}
        return {"ok": True, "result": {"value": {"done": True}}}

    n.run = fake_run
    scenario = rs._load_yaml(HERE / "scenarios" / "web-login.yaml")
    report = rs.run_scenario(n, scenario)
    assert report["total"] == len(scenario["steps"])
    assert report["ok"] == report["total"]          # fake node accepts every step
    assert calls[0][0] == "browser://lab/page/command/open"  # placeholder resolved, order kept


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print("ok ", fn.__name__)
    print(f"\n{len(fns)} passed")
