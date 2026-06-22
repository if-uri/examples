# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Offline-safe checks for the NL→YAML→execute→repair loop. Fully deterministic:
# the stub planner fails on the first pass (empty key) and self-corrects from the
# structured error on the second.

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent_repair


def _cleanup():
    for f in ("notes.json", "agent-run.log"):
        p = os.path.join(os.path.dirname(agent_repair.__file__), f)
        if os.path.exists(p):
            os.remove(p)


def test_action_space_is_the_allowed_uris():
    import urirun
    registry = agent_repair.load_registry()
    uris = {r["uri"] for r in urirun.action_space(registry)}
    assert "note://host/store/command/put" in uris
    assert "time://host/clock/query/now" in uris


def test_stub_planner_emits_valid_yaml_flow():
    from urirun_flow import Flow
    yaml_text = agent_repair.plan_yaml("zapisz notatke",
                                       ["time://host/clock/query/now", "note://host/store/command/put"])
    flow = Flow.from_yaml(yaml_text)               # parses + schema-validates
    assert [s.uri for s in flow.steps][:2] == ["time://host/clock/query/now", "note://host/store/command/put"]
    # first pass intentionally leaves the required key empty
    save = next(s for s in flow.steps if s.id == "save")
    assert save.payload.get("key", "") == ""


def test_repair_loop_recovers_on_second_attempt():
    _cleanup()
    registry = agent_repair.load_registry()
    report = agent_repair.repair_run("sprawdz dysk i zapisz notatke", registry, execute=True, tries=3)
    assert report["ok"] is True
    assert report["attempts"] == 2                 # failed once, fixed on the retry
    # attempt 1 failed on the note step with the structured "key required" error
    a1 = report["transcript"][0]
    assert a1["ok"] is False
    assert a1["failed"]["step"] == "save"
    assert "key is required" in a1["failed"]["error"]
    # attempt 2 succeeded and actually stored the note
    assert report["transcript"][1]["ok"] is True
    notes = os.path.join(os.path.dirname(agent_repair.__file__), "notes.json")
    assert os.path.exists(notes)
    _cleanup()


def test_unknown_uri_is_rejected_before_execution():
    """A planner that hallucinates a URI outside the action space never executes —
    the loop turns it into structured 'validate' feedback."""
    registry = agent_repair.load_registry()

    def bad_planner(goal, allowed, feedback=None):
        return "task: {title: x}\nsteps:\n- id: s1\n  uri: shell://host/run/command/exec\n"

    report = agent_repair.repair_run("x", registry, execute=True, tries=2, planner=bad_planner)
    assert report["ok"] is False
    assert report["lastError"]["stage"] == "validate"
    assert "shell://host/run/command/exec" in report["lastError"]["unknownUris"]


def test_dry_run_does_not_execute_steps():
    _cleanup()
    registry = agent_repair.load_registry()
    # In dry-run the note tool never runs, so the empty-key failure can't happen;
    # the flow "passes" as a plan without writing anything.
    report = agent_repair.repair_run("zapisz", registry, execute=False, tries=1)
    assert report["ok"] is True
    notes = os.path.join(os.path.dirname(agent_repair.__file__), "notes.json")
    assert not os.path.exists(notes)               # nothing was actually written
    _cleanup()


# --- the ready-to-run YAML flow files --------------------------------------

import glob
from urirun_flow import Flow

FLOWS = sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flows", "*.yaml")))


def test_ready_flows_parse_and_use_known_uris():
    import urirun
    assert FLOWS, "no flows/*.yaml found"
    allowed = {r["uri"] for r in urirun.action_space(agent_repair.load_registry(include_llm=True))}
    for path in FLOWS:
        flow = Flow.from_yaml(open(path, encoding="utf-8").read())   # parses + validates DAG
        assert flow.steps, f"{path} has no steps"
        for s in flow.steps:
            assert s.uri in allowed, f"{path}: {s.uri} not in action space"


def test_ready_flow_save_note_executes():
    _cleanup()
    registry = agent_repair.load_registry(include_llm=True)
    path = os.path.join(os.path.dirname(agent_repair.__file__), "flows", "save-note.yaml")
    report = agent_repair.run_flow_file(path, registry, execute=True)
    assert report["ok"] is True
    assert [t["uri"] for t in report["timeline"]][0] == "time://host/clock/query/now"
    assert os.path.exists(os.path.join(os.path.dirname(agent_repair.__file__), "notes.json"))
    _cleanup()


def test_ready_flow_ocr_dry_run_is_a_valid_plan():
    registry = agent_repair.load_registry(include_llm=True)
    path = os.path.join(os.path.dirname(agent_repair.__file__), "flows", "ocr-to-note.yaml")
    report = agent_repair.run_flow_file(path, registry, execute=False)
    assert report["ok"] is True                    # the plan validates (URIs + DAG)
    assert any(t["uri"] == "llm://host/vision/command/ocr" for t in report["timeline"])
