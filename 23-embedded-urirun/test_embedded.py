# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

"""Verify the embedded URIRUN layer resolves zero-config (no connector, no registry).

Skips when the installed urirun predates the registry:// builtin (< 0.4.4).
"""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

URIRUN = [sys.executable, "-m", "urirun.v2"]


def _run(uri: str, allow: str, payload: str = "{}") -> dict:
    proc = subprocess.run(
        [*URIRUN, "run", uri, "--execute", "--allow", allow, "--payload", payload],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def _has_registry_builtin() -> bool:
    try:
        out = _run("registry://local/routes/query/list", "registry://*")
    except Exception:
        return False
    return bool(out.get("ok"))


pytestmark = pytest.mark.skipif(
    not _has_registry_builtin(),
    reason="needs urirun >= 0.4.4 (registry:// builtin + zero-config run)",
)


def test_registry_lists_routes_zero_config():
    out = _run("registry://local/routes/query/list", "registry://*")
    assert out["ok"] and out["result"]["count"] >= 1


def test_registry_self_describes_builtin_layer():
    out = _run("registry://local/routes/query/list", "registry://*")
    uris = {r["uri"] for r in out["result"]["routes"]}
    assert "registry://local/routes/query/list" in uris
    assert "error://local/errors/query" in uris


def test_registry_show_builtin_binding():
    out = _run("registry://local/bindings/query/show", "registry://*",
               '{"uri":"error://local/errors/query"}')
    assert out["result"]["binding"]["adapter"] == "error-store"
    assert out["result"]["binding"]["connector"] == "urirun-core"


def test_error_store_query_zero_config():
    out = _run("error://local/errors/query", "error://*")
    assert out["ok"] and out["result"]["type"] == "error-store"
