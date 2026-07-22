#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Read-only LinkedIn scout. Attaches to a Chrome session you already run with
# --remote-debugging-port, walks the feed / your posts / saved / a hashtag page,
# scrolls, parses, and appends interesting posts to a local markdown file.
#
# It never types, never clicks publish, never navigates away from these read
# pages. The publish step stays a human action.

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mock_linkedin
from websocket_frames import recv_json, send_text

DEFAULT_ENV = HERE / ".env"
CAPTURES = HERE / ".state" / "captures.md"


@dataclass
class ScoutConfig:
    debug_port: int
    base: str
    profile_path: str
    hashtag: str
    scroll_steps: int
    scroll_delay: float
    min_text_len: int


def scout_config(env_path: str | Path = DEFAULT_ENV, *, debug_port: int | None = None) -> ScoutConfig:
    env = mock_linkedin.load_env(env_path)
    port = int(debug_port) if debug_port is not None else int(env.get("LI_DEBUG_PORT") or "9222")
    return ScoutConfig(
        debug_port=port,
        base=f"http://127.0.0.1:{port}",
        profile_path="/" + (env.get("LI_PROFILE_PATH") or "/in/tom-developer/recent-activity/").lstrip("/"),
        hashtag=(env.get("LI_HASHTAG") or "programming").strip().lstrip("#"),
        scroll_steps=int(env.get("LI_SCROLL_STEPS") or "4"),
        scroll_delay=float(env.get("LI_SCROLL_DELAY") or "1.5"),
        min_text_len=int(env.get("LI_MIN_TEXT_LEN") or "80"),
    )


class AttachCDP:
    """Minimal CDP client that attaches to a running Chrome over /json."""

    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.sock: socket.socket | None = None
        self.next_id = 1
        self.target_id: str | None = None

    def _json(self, path: str) -> Any:
        req = urllib.request.Request(self.base + path)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8") or "[]")

    def connect(self, prefer_url_contains: str = "linkedin.com") -> None:
        pages = [p for p in self._json("/json") if p.get("type") == "page"]
        if not pages:
            raise RuntimeError(f"no Chrome pages at {self.base}; is --remote-debugging-port set?")
        if prefer_url_contains:
            preferred = [p for p in pages if prefer_url_contains in str(p.get("url", ""))]
            pages = preferred or pages
        page = pages[0]
        ws_url = page["webSocketDebuggerUrl"]
        parsed = urllib.parse.urlparse(ws_url)
        self.sock = socket.create_connection((parsed.hostname, parsed.port), timeout=6)
        # Finish the WS handshake so subsequent command() works.
        import base64, os  # local; only needed once
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {parsed.path} HTTP/1.1\r\n"
                           f"Host: {parsed.hostname}:{parsed.port}\r\n"
                           "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.sock.recv(4096)

    # --- send/recv frames (mirrors autonomous_browser.CDPBrowser) ---
    def _send(self, text: str) -> None:
        assert self.sock is not None
        send_text(self.sock, text)

    def _recv(self) -> dict[str, Any]:
        assert self.sock is not None
        return recv_json(self.sock)

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        msg_id = self.next_id
        self.next_id += 1
        self._send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            message = self._recv()
            if message.get("id") == msg_id:
                return message

    def eval(self, expression: str) -> Any:
        result = self.command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        if "exceptionDetails" in result:
            return None
        return (result.get("result") or {}).get("result", {}).get("value")

    def scroll_down(self, delay: float) -> None:
        self.eval("window.scrollBy(0, window.innerHeight * 0.9)")
        time.sleep(delay)

    def close(self) -> None:
        try:
            if self.sock:
                self.sock.close()
        finally:
            self.sock = None


EXTRACT_JS = """(() => {
  const out = [];
  const seen = new Set();
  // LinkedIn feed items use various wrappers over time; grab any article-like block.
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
    
    // Extract comments if any
    const comments = [];
    b.querySelectorAll('.comments-comment-item, .feed-shared-comment-item, [data-testid="comment-item"], .comments-comment-item-content-body').forEach(c => {
      const cAuthor = (c.querySelector('.comments-post-meta__profile-link, .comments-comment-meta__description, .comments-comment-item__name, h4, .comments-comment-item__username')?.innerText || '').trim();
      const cText = (c.querySelector('.comments-comment-item__main-content, .comments-comment-item__body, .comments-comment-item-content-body, p')?.innerText || '').trim();
      if (cAuthor || cText) {
        comments.push({ author: cAuthor, text: cText });
      }
    });

    if (seen.has(href + text.slice(0, 40))) continue;
    seen.add(href + text.slice(0, 40));
    out.push({ author: author.slice(0, 140), text: text.slice(0, 1200), url: href, comments: comments });
  }
  return out;
})()"""


def extract_posts(cdp: AttachCDP) -> list[dict[str, Any]]:
    value = cdp.eval(EXTRACT_JS)
    return value if isinstance(value, list) else []


def scout_page(cdp: AttachCDP, url: str, config: ScoutConfig) -> list[dict[str, Any]]:
    cdp.command("Page.navigate", {"url": url})
    cdp.eval("document.readyState === 'complete' || new Promise(r => setTimeout(r, 2000))")
    time.sleep(2.0)
    posts: list[dict[str, Any]] = []
    for _ in range(config.scroll_steps):
        cdp.scroll_down(config.scroll_delay)
        for post in extract_posts(cdp):
            if len(post.get("text", "")) >= config.min_text_len and post not in posts:
                posts.append(post)
    return posts


def dedupe_keep_order(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("url") or "") + "|" + (item.get("text") or "")[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def to_markdown(posts: list[dict[str, Any]], sources: dict[str, str]) -> str:
    lines: list[str] = [f"# LinkedIn captures · {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for source, url in sources.items():
        lines.append(f"- source: {source} — <{url}>")
    lines.append("")
    for i, post in enumerate(posts, 1):
        lines.append(f"## {i}. {post.get('author') or '(no author)'}")
        lines.append("")
        lines.append(post.get("text", "").strip() or "(no text)")
        lines.append("")
        if post.get("url"):
            lines.append(f"link: <{post['url']}>")
            lines.append("")
        comments = post.get("comments", [])
        if comments:
            lines.append("### Comments:")
            for c in comments:
                lines.append(f"- **{c.get('author') or 'Unknown'}**: {c.get('text') or ''}")
            lines.append("")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def write_captures(path: Path, markdown: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(markdown)


def search_phrase(cdp: AttachCDP, phrase: str) -> None:
    # Try typing into the search filter
    typed = cdp.eval(f"""(() => {{
      const input = document.querySelector('input.search-global-typeahead__input, input[placeholder*="Search"], input.search');
      if (input) {{
        input.focus();
        input.value = {json.dumps(phrase)};
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        const form = input.closest('form');
        if (form) {{
          form.submit();
          return true;
        }}
      }}
      return false;
    }})()""")
    if typed:
        time.sleep(3.0)
    else:
        # Fallback to direct navigation if input not found
        url = f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote(phrase)}"
        cdp.command("Page.navigate", {"url": url})
        time.sleep(3.0)


def scout_run(
    env_path: str | Path = DEFAULT_ENV,
    *,
    debug_port: int | None = None,
    out_path: Path | str | None = None,
    pages: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    config = scout_config(env_path, debug_port=debug_port)
    cdp = AttachCDP(config.base)
    cdp.connect()
    try:
        selected = pages or ("feed", "myposts", "saved", "hashtag", "search")
        urls: dict[str, str] = {}
        if "feed" in selected:
            urls["feed"] = "https://www.linkedin.com/feed/"
        if "myposts" in selected:
            urls["myposts"] = "https://www.linkedin.com" + config.profile_path
        if "saved" in selected:
            urls["saved"] = "https://www.linkedin.com/my-items/saved-posts/"
        if "hashtag" in selected:
            urls["hashtag"] = f"https://www.linkedin.com/feed/hashtag/?keywords={urllib.parse.quote(config.hashtag)}"
        if "search" in selected:
            urls["search"] = f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote(config.hashtag)}"

        all_posts: list[dict[str, Any]] = []
        visited: dict[str, Any] = {}
        for name, url in urls.items():
            try:
                if name == "search":
                    # Navigate to feed first to access search input, then search
                    cdp.command("Page.navigate", {"url": "https://www.linkedin.com/feed/"})
                    time.sleep(3.0)
                    search_phrase(cdp, config.hashtag)
                    cdp.eval("document.readyState === 'complete'")
                    posts: list[dict[str, Any]] = []
                    for _ in range(config.scroll_steps):
                        cdp.scroll_down(config.scroll_delay)
                        for post in extract_posts(cdp):
                            if len(post.get("text", "")) >= config.min_text_len and post not in posts:
                                posts.append(post)
                else:
                    posts = scout_page(cdp, url, config)
                visited[name] = {"url": url, "count": len(posts)}
                all_posts.extend(posts)
            except Exception as exc:  # noqa: BLE001
                visited[name] = {"url": url, "error": str(exc)}

        unique = dedupe_keep_order(all_posts)
        markdown = to_markdown(unique, {k: v["url"] for k, v in visited.items() if "url" in v})
        out = Path(out_path) if out_path else CAPTURES
        write_captures(out, markdown)
        return {
            "ok": True,
            "pages": visited,
            "captured": len(unique),
            "out": str(out),
        }
    finally:
        cdp.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only LinkedIn scout: capture interesting posts to markdown.")
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--debug-port", type=int, help="override LI_DEBUG_PORT from .env")
    parser.add_argument("--out", help="markdown output path; defaults to .state/captures.md")
    parser.add_argument("--pages", help="comma list: feed,myposts,saved,hashtag,search")
    args = parser.parse_args(argv)

    pages = tuple(p.strip() for p in args.pages.split(",") if p.strip()) if args.pages else None
    result = scout_run(args.env, debug_port=args.debug_port, out_path=args.out, pages=pages)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
