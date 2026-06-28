# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""The example must do two things: pass the honest flow, and CATCH the drift.

Plus: the in-process Python CONTRACTS and the neutral `contracts.json` (which drives the
JS/Go SDK guards) declare the SAME shape — one source of truth, any language."""
import json
import os

import pytest

import run as ex

HERE = os.path.dirname(os.path.abspath(__file__))


def test_honest_flow_conforms():
    assert ex.run(drift=False) == 0


def test_drift_is_caught_by_contract():
    # run(drift=True) returns 0 only because the contract CAUGHT the drift
    assert ex.run(drift=True) == 0


def test_contract_conforms_standalone():
    from urirun_contract import conform
    conform(ex.CONTRACTS)


def test_neutral_json_matches_inprocess_contracts():
    """contracts.json (for JS/Go guards) declares the same routes + out shape as the Python CONTRACTS."""
    doc = json.load(open(os.path.join(HERE, "contracts.json")))
    assert set(doc["contracts"]) == set(ex.CONTRACTS)
    for route, c in doc["contracts"].items():
        assert c["effect"] == ex.CONTRACTS[route].effect
        assert c["out"] == ex.CONTRACTS[route].out
