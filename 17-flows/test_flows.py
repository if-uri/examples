# Author: Tom Sapletta · https://tom.sapletta.com
# Offline CI test for the flow runner (uses example 14's offline routes).
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_flow


def _ensure_tools_bindings():
    out = subprocess.run([sys.executable, str(HERE.parent / "14-llm-uri-agent" / "tools.py"), "bindings"],
                         capture_output=True, text=True, check=True)
    (HERE / "tools.bindings.json").write_text(out.stdout)


def test_local_flow_runs_offline():
    _ensure_tools_bindings()
    flow = run_flow.load(str(HERE / "local.flow.yaml"))
    result = run_flow.run_flow(flow, HERE, execute=True, allow=["time://*", "log://*"], secret_allow=[])
    assert result["ok"] is True
    assert [t["id"] for t in result["timeline"]] == ["stamp", "audit"]
    assert all(t["ok"] for t in result["timeline"])
    for junk in ("agent-run.log", "run.log"):
        (HERE / junk).unlink(missing_ok=True)


def test_command_step_is_gated_without_allow():
    _ensure_tools_bindings()
    flow = run_flow.load(str(HERE / "local.flow.yaml"))
    # allow only the query; the log COMMAND must be denied -> flow stops
    result = run_flow.run_flow(flow, HERE, execute=True, allow=["time://*"], secret_allow=[])
    assert result["ok"] is False
    assert result["timeline"][0]["ok"] is True       # stamp (query) ran
    assert result["timeline"][-1]["ok"] is False      # audit (command) denied


def test_all_yaml_flows_parse():
    for name in ("local.flow.yaml", "web-recon.flow.yaml", "ksef-send.flow.yaml"):
        flow = run_flow.load(str(HERE / name))
        assert flow["steps"] and all("uri" in s for s in flow["steps"])
        assert "registry" in flow
