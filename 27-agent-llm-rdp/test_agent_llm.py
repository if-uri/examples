# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Deterministic CI for the LLM-driven RDP control task. The heuristic-fallback path
# runs offline (no API key) and must still compose a valid, covered plan; the live LLM
# path runs only when an OpenRouter key is configured.
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import llm_planner  # noqa: E402

SPACE = [
    {"uri": "rdp://{host}/session/command/prepare-target", "kind": "command", "label": "rdp.session.prepare_target"},
    {"uri": "kvm://{host}/monitor/{monitor}/query/screenshot", "kind": "query", "label": "kvm.monitor.screenshot"},
    {"uri": "ocr://{host}/image/latest/query/text", "kind": "query", "label": "ocr.latest.text"},
    {"uri": "llm://{host}/text/query/decide", "kind": "query", "label": "llm.text.decide"},
]


def test_extract_json_strips_fences():
    assert llm_planner._extract_json('```json\n[{"uri":"a"}]\n```') == [{"uri": "a"}]
    assert llm_planner._extract_json("noise [\n{\"uri\":\"x\"}\n] tail") == [{"uri": "x"}]


def test_heuristic_plan_covers_the_goal_offline(monkeypatch):
    # force the offline path: no key -> heuristic
    monkeypatch.setenv("URIRUN_ENV", "/nonexistent")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    steps = llm_planner.plan("control the computer over rdp, screenshot, ocr, decide", SPACE)
    schemes = [s["uri"].split("://", 1)[0] for s in steps]
    assert schemes[0] == "rdp"
    assert "kvm" in schemes and "ocr" in schemes and "llm" in schemes
    # path params concretized, and the decide step threads the OCR output
    assert all("{" not in s["uri"] for s in steps)
    assert any(str(s["payload"]).find("$ref:") != -1 for s in steps)


def test_planner_only_picks_uris_from_the_space():
    steps = llm_planner.heuristic_plan("do it", SPACE)
    allowed = {r["uri"].split("://", 1)[0] for r in SPACE}
    assert all(s["uri"].split("://", 1)[0] in allowed for s in steps)


@pytest.mark.skipif(not os.environ.get("OPENROUTER_API_KEY") and not Path(llm_planner.DEFAULT_ENV).exists(),
                    reason="no OpenRouter key / .env configured")
def test_live_llm_plan_is_valid_when_configured():
    steps = llm_planner.plan("open rdp, kvm screenshot, ocr, decide next action", SPACE)
    assert steps, "planner returned no steps"
    allowed = {r["uri"].split("://", 1)[0] for r in SPACE}
    assert all(s["uri"].split("://", 1)[0] in allowed for s in steps)
