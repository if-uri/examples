from __future__ import annotations

import json
from pathlib import Path

import scout


def _posts():
    return [
        {"author": "Ann", "text": "short", "url": "https://linkedin.com/posts/a1"},
        {"author": "Bo",  "text": "x" * 90, "url": "https://linkedin.com/posts/b1"},
        {"author": "Bo",  "text": "x" * 90, "url": "https://linkedin.com/posts/b1"},  # dup
        {"author": "Cy",  "text": "y" * 200, "url": "https://linkedin.com/posts/c1"},
    ]


def test_dedupe_keeps_order_and_drops_duplicates():
    out = scout.dedupe_keep_order(_posts())
    assert [p["author"] for p in out] == ["Ann", "Bo", "Cy"]
    assert len(out) == 3


def test_to_markdown_has_section_per_post_and_source_line():
    md = scout.to_markdown(
        [{"author": "Bo", "text": "hello world" * 10, "url": "https://linkedin.com/posts/x"}],
        {"feed": "https://www.linkedin.com/feed/"},
    )
    assert "# LinkedIn captures" in md
    assert "source: feed" in md
    assert "## 1. Bo" in md
    assert "https://linkedin.com/posts/x" in md
    assert md.endswith("---\n")


def test_write_captures_appends(tmp_path: Path):
    p = tmp_path / "out.md"
    scout.write_captures(p, "first\n")
    scout.write_captures(p, "second\n")
    assert p.read_text(encoding="utf-8") == "first\nsecond\n"


def test_scout_config_reads_env(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "LI_DEBUG_PORT=9333\n"
        "LI_PROFILE_PATH=/in/someone/recent-activity/\n"
        "LI_HASHTAG=#python\n"
        "LI_SCROLL_STEPS=2\n",
        encoding="utf-8",
    )
    cfg = scout.scout_config(env)
    assert cfg.debug_port == 9333
    assert cfg.base == "http://127.0.0.1:9333"
    assert cfg.profile_path == "/in/someone/recent-activity/"
    assert cfg.hashtag == "python"
    assert cfg.scroll_steps == 2


def test_extract_posts_returns_empty_for_none():
    class Fake:
        def eval(self, expr):
            return None
    assert scout.extract_posts(Fake()) == []
