# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Fast offline checks: the action space carries real typed schemas, and the
# schema-aware planner fills parameters per those schemas. The live desktop run is
# opt-in (URIRUN_NOVNC_LIVE=1) because it boots a Docker container.
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import schema_planner  # noqa: E402
from novnc_connector import core as novnc  # noqa: E402
from urirun.runtime import agent  # noqa: E402


def test_action_space_exposes_typed_schemas():
    space = {r["uri"]: r for r in agent.action_space(novnc.registry())}
    typ = space["desktop://novnc/input/command/type"]
    props = typ["schema"]["properties"]
    assert props["text"]["type"] == "string"          # the LLM sees the type
    assert props["enter"]["type"] == "boolean"
    assert typ["required"] == ["text"]                 # ...and what's required


def test_schema_planner_fills_params_from_nl_offline(monkeypatch):
    monkeypatch.setenv("URIRUN_ENV", "/nonexistent")   # force the offline heuristic
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    space = agent.action_space(novnc.registry())
    steps = schema_planner.plan("open a terminal and type 'hello world', then screenshot", space)
    type_step = next(s for s in steps if s["uri"].endswith("/input/command/type"))
    assert "hello world" in type_step["payload"]["text"]      # param filled from the NL intent
    assert type_step["payload"]["enter"] is True
    # only real uris, ordered start ... stop
    uris = {r["uri"] for r in space}
    assert all(s["uri"] in uris for s in steps)
    assert steps[0]["uri"].endswith("/session/command/start")
    assert steps[-1]["uri"].endswith("/session/command/stop")


@pytest.mark.skipif(os.environ.get("URIRUN_NOVNC_LIVE") != "1" or shutil.which("docker") is None,
                    reason="set URIRUN_NOVNC_LIVE=1 (and have docker) to run the live desktop session")
def test_live_desktop_session_realizes_intent(tmp_path):
    env = {**os.environ,
           "PYTHONPATH": f"{HERE.parent.parent / 'urirun' / 'adapters' / 'python'}:{HERE}",
           "URIRUN_NOVNC_STATE": str(tmp_path / "s.json"),
           "URIRUN_NOVNC_SHOTS": str(tmp_path / "shots"),
           "GOAL": "Open a terminal and run a command printing 'urirun ci check', then screenshot."}
    result = subprocess.run([sys.executable, str(HERE / "run_session.py")],
                            capture_output=True, text=True, env=env, timeout=420)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Verdict: YES" in result.stdout
