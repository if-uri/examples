# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The agent discovers routes from the action space, composes a capture->ocr->llm
# plan with $ref threading, and runs it under policy. Self-contained (reuses the
# example-25 flow packs).
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PACKS = HERE.parent / "25-tellmesh-uri-flow" / "packs"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(PACKS))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import planner  # noqa: E402
from urirun import v2  # noqa: E402
from urirun.runtime import adopt_pack, agent  # noqa: E402


def _registry() -> dict:
    bindings: dict[str, dict] = {}
    for name in ("flow_kvm", "flow_ocr", "flow_llm"):
        for uri, b in adopt_pack.adopt(str(PACKS / name / "manifest.yaml"))["bindings"].items():
            bindings[uri] = b
    return v2.compile_registry({"version": "urirun.bindings.v2", "bindings": bindings})


def test_planner_composes_chain_from_action_space():
    space = agent.action_space(_registry())
    steps = planner.plan("capture the screen, read its text, and summarize it", space)
    uris = [s["uri"].split("://", 1)[0] for s in steps]
    assert uris == ["kvm", "ocr", "llm"]                       # discovered, in order
    # the chain is threaded: step 2 refs step 0's image_id, step 3 refs step 1's text
    assert steps[1]["payload"]["image_id"] == "$ref:0.image_id"
    assert steps[2]["payload"]["prompt"] == "$ref:1.text"


def test_agent_runs_the_composed_plan_under_policy():
    registry = _registry()
    space = agent.action_space(registry)
    steps = planner.plan("capture, ocr, summarize", space)
    trace = agent.run_plan(registry, steps, allow=["kvm://**", "ocr://**", "llm://**"],
                           allow_commands=True)
    # data really flowed: the OCR step received the capture's image_id, the summary
    # was derived from the OCR text.
    assert trace[1]["payload"]["image_id"] == "shot-mon0"
    assert "42.00" in trace[2]["data"]["summary"]
    assert all(s["ok"] for s in trace)


def test_agent_command_via_cli():
    if shutil.which("jq") is None:
        pytest.skip("jq not available")
    result = subprocess.run(["bash", str(HERE / "agent_flow.sh")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "composed kvm->ocr->llm from the action space and ran it: ok" in result.stdout
