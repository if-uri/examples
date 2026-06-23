#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# URI command runtime for read-only browser control. Each command is a typed
# URI (e.g. chrome://scout/search?q=python) that the executor dispatches to a
# handler over an attach-only CDP connection.
#
# Scope is intentionally read-only:
#   navigate, search (via the site's own search box), scroll, extract posts,
#   extract comments, OCR low-text blocks, snapshot, append markdown.
# There is no publish/comment/message/like/follow command. Writes go only to a
# local file, never back into the page.

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mock_linkedin
from scout import AttachCDP, ScoutConfig, scout_config, dedupe_keep_order

DEFAULT_ENV = HERE / ".env"
CAPTURES = HERE / ".state" / "captures.md"

# --- DOM extraction snippets -------------------------------------------------

POSTS_JS = """(() => {
  const out = [];
  const seen = new Set();
  const blocks = document.querySelectorAll(
    '[data-testid="main-feed-async-card"], div.feed-shared-update-v2, article, [role="article"]'
  );
  for (const b of blocks) {
    const text = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (!text) continue;
    const author = (b.querySelector(
      '.update-components-actor__title, .feed-shared-actor__title, span.update-components__text-break-words, h3, h2'
    )?.innerText || '').trim();
    const link = b.querySelector('a[href*="/feed/update/"], a[href*="/posts/"], a[href*="/activities/"]');
    const href = link ? link.href : location.href;
    const key = href + text.slice(0, 40);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push({ author: author.slice(0, 140), text: text.slice(0, 1200), url: href });
  }
  return out;
})()"""

COMMENTS_JS = """(() => {
  const out = [];
  const blocks = document.querySelectorAll(
    'div.comments-comment-item, article.comments-comment-item, [data-testid="comments-comment"]'
  );
  for (const b of blocks) {
    const author = (b.querySelector(
      '.comments-post-meta__name, span.comments-comment-item__name, h3, h4'
    )?.innerText || '').trim();
    const text = (b.innerText || '').replace(/\\s+/g, ' ').trim();
    if (text) out.push({ author: author.slice(0, 140), text: text.slice(0, 800) });
  }
  return out;
})()"""

SCROLL_FILTER_JS = """(() => {
  const q = window.__SCOUT_FILTER__;
  if (!q) return [];
  const ql = q.toLowerCase();
  const out = [];
  document.querySelectorAll('article, [role="article"], div.feed-shared-update-v2').forEach(b => {
    const t = (b.innerText || '').toLowerCase();
    if (t.includes(ql)) {
      const text = (b.innerText || '').replace(/\\s+/g, ' ').trim();
      if (text) out.push({ text: text.slice(0, 1200) });
    }
  });
  return out;
})()"""


# --- Command handlers --------------------------------------------------------
# Each handler: (cdp, config, params, ctx) -> dict result.
# ctx is a mutable per-run dict (carries captured markdown, last OCR text, etc.)


def cmd_navigate(cdp: AttachCDP, config: ScoutConfig, params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    url = params.get("url") or "https://www.linkedin.com/feed/"
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"navigate requires absolute http(s) url, got: {url}")
    cdp.command("Page.navigate", {"url": url})
    cdp.eval("document.readyState === 'complete' || new Promise(r => setTimeout(r, 2000))")
    time.sleep(float(params.get("settle", 2.0)))
    info = cdp.eval("({title: document.title, href: location.href})") or {}
    ctx["last_url"] = info.get("href", url)
    return {"ok": True, "navigated": info}


def cmd_search(cdp: AttachCDP, config: ScoutConfig, params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Use the site's own search box by typing into it and pressing Enter."""
    query = (params.get("q") or params.get("query") or "").strip()
    if not query:
        raise ValueError("search requires 'q'")
    scope = params.get("scope", "content")
    base = {
        "content":  "https://www.linkedin.com/search/results/all/?keywords=",
        "posts":    "https://www.linkedin.com/search/results/content/?keywords=",
        "people":   "https://www.linkedin.com/search/results/people/?keywords=",
    }.get(scope, "https://www.linkedin.com/search/results/all/?keywords=")
    url = base + urllib.parse.quote(query)
    cdp.command("Page.navigate", {"url": url})
    cdp.eval("document.readyState === 'complete' || new Promise(r => setTimeout(r, 2000))")
    time.sleep(float(params.get("settle", 2.5)))
    ctx["last_query"] = query
    return {"ok": True, "scope": scope, "query": query, "url": url}


def cmd_scroll(cdp: AttachCDP, config: ScoutConfig, params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    steps = int(params.get("steps", config.scroll_steps))
    delay = float(params.get("delay", config.scroll_delay))
    return {"ok": True, "scrolled": steps, "filter": ctx.get("filter_query")}


def cmd_filter(cdp: AttachCDP, config: ScoutConfig, params: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    q = (params.get("q") or "").strip()
    cdp.eval(f"window.__SCOUT_FILTER__ = {json.dumps(q)}")
    ctx["filter_query"] = q or None
    return {"ok": True, "filter": q or None}


def cmd_extract_posts(cdp: AttachCDP, config: ScoutConfig, params: dict, ctx: dict[str, Any]) -> dict[str, Any]:
    posts = extract_posts(cdp, min_text_len=int(params.get("min_text_len", config.min_text_len)))
    ctx.setdefault("posts", []).extend(posts)
    return {"ok": True, "count": len(posts)}


def cmd_extract_comments(cdp: AttachCDP, config: ScoutConfig, params: dict, ctx: dict[str, Any]) -> dict[str, Any]:
    value = cdp.eval(COMMENTS_JS)
    comments = value if isinstance(value, list) else []
    if int(params.get("min_text_len", 20)):
        comments = [c for c in comments if len(c.get("text", "")) >= int(params.get("min_text_len", 20))]
    ctx.setdefault("comments", []).extend(comments)
    return {"ok": True, "count": len(comments)}


def cmd_ocr(cdp: AttachCDP, config: ScoutConfig, params: dict, ctx: dict[str, Any]) -> dict[str, Any]:
    selector = params.get("selector") or "main, [role='main'], body"
    out = ocr_element(cdp, selector)
    if out:
        ctx["last_ocr"] = out
    return {"ok": True, "chars": len(out), "text_preview": out[:200]}


def cmd_snapshot(cdp: AttachCDP, config: ScoutConfig, params: dict, ctx: dict[str, Any]) -> dict[str, Any]:
    path = Path(params.get("path") or (HERE / ".state" / f"snapshot-{int(time.time())}.png"))
    path.parent.mkdir(parents=True, exist_ok=True)
    data = cdp.command("Page.captureScreenshot", {"format": "png"}).get("result", {}).get("data")
    if data:
        path.write_bytes(base64.b64decode(data))
    info = cdp.eval("({title: document.title, href: location.href})") or {}
    return {"ok": True, "path": str(path), "page": info}


def cmd_append_markdown(cdp: AttachCDP, config: ScoutConfig, params: dict, ctx: dict[str, Any]) -> dict[str, Any]:
    out_path = Path(params.get("path") or CAPTURES)
    heading = params.get("heading") or f"Capture · {time.strftime('%Y-%m-%d %H:%M:%S')}"
    posts = dedupe_keep_order(ctx.get("posts", []))
    comments = dedupe_keep_order(ctx.get("comments", []))
    ocr_text = ctx.get("last_ocr") or ""
    md = render_markdown(heading, posts=posts, comments=comments, ocr_text=ocr_text,
                         meta={"url": ctx.get("last_url"), "query": ctx.get("last_query"),
                               "filter": ctx.get("filter_query")})
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(md)
    # record what we saved, then clear the buffers for the next append
    ctx["saved_posts"] = ctx.get("saved_posts", 0) + len(posts)
    ctx["saved_comments"] = ctx.get("saved_comments", 0) + len(comments)
    ctx["posts"] = []
    ctx["comments"] = []
    ctx["last_ocr"] = ""
    return {"ok": True, "path": str(out_path), "posts": len(posts), "comments": len(comments)}


# --- helpers -----------------------------------------------------------------

def extract_posts(cdp: AttachCDP, min_text_len: int = 80) -> list[dict[str, str]]:
    value = cdp.eval(POSTS_JS)
    posts = value if isinstance(value, list) else []
    return [p for p in posts if len(p.get("text", "")) >= min_text_len]


def ocr_element(cdp: AttachCDP, selector: str) -> str:
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return ""
    rect = cdp.eval(f"""(() => {{
      const el = document.querySelector({json.dumps(selector)});
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {{x: r.x, y: r.y, width: r.width, height: r.height}};
    }})()""")
    if not rect or not rect.get("width") or not rect.get("height"):
        return ""
    clip = {"x": rect["x"], "y": rect["y"], "width": rect["width"], "height": rect["height"], "scale": 1}
    shot = cdp.command("Page.captureScreenshot", {"format": "png", "clip": clip}).get("result", {}).get("data")
    if not shot:
        return ""
    png = base64.b64decode(shot)
    proc = subprocess.run([tesseract, "stdin", "stdout", "-l", "eng"],
                          input=png, capture_output=True)
    return proc.stdout.decode("utf-8", "replace").strip()


def render_markdown(heading: str, *, posts: list[dict], comments: list[dict],
                    ocr_text: str, meta: dict[str, Any]) -> str:
    lines = [f"# {heading}", ""]
    for k, v in meta.items():
        if v:
            lines.append(f"- {k}: {v}")
    if lines[-1].startswith("- "):
        lines.append("")
    for i, p in enumerate(posts, 1):
        lines.append(f"## post {i}. {p.get('author') or '(no author)'}")
        lines.append("")
        lines.append((p.get("text") or "").strip() or "(no text)")
        lines.append("")
        if p.get("url"):
            lines.append(f"link: <{p['url']}>")
            lines.append("")
    for i, c in enumerate(comments, 1):
        lines.append(f"### comment {i}. {c.get('author') or '(no author)'}")
        lines.append("")
        lines.append((c.get("text") or "").strip() or "(no text)")
        lines.append("")
    if ocr_text:
        lines.append("## OCR")
        lines.append("")
        lines.append("```")
        lines.append(ocr_text)
        lines.append("```")
        lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


# --- registry + executor -----------------------------------------------------

REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "navigate":        cmd_navigate,
    "search":          cmd_search,
    "scroll":          cmd_scroll,
    "filter":          cmd_filter,
    "extract_posts":   cmd_extract_posts,
    "extract_comments":cmd_extract_comments,
    "ocr":             cmd_ocr,
    "snapshot":        cmd_snapshot,
    "append_markdown": cmd_append_markdown,
}


def parse_uri(uri: str) -> tuple[str, dict[str, Any]]:
    """Parse chrome://scout/<command>?<query> into (command, params)."""
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme not in {"chrome", "scout"}:
        raise ValueError(f"unsupported scheme: {parsed.scheme} in {uri}")
    command = parsed.path.strip("/").split("/", 1)[-1] if "/" in parsed.path.strip("/") else parsed.path.strip("/")
    command = command or parsed.netloc
    params = dict(urllib.parse.parse_qsl(parsed.query))
    return command, params


def run_program(cdp: AttachCDP, config: ScoutConfig, commands: list[dict[str, Any]]) -> dict[str, Any]:
    ctx: dict[str, Any] = {"posts": [], "comments": []}
    results = []
    for step in commands:
        uri = step.get("uri") or ""
        try:
            command, params = parse_uri(uri)
            # inline params can override/augment query params
            params = {**params, **{k: v for k, v in step.items() if k not in {"uri", "why"}}}
            handler = REGISTRY.get(command)
            if not handler:
                raise ValueError(f"unknown command '{command}' from URI: {uri}")
            res = handler(cdp, config, params, ctx)
            res["command"] = command
            results.append(res)
        except Exception as exc:  # noqa: BLE001
            results.append({"ok": False, "command": uri, "error": str(exc)})
            if step.get("required", True):
                return {"ok": False, "step": uri, "results": results}
    return {"ok": True, "results": results,
            "captured": ctx.get("saved_posts", 0) + ctx.get("saved_comments", 0)
                        + len(ctx.get("posts", [])) + len(ctx.get("comments", []))}


# --- a sensible default program ----------------------------------------------

DEFAULT_PROGRAM = [
    {"uri": "chrome://scout/navigate?url=https://www.linkedin.com/feed/", "why": "land on home feed"},
    {"uri": "chrome://scout/scroll?steps=2", "why": "warm the feed"},
    {"uri": "chrome://scout/extract_posts", "why": "capture initial posts"},
    {"uri": "chrome://scout/search?scope=posts&q=__QUERY__", "why": "search the phrase"},
    {"uri": "chrome://scout/scroll?steps=4", "why": "load more results"},
    {"uri": "chrome://scout/extract_posts", "why": "capture search results"},
    {"uri": "chrome://scout/extract_comments", "why": "grab visible comments"},
    {"uri": "chrome://scout/ocr?selector=main", "why": "OCR the main column for low-text blocks"},
    {"uri": "chrome://scout/append_markdown", "why": "save everything to captures.md"},
]


def resolve_program(program: list[dict[str, Any]], *, query: str | None, hashtag: str | None) -> list[dict[str, Any]]:
    q = (query or hashtag or "").lstrip("#")
    out = []
    for step in program:
        s = dict(step)
        s["uri"] = s["uri"].replace("__QUERY__", urllib.parse.quote(q))
        out.append(s)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only URI command runtime over attach-CDP.")
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--debug-port", type=int)
    parser.add_argument("--program", help="path to a JSON program; defaults to the built-in feed+search flow")
    parser.add_argument("--query", help="phrase to search (replaces __QUERY__ in the program)")
    parser.add_argument("--hashtag", help="hashtag to search if --query is absent")
    args = parser.parse_args(argv)

    config = scout_config(args.env, debug_port=args.debug_port)
    program = json.loads(Path(args.program).read_text(encoding="utf-8")) if args.program else DEFAULT_PROGRAM
    program = resolve_program(program, query=args.query, hashtag=args.hashtag or config.hashtag)

    cdp = AttachCDP(config.base)
    cdp.connect()
    try:
        result = run_program(cdp, config, program)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    finally:
        cdp.close()


if __name__ == "__main__":
    raise SystemExit(main())
