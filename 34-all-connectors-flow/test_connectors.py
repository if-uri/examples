# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Every pip-installable connector imports, compiles into one registry, and either
# runs a representative route or is a valid config-gated route — driven by the
# generated YAML flows. Uses --no-install (the connectors are already editable) so
# the test is fast; the install flow itself is exercised by `make run`.

from __future__ import annotations

import io
import json
import contextlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import run as sweep
from connectors import CONNECTORS


def _report() -> dict:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sweep.main(["--no-install", "--json"])
    return json.loads(buf.getvalue())


def test_every_connector_imports_and_compiles():
    registry, present = sweep.merged_registry()
    assert all(present.values()), f"not importable: {[k for k, v in present.items() if not v]}"
    uris = {r["uri"] for r in __import__("urirun").action_space(registry)}
    assert "pkg://host/connector/command/install" in uris
    # a route from several different connectors is present in the merged registry
    assert "time://host/clock/query/now" in uris
    assert "fs://host/dir/query/list" in uris


def test_no_broken_connectors():
    rep = _report()
    broken = [r["connector"] for r in rep["smoke"] if not r["ok"]]
    assert not broken, f"broken connectors: {broken}"


def test_some_routes_actually_run():
    rep = _report()
    ran = [r["connector"] for r in rep["smoke"] if not r["gated"] and r["ok"]]
    assert len(ran) >= 6, f"only {len(ran)} connectors ran a route"


def test_generated_yaml_flows_cover_all_connectors():
    sweep.main(["--no-install", "--json"])  # regenerates flows/
    import yaml
    here = os.path.dirname(os.path.abspath(__file__))
    install = yaml.safe_load(open(os.path.join(here, "flows", "install.flow.yaml")))
    smoke = yaml.safe_load(open(os.path.join(here, "flows", "smoke.flow.yaml")))
    assert len(install["steps"]) == len(CONNECTORS)
    assert len(smoke["steps"]) == len(CONNECTORS)
    assert all(s["uri"] == "pkg://host/connector/command/install" for s in install["steps"])


def test_runner_exit_zero():
    assert sweep.main(["--no-install"]) == 0
