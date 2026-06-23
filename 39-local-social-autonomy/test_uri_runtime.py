from __future__ import annotations

import json
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
        self.scrolls = 0

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

    def scroll_down(self, delay):
        self.scrolls += 1


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


def test_scroll_command_calls_browser_scroll():
    cdp = FakeCDP()
    cfg = rt.scout_config(Path(__file__).resolve().parent / ".env")
    result = rt.run_program(cdp, cfg, [{"uri": "chrome://scout/scroll?steps=3&delay=0"}])
    assert result["ok"] is True
    assert cdp.scrolls == 3


def test_filter_limits_extracted_posts():
    cdp = FakeCDP()
    cfg = rt.scout_config(Path(__file__).resolve().parent / ".env")
    program = [
        {"uri": "chrome://scout/filter?q=no-match"},
        {"uri": "chrome://scout/extract_posts?min_text_len=10"},
        {"uri": "chrome://scout/append_markdown?path=/tmp/test_scout_filtered_capture.md"},
    ]
    result = rt.run_program(cdp, cfg, program)
    assert result["ok"] is True
    assert result["results"][1]["count"] == 0
    assert result["captured"] == 0


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


def test_resolve_program_substitutes_hashtag_and_profile_placeholders():
    program = [
        {"uri": "chrome://scout/navigate?url=https://www.linkedin.com__PROFILE_PATH__"},
        {"uri": "chrome://scout/navigate?url=https://www.linkedin.com/feed/hashtag/?keywords=__HASHTAG__"},
    ]
    resolved = rt.resolve_program(
        program,
        query=None,
        hashtag="#python ai",
        profile_path="/in/example/recent-activity/",
    )
    assert resolved[0]["uri"] == "chrome://scout/navigate?url=https://www.linkedin.com/in/example/recent-activity/"
    assert resolved[1]["uri"].endswith("keywords=python%20ai")


def test_registry_only_contains_read_only_commands():
    # hard assertion: there is no publish/comment/like/message/follow command
    forbidden = {"publish", "post", "comment", "like", "share", "message", "follow", "connect", "type", "click"}
    intersection = forbidden & set(rt.REGISTRY)
    assert intersection == set(), f"write commands leaked into registry: {intersection}"


def test_program_files_use_known_uri_commands():
    programs = sorted((Path(__file__).resolve().parent / "programs").glob("*.json"))
    assert programs
    for path in programs:
        program = json.loads(path.read_text(encoding="utf-8"))
        resolved = rt.resolve_program(
            program,
            query="system design",
            hashtag="python",
            profile_path="/in/example/recent-activity/",
            extra={
                "HASHTAG_A": "python",
                "HASHTAG_B": "rust",
                "KEYWORD_A": "release",
                "KEYWORD_B": "security",
            },
        )
        assert resolved, path
        for step in resolved:
            command, _ = rt.parse_uri(step["uri"])
            assert command in rt.REGISTRY, f"{path}: unknown command {command}"
            # no placeholder may survive resolution
            assert "__" not in step["uri"], f"{path}: unresolved placeholder in {step['uri']}"


def test_resolve_program_accepts_extra_tokens():
    program = [
        {"uri": "chrome://scout/navigate?url=https://x/feed/hashtag/?keywords=__HASHTAG_A__"},
        {"uri": "chrome://scout/filter?q=__KEYWORD_B__"},
    ]
    resolved = rt.resolve_program(
        program, query=None, hashtag=None,
        extra={"HASHTAG_A": "python ai", "KEYWORD_B": "security patch"},
    )
    assert "keywords=python%20ai" in resolved[0]["uri"]
    assert "q=security%20patch" in resolved[1]["uri"]


def test_resolve_program_accepts_already_wrapped_token():
    program = [{"uri": "chrome://scout/filter?q=__CUSTOM__"}]
    resolved = rt.resolve_program(
        program, query=None, hashtag=None, extra={"__CUSTOM__": "wrapped"}
    )
    assert "q=wrapped" in resolved[0]["uri"]


# --- OCR -> posts heuristic parser -------------------------------------------

def test_ocr_to_posts_returns_empty_for_empty_input():
    assert rt.ocr_to_posts("") == []
    assert rt.ocr_to_posts("   \n\n  ") == []


def test_ocr_to_posts_splits_real_linkedin_dump_into_sections():
    # Verbatim OCR sample captured from a live LinkedIn search-results page
    # on 2026-06-23 (query: "system design"). Each block here represents one
    # real post surfaced next to a Follow / degree-badge / Connect cue.
    sample = """Vanessa King @- src f+ Connect «+
Designing @ Flatiron Health
a)

Hello network, I'm hiring someone to lead our amazing design systems team here at
Flatiron!

Design Manager, Design Systems ©
Flatiron Health

New York, NY

$160K/yr - $220K/yr * 401(k) benefit

@-~s590 34 @®
Prasoon Soni + 2nd + Follow
'Software Engineer @ Wells Fargo | Scalable & Distributed
1th

Spent the weekend experimenting with a different way to think about
architecture.

--more

@-snoad ®
Halliburton + Follow ++
1®

Notes from the field: "Good design is about creating systems that are intuitive,
accessible, and built to keep operations moving."
... more

e-~ 81152 ©24 39 4 ce
Are these results helpful? © @)
Your Feedback helps us improve search results

C2C and W2 positions/ Direct clients/ ... Join +
Shiva Pathak * 2nd"""
    posts = rt.ocr_to_posts(sample, min_text_len=20)
    assert len(posts) >= 3
    authors = " | ".join(p["author"] for p in posts)
    assert "Vanessa King" in authors
    assert "Prasoon Soni" in authors
    assert "Halliburton" in authors
    # bodies carry real post content, not chrome
    bodies = " | ".join(p["text"] for p in posts)
    assert "Flatiron" in bodies
    assert "Wells Fargo" in bodies
    assert "intuitive" in bodies
    # page chrome must be filtered out
    assert "Are these results helpful" not in bodies
    assert "Your Feedback" not in bodies


def test_ocr_to_posts_drops_pure_chrome_sections():
    chrome_only = "LinkedIn © 2026\nAbout Accessibility Help Center\nPrivacy & Terms"
    posts = rt.ocr_to_posts(chrome_only, min_text_len=10)
    assert posts == []
