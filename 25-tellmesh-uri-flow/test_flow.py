# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Verifies the kvm -> ocr -> llm URI flow actually works in action: real execution,
# real data threaded between steps, and policy gating around the whole chain.
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "packs"))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import flow  # noqa: E402
from urirun import v2  # noqa: E402
from urirun.runtime import _runtime as runtime  # noqa: E402


def test_registry_carries_all_three_schemes():
    reg = flow.build_registry()
    schemes = {r["uri"].split("://", 1)[0] for r in v2.list_routes(reg, None)}
    assert schemes == {"kvm", "ocr", "llm"}


def test_flow_threads_output_into_next_input():
    reg = flow.build_registry()
    steps = flow.run_flow(reg, host="host1", monitor=0)
    cap, ocr, llm = (s["out"] for s in steps)
    # step 2 consumed step 1's image_id
    assert ocr["image_id"] == cap["image_id"] == "shot-mon0"
    # step 2's text reached step 3, and step 3 summarized it
    assert "42.00" in ocr["text"]
    assert llm["summary"] == "Invoice for 42.00 USD, due 2026-07-01."


def test_flow_branches_on_a_different_capture():
    # a different monitor -> different scanned text -> different summary, all via the
    # same three URIs (proves the data really flows, not a hard-coded result).
    reg = flow.build_registry()
    steps = flow.run_flow(reg, host="host1", monitor=1)
    ocr, llm = steps[1]["out"], steps[2]["out"]
    assert "2026-08-15" in ocr["text"]
    assert llm["summary"] == "Action due 2026-08-15."


def test_flow_is_policy_gated():
    # the flow policy only allows kvm/ocr/llm; a step outside that set is denied,
    # so the chain can't be made to call something it wasn't authorized to.
    reg = flow.build_registry()
    policy = runtime.build_policy(None, ["ocr://**", "llm://**"], None)  # note: no kvm
    env = v2.run("kvm://host1/monitor/command/capture", reg, payload={"monitor": 0},
                 mode="execute", policy=policy)
    assert env["ok"] is False
    assert env["decision"]["allowed"] is False


def test_cli_flow_runs_end_to_end():
    # the same chain driven purely by `urirun run` from bash (no Python runner),
    # proving adopted routes EXECUTE from a file registry via the CLI.
    if shutil.which("jq") is None:
        pytest.skip("jq not available")
    result = subprocess.run(["bash", str(HERE / "flow_cli.sh")], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "threaded correctly via the CLI: ok" in result.stdout


def test_node_flow_runs_over_http():
    # the same chain over a network transport: served by `urirun node serve`, each
    # step a POST /run. Proves the URIs interoperate remotely, not just in-process.
    if shutil.which("jq") is None or shutil.which("curl") is None:
        pytest.skip("jq/curl not available")
    result = subprocess.run(["bash", str(HERE / "flow_node.sh")],
                            capture_output=True, text=True, timeout=180)
    assert result.returncode == 0, result.stderr + result.stdout
    assert "threaded correctly over HTTP: ok" in result.stdout
