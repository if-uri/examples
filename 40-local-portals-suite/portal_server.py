#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Local-only suite of fake portals for browser autonomy testing. It serves different
# portal UIs based on the Host header: crm.local, support.local, shop.local, docs.local.

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

PORTALS: dict[str, dict[str, Any]] = {
    "crm": {
        "host": "crm.local",
        "title": "Fake CRM",
        "action": "Create lead",
        "record": "lead",
        "fields": {"customer": "Customer", "note": "Note"},
    },
    "support": {
        "host": "support.local",
        "title": "Fake Support",
        "action": "Create ticket",
        "record": "ticket",
        "fields": {"title": "Title", "message": "Message"},
    },
    "shop": {
        "host": "shop.local",
        "title": "Fake Shop Admin",
        "action": "Create order",
        "record": "order",
        "fields": {"product": "Product", "qty": "Quantity"},
    },
    "docs": {
        "host": "docs.local",
        "title": "Fake Docs",
        "action": "Create document",
        "record": "document",
        "fields": {"title": "Title", "body": "Body"},
    },
}


def load_env(path: str | Path = DEFAULT_ENV) -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists() and env_path.name == ".env" and EXAMPLE_ENV.exists():
        env_path = EXAMPLE_ENV
    data: dict[str, str] = {}
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


@dataclass
class PortalState:
    user: str
    password: str
    name: str
    sessions: set[str] = field(default_factory=set)
    records: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: {key: [] for key in PORTALS})

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "PortalState":
        return cls(
            user=env.get("PORTAL_USER", "agent@example.local"),
            password=env.get("PORTAL_PASSWORD", "dev-password-123"),
            name=env.get("PORTAL_NAME", "Local Portal Agent"),
        )

    def create_record(self, portal: str, payload: dict[str, str]) -> dict[str, Any]:
        cfg = PORTALS[portal]
        record = {
            "id": f"{portal}-{len(self.records[portal]) + 1}",
            "type": cfg["record"],
            "createdBy": self.name,
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "fields": {key: str(payload.get(key, "")).strip() for key in cfg["fields"]},
        }
        self.records[portal].insert(0, record)
        return record


def _page(title: str, body: str) -> bytes:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, -apple-system, sans-serif; }}
    body {{ margin: 0; background: #111318; color: #edf1f7; }}
    header {{ display: flex; align-items: center; gap: 18px; height: 58px; padding: 0 24px;
      background: #191f2a; border-bottom: 1px solid #2c3443; }}
    .logo {{ width: 34px; height: 34px; border-radius: 6px; background: #0a66c2; display: grid;
      place-items: center; font-weight: 800; }}
    nav {{ margin-left: auto; display: flex; gap: 18px; color: #aeb8c7; font-size: 13px; }}
    main {{ width: min(1080px, calc(100vw - 32px)); margin: 24px auto; display: grid;
      grid-template-columns: minmax(420px, 1fr) 320px; gap: 18px; }}
    section, aside {{ background: #1a202b; border: 1px solid #2d3645; border-radius: 8px; padding: 18px; }}
    form {{ display: grid; gap: 12px; }}
    input, textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #3a4557; border-radius: 8px;
      background: #10151d; color: #f5f7fb; padding: 11px; font: inherit; }}
    textarea {{ min-height: 96px; resize: vertical; }}
    button {{ width: max-content; border: 0; border-radius: 18px; background: #0a66c2; color: white;
      padding: 9px 18px; font-weight: 700; cursor: pointer; }}
    .record {{ padding: 12px 0; border-top: 1px solid #2d3645; }}
    .muted {{ color: #aeb8c7; }}
    .login {{ width: min(420px, calc(100vw - 32px)); margin: 70px auto; }}
    .error {{ color: #ff9b9b; }}
    @media (max-width: 800px) {{ main {{ grid-template-columns: 1fr; }} nav {{ display: none; }} }}
  </style>
</head>
<body>{body}</body>
</html>""".encode("utf-8")


class PortalHandler(BaseHTTPRequestHandler):
    server_version = "LocalPortals/0.1"

    @property
    def state(self) -> PortalState:
        return self.server.state  # type: ignore[attr-defined]

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _portal(self) -> str:
        host = (self.headers.get("Host") or "").split(":", 1)[0].lower()
        for key, cfg in PORTALS.items():
            if host == cfg["host"]:
                return key
        return "crm"

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
        return {key: values[0] if values else "" for key, values in urllib.parse.parse_qs(raw).items()}

    def _session_id(self) -> str:
        cookie = SimpleCookie(self.headers.get("Cookie"))
        return cookie.get("local_portal_session").value if cookie.get("local_portal_session") else ""

    def _authenticated(self) -> bool:
        return self._session_id() in self.state.sessions

    def do_GET(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        portal = self._portal()
        if path in {"/", "/dashboard"}:
            if not self._authenticated():
                self._redirect("/login")
                return
            self._send(200, self._dashboard(portal))
            return
        if path == "/login":
            self._send(200, self._login(portal))
            return
        if path == "/api/records":
            body = json.dumps({"ok": True, "portal": portal, "records": self.state.records[portal]},
                              ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        portal = self._portal()
        if path == "/login":
            form = self._form()
            if form.get("username") == self.state.user and form.get("password") == self.state.password:
                sid = secrets.token_urlsafe(24)
                self.state.sessions.add(sid)
                self._redirect("/dashboard", {"Set-Cookie": f"local_portal_session={sid}; Path=/; HttpOnly; SameSite=Lax"})
                return
            self._send(401, self._login(portal, "Invalid local development credentials."))
            return
        if path == "/action":
            if not self._authenticated():
                self._redirect("/login")
                return
            self.state.create_record(portal, self._form())
            self._redirect("/dashboard")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def _login(self, portal: str, error: str = "") -> bytes:
        cfg = PORTALS[portal]
        err = f'<p class="error" data-testid="login-error">{html.escape(error)}</p>' if error else ""
        return _page(f"{cfg['title']} Login", f"""
<section class="login">
  <div class="logo">{html.escape(portal[:2].upper())}</div>
  <h1>Sign in to {html.escape(cfg['title'])}</h1>
  <p class="muted">Local development portal. Credentials come from .env.</p>
  {err}
  <form method="post" action="/login" data-testid="login-form">
    <label>Email<input name="username" autocomplete="username" data-testid="username"></label>
    <label>Password<input name="password" type="password" autocomplete="current-password" data-testid="password"></label>
    <button data-testid="login-submit">Sign in</button>
  </form>
</section>
""")

    def _dashboard(self, portal: str) -> bytes:
        cfg = PORTALS[portal]
        fields = "\n".join(
            f'<label>{html.escape(label)}<textarea name="{html.escape(key)}" data-testid="{html.escape(key)}"></textarea></label>'
            if key in {"note", "message", "body"} else
            f'<label>{html.escape(label)}<input name="{html.escape(key)}" data-testid="{html.escape(key)}"></label>'
            for key, label in cfg["fields"].items()
        )
        records = "\n".join(self._record_html(record) for record in self.state.records[portal])
        records = records or '<p class="muted" data-testid="empty-records">No records yet.</p>'
        return _page(str(cfg["title"]), f"""
<header>
  <div class="logo">{html.escape(portal[:2].upper())}</div>
  <strong>{html.escape(cfg['title'])}</strong>
  <nav><span>Dashboard</span><span>Records</span><span>Reports</span><span>Settings</span></nav>
</header>
<main>
  <section>
    <h1>{html.escape(cfg['action'])}</h1>
    <form method="post" action="/action" data-testid="action-form">
      {fields}
      <button data-testid="submit-action">{html.escape(cfg['action'])}</button>
    </form>
  </section>
  <aside>
    <h2>Recent {html.escape(cfg['record'])} records</h2>
    <div data-testid="records">{records}</div>
  </aside>
</main>
""")

    def _record_html(self, record: dict[str, Any]) -> str:
        fields = " ".join(f"<strong>{html.escape(k)}</strong>: {html.escape(str(v))}"
                          for k, v in record["fields"].items())
        return f"""<div class="record" data-testid="record" data-record-id="{html.escape(record['id'])}">
  <div>{html.escape(record['type'])} · {html.escape(record['createdAt'])}</div>
  <p>{fields}</p>
</div>"""


def start_server(host: str, port: int, env_path: str | Path = DEFAULT_ENV) -> tuple[ThreadingHTTPServer, PortalState]:
    state = PortalState.from_env(load_env(env_path))
    server = ThreadingHTTPServer((host, port), PortalHandler)
    server.state = state  # type: ignore[attr-defined]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, state


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local test portals.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    args = parser.parse_args()
    state = PortalState.from_env(load_env(args.env))
    server = ThreadingHTTPServer((args.host, args.port), PortalHandler)
    server.state = state  # type: ignore[attr-defined]
    print(json.dumps({"ok": True, "port": args.port,
                      "hosts": [cfg["host"] for cfg in PORTALS.values()],
                      "user": state.user}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
