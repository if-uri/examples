#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Turns the reversibility analysis into a GUARANTEE: the contract's classification of the real
# scenarios is asserted, so a regression (a route mis-marked mutating/reversible, the surface
# principle broken) fails the build. Offline — no node, no network.
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import reversibility_check as rc
import run_scenarios as rs


def _scenario(name: str) -> dict:
    return rs._load_yaml(HERE / "scenarios" / f"{name}.yaml")


def test_read_only_commands_are_not_mutations():
    # a `/command/` is NOT automatically a mutation — fixed-arg reads must classify as read-only
    for suf in ("shell/command/date", "shell/command/uname", "shell/command/which"):
        mut, rev, _ = rc.classify(f"shell://host/{suf.split('/',1)[1]}", {}, "os")
        assert mut is False, f"{suf} is read-only, must not be a mutation"


def test_irreversible_boundary_is_blocked_on_both_surfaces():
    # the login SUBMIT (enter) is genuinely irreversible — blocked whatever the surface
    for surface in ("os", "cdp"):
        mut, rev, _ = rc.classify("kvm://host/input/command/key", {"keys": "enter"}, surface)
        assert mut is True and rev is False
    # proc kill and a blind pixel-coordinate write are irreversible too
    assert rc.classify("kvm://host/proc/command/kill", {"pid": 9}, "cdp")[:2] == (True, False)


def test_surface_principle_holds_on_web_login():
    # os-level blocks early (blind type); cdp reads state -> type becomes reversible -> the flow
    # gets all the way to the irreversible login submit before the invariant stops it.
    a_os = rc.analyse(_scenario("web-login"), "os")
    a_cdp = rc.analyse(_scenario("web-login"), "cdp")
    assert a_os["first_block"] == 2          # the email type, blind, has no inverse
    assert a_cdp["first_block"] == 5         # only the `enter` submit blocks under cdp
    assert a_cdp["reversible"] > a_os["reversible"]   # cdp makes strictly more reversible


def test_launch_and_capture_flows_are_fully_reversible():
    # open-a-page-and-screenshot scenarios mutate only via launch (⟂kill) -> fully undoable.
    # Found by shape, not name, so renames don't break the guarantee.
    fully = []
    for f in sorted((HERE / "scenarios").glob("*.yaml")):
        a = rc.analyse(rs._load_yaml(f), "os")
        forwards = [suf for _, suf, mut, _, _ in a["rows"] if mut]
        if a["mutations"] >= 1 and a["reversible"] == a["mutations"] and \
                any("desktop/command/launch" in s for s in forwards):
            fully.append(a["name"])
    assert len(fully) >= 2, f"expected ≥2 launch-only reversible flows, got {fully}"


def test_every_scenario_classifies_and_aggregate_counts():
    files = sorted((HERE / "scenarios").glob("*.yaml"))
    assert files
    fully_os = sum(1 for f in files
                   if (a := rc.analyse(rs._load_yaml(f), "os"))["mutations"]
                   and a["reversible"] == a["mutations"])
    fully_cdp = sum(1 for f in files
                    if (a := rc.analyse(rs._load_yaml(f), "cdp"))["mutations"]
                    and a["reversible"] == a["mutations"])
    # cdp never makes FEWER flows reversible than os (reading state only adds inverses)
    assert fully_cdp >= fully_os >= 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print("ok ", fn.__name__)
    print(f"\n{len(fns)} passed")


def test_scenario_drives_full_loop_goal_fail_then_compensate(monkeypatch):
    # The capstone: a real scenario YAML (verification.goal + rollbackOnFailure) runs the WHOLE
    # loop — all steps green, but the GOAL state is wrong (/login not /feed) -> verify fails ->
    # saga compensation unwinds the mutations LIFO over the connector's inverses.
    from urirun.node import flow as F

    doc = rs._load_yaml(HERE / "scenarios" / "reversible-web-draft.yaml")
    doc = __import__("json").loads(__import__("json").dumps(doc).replace("{host}", "laptop"))
    mesh = {"routes": [{"uri": "kvm://laptop/cdp/page/command/navigate"},
                       {"uri": "kvm://laptop/ui/command/fill"}], "serviceMap": {}, "nodes": [{"name": "laptop"}]}

    # steps ran green and each mutation returned its concrete inverse
    execution = {"ok": True,
        "timeline": [{"id": "nav", "uri": "kvm://laptop/cdp/page/command/navigate", "ok": True},
                     {"id": "fill", "uri": "kvm://laptop/ui/command/fill", "ok": True}],
        "results": {
            "nav": {"result": {"value": {"ok": True, "inverse": {"uri": "kvm://laptop/cdp/page/command/navigate", "args": {"url": "PREV"}}}}},
            "fill": {"result": {"value": {"ok": True, "inverse": {"uri": "kvm://laptop/ui/command/fill", "args": {"value": "OLD"}}}}},
        }}
    monkeypatch.setattr(F, "execute_flow", lambda *a, **k: execution)
    monkeypatch.setattr(F, "normalize_flow", lambda d, uris: {"steps": d.get("steps", [])})

    inverse_calls = []
    def fake_call(uri, payload, registry, mode="execute"):
        if "cdp/page/query/eval" in uri:                 # the GOAL probe -> we are on /login, NOT /feed
            return {"ok": True, "result": {"value": {"value": "https://www.linkedin.com/login/"}}}
        if "env/query/profile" in uri:                   # the scan route -> {state} for the re-scan proof
            return {"ok": True, "result": {"value": {"ok": True, "state": {"url": "https://…/login"}}}}
        inverse_calls.append(uri)                         # a rollback inverse
        return {"ok": True, "result": {"value": {"ok": True}}}
    monkeypatch.setattr(F.v2_service, "call", fake_call)

    result = F.run_flow_document(doc, mesh, execute=True)   # rollbackOnFailure comes from the doc
    assert result["ok"] is False                            # goal not reached -> flow fails honestly
    assert result["verification"]["ok"] is False
    assert result["compensation"]["ok"] is True             # the mutations were undone
    # both inverses fired (LIFO), the navigate and the fill — order may vary by rollback path
    assert set(inverse_calls) == {"kvm://laptop/cdp/page/command/navigate", "kvm://laptop/ui/command/fill"}
