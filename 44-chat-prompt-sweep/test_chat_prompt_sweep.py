from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("run_chat_prompts", HERE / "run_chat_prompts.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(runner)


def test_prompt_corpus_has_exactly_100_unique_cases():
    cases = runner.load_cases(HERE / "prompts.json")

    assert len(cases) == 100
    assert len({case["id"] for case in cases}) == 100
    assert all(case["prompt"].strip() for case in cases)


def test_defaults_from_dashboard_url_reads_base_and_targets_but_not_execute():
    defaults = runner.defaults_from_url(
        "http://127.0.0.1:8194/?view=chat&execute=1&targets=host,node:lenovo&noLlm=1"
    )

    assert defaults["base"] == "http://127.0.0.1:8194"
    assert defaults["targets"] == ["host", "node:lenovo"]
    assert defaults["no_llm"] is True
    assert "execute" not in defaults


def test_execute_skips_side_effect_cases_by_default():
    case = {"id": "x", "prompt": "opublikuj post", "executeAllowed": False}

    payload, skipped = runner.build_payload(
        case,
        {"targets": ["host"], "nodes": [], "no_llm": True},
        execute=True,
        no_llm=None,
        include_side_effects=False,
        artifact_dir=None,
    )

    assert skipped is True
    assert payload["execute"] is False
    assert payload["no_llm"] is True


def test_execute_can_include_side_effect_cases_when_explicit():
    case = {"id": "x", "prompt": "opublikuj post", "executeAllowed": False}

    payload, skipped = runner.build_payload(
        case,
        {"targets": ["host"], "nodes": [], "no_llm": False},
        execute=True,
        no_llm=None,
        include_side_effects=True,
        artifact_dir=None,
    )

    assert skipped is False
    assert payload["execute"] is True


def test_category_filter_keeps_order():
    cases = runner.load_cases(HERE / "prompts.json")
    selected = runner.select_cases(cases, {"routing"}, 3)

    assert [case["id"] for case in selected] == ["routing-041", "routing-042", "routing-043"]
