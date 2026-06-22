# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Deterministic, offline checks: every office task plans ≥10 URI steps over the
# MCP tool surface, executes, and is VERIFIED against the resulting system state.

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run as office_run
from scenarios import SCENARIOS


def test_mcp_tool_surface_has_schemas():
    registry = office_run.load_registry()
    tools = office_run.mcp_tools(registry)
    assert len(tools) == 26
    schemes = {t["uri"].split("://")[0] for t in tools}
    assert {"app", "window", "browser", "email", "fs", "clipboard", "calendar", "screen", "notify"} <= schemes
    # required fields are part of the tool schema (what the LLM plans against)
    compose = next(t for t in tools if t["uri"] == "email://office/message/command/compose")
    assert set(compose["required"]) == {"to", "subject", "body"}


def test_six_scenarios_each_at_least_10_steps():
    assert len(SCENARIOS) == 6
    for scn in SCENARIOS:
        assert len(scn["steps"]) >= 10, f"{scn['id']} has only {len(scn['steps'])} steps"


def test_all_scenarios_execute_and_verify():
    registry = office_run.load_registry()
    for scn in SCENARIOS:
        r = office_run.run_scenario(scn, registry)
        assert r["all_ok"], f"{scn['id']}: only {r['executed']}/{r['steps']} steps ok"
        assert r["verified"], f"{scn['id']}: task not verified — {r['detail']}"
        assert r["steps"] >= 10


def test_runner_reports_all_done():
    rc = office_run.main([])
    assert rc == 0
