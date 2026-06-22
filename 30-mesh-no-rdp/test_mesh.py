# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


@pytest.mark.skipif(shutil.which("jq") is None or shutil.which("curl") is None,
                    reason="needs jq + curl")
def test_controller_drives_nodes_without_rdp():
    r = subprocess.run(["bash", str(HERE / "mesh_local.sh")], capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, r.stderr + r.stdout
    out = r.stdout
    assert "node-a" in out and "node-b" in out                 # both nodes registered
    assert "Linux" in out                                       # a remote command ran and returned
    assert '"wrote":"hello from the controller"' in out         # a write dispatched to a node
    # the node refuses a command outside its exposed enum — least privilege, not RDP
    assert "is not one of" in out
