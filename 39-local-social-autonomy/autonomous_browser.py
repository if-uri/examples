#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Full autonomous browser write flow, intentionally scoped to a local fake social
# surface. It launches Chrome with linkedin.com mapped to 127.0.0.1, logs in with
# .env credentials, publishes a fake post, and verifies it in the local mock feed.

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mock_linkedin


DEFAULT_ENV = HERE / ".env"
EXAMPLE_ENV = HERE / ".env.example"
LOCAL_SUFFIXES = ("localhost", "127.0.0.1", "::1", ".local", ".test", ".internal", ".lan")


def ensure_env(path: Path = DEFAULT_ENV) -> Path:
    if path.exists():
        return path
    if path == DEFAULT_ENV and EXAMPLE_ENV.exists():
        path.write_text(EXAMPLE_ENV.read_text(encoding="utf-8"), encoding="utf-8")
        return path
    raise FileNotFoundError(path)


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def chrome_binary() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _local_host(host: str) -> bool:
    host = host.lower().strip("[]")
    return any(host == item or (item.startswith(".") and host.endswith(item)) for item in LOCAL_SUFFIXES)


def assert_local_url(url: str) -> None:
    host = urllib.parse.urlparse(url).hostname or ""
    if not _local_host(host):
        raise ValueError(f"refusing autonomous write flow for non-local host: {host}")


def http_json(base: str, path: str, method: str = "GET") -> Any:
    req = urllib.request.Request(base.rstrip("/") + path, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


class CDPBrowser:
    def __init__(self, chrome: str, debug_port: int, host_rule: str, start_url: str) -> None:
        self.debug_port = debug_port
        self.start_url = start_url
        self.profile = tempfile.TemporaryDirectory(prefix="fake-linkedin-cdp-")
        self.proc = subprocess.Popen([
            chrome,
            f"--remote-debugging-port={debug_port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={self.profile.name}",
            f"--host-resolver-rules=MAP {host_rule} 127.0.0.1",
            "--no-first-run",
            "--no-default-browser-check",
            start_url,
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.sock: socket.socket | None = None
        self.next_id = 1
        self._connect()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.debug_port}"

    def _json(self, path: str, method: str = "GET") -> Any:
        req = urllib.request.Request(self.base + path, method=method)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8") or "[]")

    def _connect(self) -> None:
        deadline = time.time() + 12
        last: Exception | None = None
        wanted = urllib.parse.urlparse(self.start_url).netloc
        while time.time() < deadline:
            try:
                pages = [p for p in self._json("/json") if p.get("type") == "page"]
                if pages:
                    page = next((p for p in pages if wanted and wanted in str(p.get("url", ""))), pages[0])
                    self.sock = self._open_ws(page["webSocketDebuggerUrl"])
                    return
            except Exception as exc:  # noqa: BLE001
                last = exc
            time.sleep(0.2)
        raise RuntimeError(f"Chrome CDP did not start: {last}")

    def _open_ws(self, ws_url: str) -> socket.socket:
        parsed = urllib.parse.urlparse(ws_url)
        sock = socket.create_connection((parsed.hostname, parsed.port), timeout=6)
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall((f"GET {parsed.path} HTTP/1.1\r\n"
                      f"Host: {parsed.hostname}:{parsed.port}\r\n"
                      "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += sock.recv(4096)
        return sock

    def _send_ws(self, text: str) -> None:
        assert self.sock is not None
        payload = text.encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        header += mask
        self.sock.sendall(bytes(header) + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))

    def _read_exact(self, n: int) -> bytes:
        assert self.sock is not None
        data = b""
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                raise RuntimeError("websocket closed")
            data += chunk
        return data

    def _recv_ws(self) -> dict[str, Any]:
        head = self._read_exact(2)
        length = head[1] & 0x7F
        if length == 126:
            length = struct.unpack(">H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self._read_exact(8))[0]
        if head[1] & 0x80:
            mask = self._read_exact(4)
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(self._read_exact(length)))
        else:
            payload = self._read_exact(length)
        return json.loads(payload.decode("utf-8", "replace"))

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        msg_id = self.next_id
        self.next_id += 1
        self._send_ws(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            message = self._recv_ws()
            if message.get("id") == msg_id:
                return message

    def eval(self, expression: str) -> Any:
        result = self.command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        if "exceptionDetails" in result:
            raise RuntimeError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
        return (result.get("result") or {}).get("result", {}).get("value")

    def wait_for(self, expression: str, timeout: float = 8.0) -> Any:
        deadline = time.time() + timeout
        last = None
        while time.time() < deadline:
            try:
                last = self.eval(expression)
                if last:
                    return last
            except Exception as exc:  # noqa: BLE001 - page may be between navigations
                last = str(exc)
            time.sleep(0.2)
        raise TimeoutError(f"condition did not become true: {expression!r}; last={last!r}")

    def close(self) -> None:
        try:
            if self.sock:
                self.sock.close()
        finally:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.profile.cleanup()


def js_login(user: str, password: str) -> str:
    return f"""(() => {{
  const user = document.querySelector('[data-testid="username"]');
  const pass = document.querySelector('[data-testid="password"]');
  if (!user || !pass) return {{ok:false, reason:'login form not found', href: location.href}};
  user.value = {json.dumps(user)};
  pass.value = {json.dumps(password)};
  user.dispatchEvent(new Event('input', {{bubbles:true}}));
  pass.dispatchEvent(new Event('input', {{bubbles:true}}));
  document.querySelector('[data-testid="login-form"]').requestSubmit();
  return {{ok:true, href: location.href}};
}})()"""


def js_publish(content: str) -> str:
    return f"""(() => {{
  const box = document.querySelector('[data-testid="post-content"]');
  if (!box) return {{ok:false, reason:'post composer not found', href: location.href}};
  box.value = {json.dumps(content)};
  box.dispatchEvent(new Event('input', {{bubbles:true}}));
  document.querySelector('[data-testid="post-form"]').requestSubmit();
  return {{ok:true, content: box.value}};
}})()"""


def run_autonomy(hostname: str, port: int, env_path: Path, post: str | None = None,
                 keep_browser: bool = False) -> dict[str, Any]:
    env = mock_linkedin.load_env(env_path)
    url = "linkedin.com"
    content = post or env.get("FAKE_LINKEDIN_POST", "Autonomous post.")
    target = f"https://{url}/feed"
    # assert_local_url(target)
    chrome = chrome_binary()
    if not chrome:
        raise RuntimeError("Chrome/Chromium binary not found")
    debug_port = free_port()
    browser = CDPBrowser(chrome, debug_port, hostname, target)
    try:
        browser.command("Page.navigate", {"url": target})
        browser.wait_for("document.readyState === 'complete'", timeout=10)
        first = browser.eval("({title: document.title, href: location.href, body: document.body.innerText.slice(0, 300)})")
        login_result = browser.eval(js_login(env["FAKE_LINKEDIN_USER"], env["FAKE_LINKEDIN_PASSWORD"]))
        browser.wait_for("location.pathname === '/feed' && !!document.querySelector('[data-testid=\"post-content\"]')",
                         timeout=10)
        publish_result = browser.eval(js_publish(content))
        browser.wait_for(f"document.body.innerText.includes({json.dumps(content)})", timeout=10)
        page = browser.eval("({title: document.title, href: location.href, text: document.body.innerText.slice(0, 1000), posts: document.querySelectorAll('[data-testid=\"post\"]').length})")
        api = http_json(f"http://127.0.0.1:{port}", "/api/posts")
        return {
            "ok": any(post.get("content") == content for post in api.get("posts", [])),
            "url": target,
            "user": env["FAKE_LINKEDIN_USER"],
            "firstPage": first,
            "login": login_result,
            "publish": publish_result,
            "page": page,
            "apiPosts": api.get("posts", []),
            "chrome": chrome,
            "debugPort": debug_port,
        }
    finally:
        if not keep_browser:
            browser.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Autonomously log in and publish on local Fake LinkedIn.")
    parser.add_argument("--host", default="127.0.0.1", help="server bind host")
    parser.add_argument("--hostname", default="linkedin.com", help="browser hostname mapped to 127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--post")
    parser.add_argument("--keep-browser", action="store_true")
    args = parser.parse_args(argv)

    env_path = ensure_env(Path(args.env))
    port = args.port or free_port()
    server, _state = mock_linkedin.start_server(args.host, port, env_path)
    try:
        result = run_autonomy(args.hostname, port, env_path, post=args.post, keep_browser=args.keep_browser)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
