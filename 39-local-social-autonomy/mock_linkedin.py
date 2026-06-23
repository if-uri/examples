#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Local-only LinkedIn-like development surface. It has a login form backed by .env
# credentials and a fake feed with a publish form. No network calls, no real social
# service, no external side effects.

from __future__ import annotations

import argparse
import html
import json
import secrets
import threading
import time
import urllib.parse
from dataclasses import dataclass, field
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_ENV = HERE / ".env"
EXAMPLE_ENV = HERE / ".env.example"


def load_env(path: str | Path = DEFAULT_ENV) -> dict[str, str]:
    """Small .env reader for the example; no python-dotenv dependency."""
    env_path = Path(path)
    if not env_path.exists() and env_path.name == ".env" and EXAMPLE_ENV.exists():
        env_path = EXAMPLE_ENV
    data: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


@dataclass
class MockState:
    user: str
    password: str
    name: str
    sessions: set[str] = field(default_factory=set)
    posts: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "MockState":
        return cls(
            user=env.get("REAL_LINKEDIN_USER") or env.get("LINKEDIN_USER") or env.get("FAKE_LINKEDIN_USER", "tom@example.local"),
            password=env.get("REAL_LINKEDIN_PASSWORD") or env.get("LINKEDIN_PASSWORD") or env.get("FAKE_LINKEDIN_PASSWORD", "dev-password-123"),
            name=env.get("REAL_LINKEDIN_NAME") or env.get("LINKEDIN_NAME") or env.get("FAKE_LINKEDIN_NAME", "Tom Developer"),
        )

    def publish(self, content: str) -> dict[str, Any]:
        post = {
            "id": f"post-{len(self.posts) + 1}",
            "author": self.name,
            "content": content,
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.posts.insert(0, post)
        return post


def _page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, -apple-system, sans-serif; }}
    body {{ margin: 0; background: #0f1115; color: #e7e9ee; }}
    header {{ height: 58px; display: flex; align-items: center; gap: 18px; padding: 0 22px;
      background: #151922; border-bottom: 1px solid #252b36; position: sticky; top: 0; z-index: 2; }}
    .brand {{ width: 34px; height: 34px; display: grid; place-items: center; border-radius: 5px;
      background: #0a66c2; color: white; font-weight: 800; font-size: 22px; }}
    .search {{ width: min(420px, 42vw); height: 34px; border-radius: 18px; border: 1px solid #343c49;
      background: #10141b; color: #dfe4ec; padding: 0 15px; }}
    nav {{ margin-left: auto; display: flex; gap: 18px; color: #aeb6c2; font-size: 13px; }}
    main {{ width: min(1180px, calc(100vw - 32px)); margin: 22px auto; display: grid;
      grid-template-columns: 260px minmax(420px, 1fr) 300px; gap: 18px; }}
    section, aside, .panel {{ background: #191e27; border: 1px solid #2a3240; border-radius: 8px; }}
    .profile {{ padding: 18px; }}
    .avatar {{ width: 76px; height: 76px; border-radius: 50%; background: linear-gradient(135deg, #4aa3ff, #26c281);
      display: grid; place-items: center; font-weight: 800; font-size: 30px; margin-bottom: 12px; }}
    .muted {{ color: #a8b0bd; }}
    .composer {{ padding: 16px; margin-bottom: 14px; }}
    textarea {{ width: 100%; min-height: 104px; resize: vertical; box-sizing: border-box; border-radius: 8px;
      border: 1px solid #394252; background: #10141b; color: #f4f6fa; padding: 12px; font: inherit; }}
    input {{ box-sizing: border-box; width: 100%; border-radius: 8px; border: 1px solid #394252;
      background: #10141b; color: #f4f6fa; padding: 12px; font: inherit; }}
    button {{ border: 0; border-radius: 18px; background: #0a66c2; color: white; padding: 9px 18px;
      font-weight: 700; cursor: pointer; }}
    .post {{ padding: 16px; margin-bottom: 14px; }}
    .post h3 {{ margin: 0 0 4px; font-size: 15px; }}
    .post p {{ line-height: 1.45; }}
    .login {{ width: min(420px, calc(100vw - 32px)); margin: 70px auto; padding: 24px; }}
    .login form {{ display: grid; gap: 12px; }}
    .error {{ color: #ff9b9b; }}
    @media (max-width: 900px) {{ main {{ grid-template-columns: 1fr; }} nav {{ display: none; }} }}
  </style>
</head>
<body>
{body}
</body>
</html>""".encode("utf-8")


class MockLinkedInHandler(BaseHTTPRequestHandler):
    server_version = "LinkedIn/0.1"

    @property
    def state(self) -> MockState:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _send(self, status: int, body: bytes, content_type: str = "text/html; charset=utf-8",
              headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, location: str, headers: dict[str, str] | None = None) -> None:
        self._send(HTTPStatus.SEE_OTHER, b"", headers={"Location": location, **(headers or {})})

    def _form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8", "replace")
        return {k: v[0] if v else "" for k, v in urllib.parse.parse_qs(raw).items()}

    def _session_id(self) -> str:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        return cookie.get("fake_li_session").value if cookie.get("fake_li_session") else ""

    def _authenticated(self) -> bool:
        return self._session_id() in self.state.sessions

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path in {"/", "/feed"}:
            if not self._authenticated():
                self._redirect("/login?next=/feed")
                return
            self._send(200, self._feed())
            return
        if path == "/login":
            self._send(200, self._login())
            return
        if path == "/api/posts":
            body = json.dumps({"ok": True, "posts": self.state.posts}, ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        if path == "/login":
            form = self._form()
            if form.get("username") == self.state.user and form.get("password") == self.state.password:
                sid = secrets.token_urlsafe(24)
                self.state.sessions.add(sid)
                self._redirect("/feed", {"Set-Cookie": f"fake_li_session={sid}; Path=/; HttpOnly; SameSite=Lax"})
                return
            self._send(401, self._login("Invalid local development credentials."))
            return
        if path == "/post":
            if not self._authenticated():
                self._redirect("/login?next=/feed")
                return
            content = self._form().get("content", "").strip()
            if content:
                self.state.publish(content)
            self._redirect("/feed")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def _login(self, error: str = "") -> bytes:
        err = f'<p class="error" data-testid="login-error">{html.escape(error)}</p>' if error else ""
        return _page("LinkedIn Login", f"""
<section class="login">
  <div class="brand">in</div>
  <h1>Sign in to LinkedIn</h1>
  <p class="muted">Local development surface. Credentials come from .env.</p>
  {err}
  <form method="post" action="/login" data-testid="login-form">
    <label>Email<input name="username" autocomplete="username" data-testid="username"></label>
    <label>Password<input name="password" type="password" autocomplete="current-password" data-testid="password"></label>
    <button data-testid="login-submit">Sign in</button>
  </form>
</section>
""")

    def _feed(self) -> bytes:
        posts = "\n".join(
            f"""<article class="post" data-testid="post" data-post-id="{html.escape(post['id'])}">
  <h3>{html.escape(post['author'])}</h3>
  <div class="muted">{html.escape(post['createdAt'])}</div>
  <p>{html.escape(post['content'])}</p>
</article>""" for post in self.state.posts
        ) or '<article class="post muted" data-testid="empty-feed">No posts yet.</article>'
        return _page("LinkedIn Feed", f"""
<header>
  <div class="brand">in</div>
  <input class="search" aria-label="Search" placeholder="I'm looking for..." value="">
  <nav><span>Home</span><span>My Network</span><span>Jobs</span><span>Messaging</span><span>Notifications</span></nav>
</header>
<main>
  <aside class="profile">
    <div class="avatar">{html.escape(self.state.name[:1].upper())}</div>
    <h2>{html.escape(self.state.name)}</h2>
    <p class="muted">URI automation developer</p>
    <p>Profile viewers <strong>110</strong></p>
    <p>Post impressions <strong>2,461</strong></p>
  </aside>
  <section>
    <div class="composer">
      <h2>Start a post</h2>
      <form method="post" action="/post" data-testid="post-form">
        <textarea name="content" data-testid="post-content" placeholder="What do you want to talk about?"></textarea>
        <p><button data-testid="publish-button">Publish</button></p>
      </form>
    </div>
    <div data-testid="feed">{posts}</div>
  </section>
  <aside class="profile">
    <h2>Messaging</h2>
    <p class="muted">Local mock conversations are read-only in this demo.</p>
    <h2>Today's puzzles</h2>
    <p>Wend #14</p><p>Patches #97</p><p>Mini Sudoku #315</p>
  </aside>
</main>
""")


def start_server(host: str, port: int, env_path: str | Path = DEFAULT_ENV) -> tuple[ThreadingHTTPServer, MockState]:
    state = MockState.from_env(load_env(env_path))
    server = ThreadingHTTPServer((host, port), MockLinkedInHandler)
    server.state = state  # type: ignore[attr-defined]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Fake LinkedIn development server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    args = parser.parse_args()
    state = MockState.from_env(load_env(args.env))
    server = ThreadingHTTPServer((args.host, args.port), MockLinkedInHandler)
    server.state = state  # type: ignore[attr-defined]
    print(json.dumps({"ok": True, "url": f"http://{args.host}:{args.port}/feed", "user": state.user}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
