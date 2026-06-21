# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline-safe checks for the LLM-over-URI agent loop. Network/Chrome-dependent
# routes are only asserted to be *attempted*; the time:// route runs offline.

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent


def test_action_space_lists_routes_with_kinds():
    registry = agent.load_registry()
    space = agent.action_space(registry)
    uris = {r["uri"]: r for r in space}
    assert "time://host/clock/query/now" in uris
    assert uris["time://host/clock/query/now"]["kind"] == "query"
    assert uris["log://host/run/command/write"]["kind"] == "command"


def test_plan_produces_steps_for_a_goal():
    registry = agent.load_registry()
    steps = agent.plan("read https://example.com", agent.action_space(registry))
    assert steps, "planner returned no steps"
    assert steps[-1]["uri"] == "log://host/run/command/write"
    assert all("uri" in s and "payload" in s for s in steps)


def test_query_route_runs_offline():
    registry = agent.load_registry()
    out = agent.run_step(registry, {"uri": "time://host/clock/query/now", "payload": {}}, allow_commands=False)
    assert out["ran"] is True
    assert out["ok"] is True
    assert "utc" in out["data"]


def test_command_is_gated_without_permission():
    registry = agent.load_registry()
    out = agent.run_step(registry, {"uri": "log://host/run/command/write", "payload": {"event": "x"}}, allow_commands=False)
    assert out["ran"] is False
    out2 = agent.run_step(registry, {"uri": "log://host/run/command/write", "payload": {"event": "x"}}, allow_commands=True)
    assert out2["ran"] is True and out2["ok"] is True
    os.path.exists(os.path.join(os.path.dirname(agent.__file__), "agent-run.log")) and os.remove(
        os.path.join(os.path.dirname(agent.__file__), "agent-run.log")
    )
