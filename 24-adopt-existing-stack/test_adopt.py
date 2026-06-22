# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Adopt existing multi-runtime code under one shop:// URI surface (zero rewrite).

Verifies the compiled registry runs each route across python/node/shell and
projects to MCP + A2A. Skips when urirun < 0.4.4 or node is missing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
URIRUN = [sys.executable, "-m", "urirun.v2"]
MCP = [sys.executable, "-m", "urirun.v2_mcp"]
REGISTRY = HERE / "shop.registry.json"


def _has(cmd) -> bool:
    return shutil.which(cmd) is not None


pytestmark = pytest.mark.skipif(not _has("node"), reason="node runtime required for the nodejs route")


@pytest.fixture(scope="module", autouse=True)
def registry():
    proc = subprocess.run([*URIRUN, "compile", str(HERE / "shop.bindings.json"), "--out", str(REGISTRY)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        pytest.skip(f"urirun compile failed (needs urirun>=0.4.4): {proc.stderr}")
    yield
    REGISTRY.unlink(missing_ok=True)


def _run(uri: str, payload: dict) -> dict:
    proc = subprocess.run(
        [*URIRUN, "run", uri, str(REGISTRY), "--execute", "--allow", "shop://*", "--payload", json.dumps(payload)],
        capture_output=True, text=True, cwd=HERE,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(json.loads(proc.stdout)["result"]["stdout"])


def test_python_route():
    assert _run("shop://inventory/stock/query/check", {"sku": "sku-1"})["available"] == 7


def test_python_reserve_route():
    out = _run("shop://inventory/stock/command/reserve", {"sku": "sku-1", "qty": 3})
    assert out["ok"] and out["remaining"] == 4


def test_node_route():
    assert _run("shop://notify/email/command/send", {"to": "a@b.com", "msg": "hi"})["sent"] is True


def test_shell_route():
    assert _run("shop://report/sales/query/daily", {"date": "2026-06-22"})["orders"] == 12


def test_mcp_projection():
    proc = subprocess.run([*MCP, "tools", str(REGISTRY)], capture_output=True, text=True)
    tools = json.loads(proc.stdout)["tools"]
    assert len(tools) == 4


def test_a2a_card_projection():
    proc = subprocess.run([*MCP, "card", str(REGISTRY), "--name", "shop", "--url", "http://gateway:8080/"],
                          capture_output=True, text=True)
    assert len(json.loads(proc.stdout)["skills"]) == 4
