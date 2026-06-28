#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import host_node_matrix as hnm


def test_route_key_ignores_target_name():
    assert hnm._route_key("kvm://host/screen/query/capture") == hnm._route_key(
        "kvm://lenovo/screen/query/capture"
    )


def test_degraded_capture_is_not_a_pass():
    step = hnm.Step("capture", "kvm://host/screen/query/capture", expect="non_degraded_capture")
    env = {"ok": True}
    value = {
        "ok": True,
        "degraded": True,
        "degradedReason": "xdg-portal returned a placeholder",
        "bytes": 3848,
    }
    status, reason = hnm._verdict(step, env, value)
    assert status == "degraded"
    assert "degraded" in reason


def test_small_capture_is_degraded_even_without_flag():
    step = hnm.Step("capture", "kvm://host/screen/query/capture", expect="non_degraded_capture")
    status, reason = hnm._verdict(step, {"ok": True}, {"ok": True, "bytes": 3848, "path": "/tmp/x.png"})
    assert status == "degraded"
    assert "too small" in reason
