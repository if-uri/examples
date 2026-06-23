from __future__ import annotations

from pathlib import Path

import uri_runtime as rt


# --- URI parser ---------------------------------------------------------------

def test_parse_uri_extracts_command_and_query_params():
    cmd, params = rt.parse_uri("chrome://scout/search?scope=posts&q=python")
    assert cmd == "search"
    assert params == {"scope": "posts", "q": "python"}


def test_parse_uri_command_without_query():
    cmd, params = rt.parse_uri("chrome://scout/extract_posts")
    assert cmd == "extract_posts"
    assert params == {}


def test_parse_uri_rejects_unsupported_scheme():
    try:
        rt.parse_uri("https://scout/search?q=x")
    except ValueError as exc:
        assert "unsupported scheme" in str(exc)
    else:
        raise AssertionError("non-chrome scheme should be rejected")


# --- markdown rendering -------------------------------------------------------

def test_render_markdown_includes_meta_posts_comments_and_ocr():
    md = rt.render_markdown(
        "Capture · 2026-06-23 10:00:00",
        posts=[{"author": "Ann", "text": "post body", "url": "https://linkedin.com/posts/a"}],
        comments=[{"author": "Bo", "text": "comment body"}],
        ocr_text="OCR line",
        meta={"url": "https://www.linkedin.com/feed/", "query": "python"},
    )
    assert "# Capture · 2026-06-23 10:00:00" in md
    assert "- url: https://www.linkedin.com/feed/" in md
    assert "- query: python" in md
    assert "## post 1. Ann" in md
    assert "post body" in md
    assert "### comment 1. Bo" in md
    assert "comment body" in md
    assert "## OCR" in md
    assert "OCR line" in md
    assert md.endswith("---\n")


def test_render_markdown_skips_empty_meta_values():
    md = rt.render_markdown("h", posts=[], comments=[], ocr_text="", meta={"url": None, "query": ""})
    assert "- url:" not in md
    assert "- query:" not in md


# --- fake CDP for executor tests ---------------------------------------------

class FakeCDP:
    def __init__(self):
        self.url = "https://www.linkedin.com/feed/"
        self.eval_calls = []

    def command(self, method, params=None):
        if method == "Page.navigate":
            self.url = params["url"]
            return {}
        if method == "Page.captureScreenshot":
            return {"result": {"data": ""}}
        return {}

    def eval(self, expr):
        self.eval_calls.append(expr)
        if "document.title" in expr:
            return {"title": "Feed", "href": self.url}
        if "getBoundingClientRect" in expr:
            return None
        if "feed-shared-update-v2" in expr or "main-feed-async-card" in expr:
            return [{"author": "Ann", "text": "x" * 100, "url": "https://linkedin.com/posts/a"}]
        if "comments-comment-item" in expr:
            return [{"author": "Bo", "text": "nice"}]
        return None


def test_run_program_executes_each_step_and_collects_results():
    cdp = FakeCDP()
    cfg = rt.scout_config(Path(__file__).resolve().parent / ".env")
    program = [
        {"uri": "chrome://scout/navigate?url=https://www.linkedin.com/feed/"},
        {"uri": "chrome://scout/extract_posts?min_text_len=10"},
        {"uri": "chrome://scout/append_markdown?path=/tmp/test_scout_capture.md"},
    ]
    result = rt.run_program(cdp, cfg, program)
    assert result["ok"] is True
    assert result["captured"] >= 1
    assert [r["command"] for r in result["results"]] == ["navigate", "extract_posts", "append_markdown"]


def test_run_program_records_error_and_stops_on_required_step():
    cdp = FakeCDP()
    cfg = rt.scout_config(Path(__file__).resolve().parent / ".env")
    program = [
        {"uri": "chrome://scout/navigate?url=ftp://bad.example/"},  # invalid scheme
        {"uri": "chrome://scout/extract_posts"},
    ]
    result = rt.run_program(cdp, cfg, program)
    assert result["ok"] is False
    assert len(result["results"]) == 1
    assert result["results"][0]["ok"] is False
    assert "absolute http(s)" in result["results"][0]["error"]


def test_run_program_unknown_command_is_reported():
    cdp = FakeCDP()
    cfg = rt.scout_config(Path(__file__).resolve().parent / ".env")
    result = rt.run_program(cdp, cfg, [{"uri": "chrome://scout/totally_made_up"}])
    assert result["ok"] is False
    assert "unknown command" in result["results"][0]["error"]


def test_resolve_program_substitutes_query_placeholder():
    program = rt.resolve_program(rt.DEFAULT_PROGRAM, query="python", hashtag=None)
    search_uri = next(s["uri"] for s in program if "search" in s["uri"])
    assert "q=python" in search_uri
    assert "__QUERY__" not in search_uri


def test_registry_only_contains_read_only_commands():
    # hard assertion: there is no publish/comment/like/message/follow command
    forbidden = {"publish", "post", "comment", "like", "share", "message", "follow", "connect", "type", "click"}
    intersection = forbidden & set(rt.REGISTRY)
    assert intersection == set(), f"write commands leaked into registry: {intersection}"
