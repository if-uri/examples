# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline: the desktop routes project to MCP tools with typed parameter schemas, and
# each tool maps back to a URI. Live (opt-in): the model drives the desktop by native
# tool-calling.
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
NOVNC = HERE.parent / "28-llm-novnc-desktop"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(NOVNC))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import mcp_agent  # noqa: E402
from novnc_connector import core as novnc  # noqa: E402
from urirun.runtime import v2_mcp  # noqa: E402


def test_routes_project_to_mcp_tools_with_typed_schema():
    registry = novnc.registry()
    tools, index = mcp_agent.mcp_tools_as_functions(registry)
    assert len(tools) == 6                                   # one tool per route
    # every tool carries a JSON-Schema 'parameters' object and maps to a real uri
    for t in tools:
        fn = t["function"]
        assert t["type"] == "function" and fn["name"] in index
        assert fn["parameters"].get("type") == "object"
    type_tool = next(t["function"] for t in tools if index[t["function"]["name"]].endswith("/input/command/type"))
    props = type_tool["parameters"]["properties"]
    assert props["text"]["type"] == "string" and props["enter"]["type"] == "boolean"


def test_tool_index_covers_every_route():
    registry = novnc.registry()
    index = v2_mcp.build_tool_index(registry)
    uris = set(index.values())
    assert "desktop://novnc/input/command/type" in uris
    assert "desktop://novnc/screen/query/screenshot" in uris


@pytest.mark.skipif(
    os.environ.get("URIRUN_NOVNC_LIVE") != "1" or shutil.which("docker") is None
    or not (os.environ.get("OPENROUTER_API_KEY") or Path("/home/tom/github/if-uri/urirun/.env").exists()),
    reason="set URIRUN_NOVNC_LIVE=1 with docker + an OpenRouter key to run the live MCP agent",
)
def test_live_mcp_agent_drives_desktop(tmp_path):
    env = {**os.environ,
           "PYTHONPATH": f"{HERE.parent.parent / 'urirun' / 'adapters' / 'python'}:{NOVNC}",
           "URIRUN_NOVNC_STATE": str(tmp_path / "s.json"),
           "URIRUN_NOVNC_SHOTS": str(tmp_path / "shots"),
           "GOAL": "open a terminal, run a command printing 'mcp ci ok', then screenshot, then stop."}
    result = subprocess.run([sys.executable, str(HERE / "mcp_agent.py")],
                            capture_output=True, text=True, env=env, timeout=450)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Intention realized: YES" in result.stdout
