# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Deterministic, offline checks. Every VM-office task plans a multi-step URI flow
# over the MCP tool surface, executes it, and is VERIFIED against the resulting
# system state — including teardown (no dangling RDP sessions / noVNC views). A
# second block exercises the BEHAVIOUR directly: connecting to a powered-off VM is
# rejected, disconnect/stop close the dependent artefacts, and the RDP clipboard is
# shared across sessions. The live noVNC desktop run is opt-in (URIRUN_NOVNC_LIVE=1).

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run as vm_run  # noqa: E402
import vm_office_system as vos_sim  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402


# -- helpers to call a route op directly against a fresh state ---------------

def _fresh():
    return {"vms": {n: {**m, "power": "off", "files": {}} for n, m in vos_sim.FLEET.items()},
            "sessions": {}, "views": {}, "clipboard": "", "screenshots": [],
            "ocr_log": [], "notifications": [], "_seq": {}}


def _call(state, op, **kw):
    ns = argparse.Namespace(**{k: "" for k in
        ("vm", "user", "session", "view", "app", "text", "keys", "image", "path", "content", "message")})
    for k, v in kw.items():
        setattr(ns, k, v)
    return vos_sim.OPS[op](state, ns)


# -- the MCP tool surface ----------------------------------------------------

def test_mcp_tool_surface_has_schemas():
    registry = vm_run.load_registry()
    tools = vm_run.mcp_tools(registry)
    assert len(tools) == 20
    schemes = {t["uri"].split("://")[0] for t in tools}
    assert {"vm", "rdp", "novnc", "desktop", "fs", "clipboard", "screen", "notify"} <= schemes
    connect = next(t for t in tools if t["uri"] == "rdp://gateway/session/command/connect")
    assert set(connect["required"]) == {"vm"}
    launch = next(t for t in tools if t["uri"] == "desktop://vm/app/command/launch")
    assert set(launch["required"]) == {"session", "app"}


def test_six_scenarios_each_at_least_10_steps():
    assert len(SCENARIOS) == 6
    for scn in SCENARIOS:
        assert len(scn["steps"]) >= 10, f"{scn['id']} has only {len(scn['steps'])} steps"


def test_all_scenarios_execute_and_verify():
    registry = vm_run.load_registry()
    for scn in SCENARIOS:
        r = vm_run.run_scenario(scn, registry)
        assert r["all_ok"], f"{scn['id']}: only {r['executed']}/{r['steps']} steps ok — {r['trace']}"
        assert r["verified"], f"{scn['id']}: task not verified — {r['detail']}"
        assert r["steps"] >= 10


def test_runner_reports_all_done():
    assert vm_run.main([]) == 0


# -- behaviour: the flow must behave correctly, not just run -----------------

def test_connect_to_powered_off_vm_is_rejected():
    s = _fresh()
    res = _call(s, "rdp-connect", vm="win11-finance", user="x")  # never started
    assert res["ok"] is False
    assert "powered off" in res["error"]
    assert s["sessions"] == {}


def test_novnc_view_requires_an_rdp_session():
    s = _fresh()
    res = _call(s, "novnc-open", session="s1")  # no session exists
    assert res["ok"] is False
    assert s["views"] == {}


def test_disconnect_closes_the_dependent_novnc_views():
    s = _fresh()
    _call(s, "vm-start", vm="win-sales")
    sid = _call(s, "rdp-connect", vm="win-sales")["session"]
    vid = _call(s, "novnc-open", session=sid)["view"]
    assert s["views"][vid]["session"] == sid
    out = _call(s, "rdp-disconnect", session=sid)
    assert out["viewsClosed"] == 1
    assert s["sessions"] == {} and s["views"] == {}        # nothing dangling


def test_powering_off_a_vm_tears_down_its_sessions():
    s = _fresh()
    _call(s, "vm-start", vm="ubuntu-dev")
    sid = _call(s, "rdp-connect", vm="ubuntu-dev")["session"]
    _call(s, "novnc-open", session=sid)
    out = _call(s, "vm-stop", vm="ubuntu-dev")
    assert out["sessionsClosed"] == 1
    assert s["sessions"] == {} and s["views"] == {}
    assert s["vms"]["ubuntu-dev"]["power"] == "off"


def test_rdp_clipboard_is_shared_across_sessions():
    s = _fresh()
    for vm in ("win11-finance", "win-sales"):
        _call(s, "vm-start", vm=vm)
    s1 = _call(s, "rdp-connect", vm="win11-finance")["session"]
    s2 = _call(s, "rdp-connect", vm="win-sales")["session"]
    _call(s, "clipboard-set", text="1 480 000")
    assert _call(s, "clipboard-get")["text"] == "1 480 000"   # set on s1's gateway, read for s2
    assert s1 != s2


def test_files_persist_on_the_vm_across_reconnects():
    s = _fresh()
    _call(s, "vm-start", vm="win11-finance")
    s1 = _call(s, "rdp-connect", vm="win11-finance")["session"]
    _call(s, "fs-save", session=s1, path="a.txt", content="hello")
    _call(s, "rdp-disconnect", session=s1)
    s2 = _call(s, "rdp-connect", vm="win11-finance")["session"]   # reconnect
    assert _call(s, "fs-read", session=s2, path="a.txt")["content"] == "hello"


@pytest.mark.skipif(os.environ.get("URIRUN_NOVNC_LIVE") != "1" or shutil.which("docker") is None,
                    reason="set URIRUN_NOVNC_LIVE=1 (and have docker) to drive a real noVNC desktop")
def test_live_finance_on_real_novnc_desktop():
    result = subprocess.run([sys.executable, os.path.join(HERE, "run.py"), "--live"],
                            capture_output=True, text=True, timeout=420)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout
