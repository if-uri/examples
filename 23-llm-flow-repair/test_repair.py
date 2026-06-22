# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline proof of the generate -> run -> repair loop with a fake LLM:
# the first reply is a broken flow (unknown route), the second — after the error
# is fed back — is a valid flow. No network, no real model.

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import urirun
import urirun_connector_time_tools.core as tt
import repair_flow

BAD = "steps:\n  - id: t\n    uri: nosuch://host/a/query/b\n    payload: {}\n"
GOOD = "```yaml\nsteps:\n  - id: t\n    uri: time://host/clock/query/now\n    payload: {output: iso}\n```"


def _fake_llm_factory():
    """First call -> broken flow; once the error is fed back -> corrected flow."""
    calls = {"n": 0}

    def ask(_llm_registry, prompt, *, model, base_url):
        calls["n"] += 1
        return GOOD if "FAILED" in prompt else BAD

    return ask, calls


def test_generate_run_repair_recovers():
    registry = tt.conn.registry()
    ask, calls = _fake_llm_factory()
    report = repair_flow.generate_run_repair(
        "get the current time", registry, llm_registry={}, model="fake", base_url="fake",
        allow=["time://*"], max_attempts=3, ask=ask,
    )
    assert report["ok"] is True
    assert report["attempts"] == 2          # failed once, fixed on the retry
    assert calls["n"] == 2                   # the model was re-asked with the error
    assert report["results"]["t"]["ok"] is True
    assert report["results"]["t"]["output"] == "iso"


def test_gives_up_after_max_attempts():
    registry = tt.conn.registry()

    def always_bad(_r, _p, *, model, base_url):
        return BAD

    report = repair_flow.generate_run_repair(
        "x", registry, llm_registry={}, model="fake", base_url="fake",
        allow=["time://*"], max_attempts=2, ask=always_bad,
    )
    assert report["ok"] is False
    assert report["attempts"] == 2
    assert report["lastError"]["uri"] == "nosuch://host/a/query/b"


def test_action_space_feeds_routes_to_prompt():
    registry = tt.conn.registry()
    space = urirun.action_space(registry)
    prompt = repair_flow.build_prompt("goal", space)
    assert "time://host/clock/query/now" in prompt
    assert "Output ONLY YAML" in prompt
