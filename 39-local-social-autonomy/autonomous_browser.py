#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Full autonomous browser write flow, intentionally scoped to a controlled
# social-like surface. By default Chrome displays linkedin.com, but the hostname is
# mapped to 127.0.0.1 and the HTTP server is the local development target.

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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mock_linkedin


DEFAULT_ENV = HERE / ".env"
EXAMPLE_ENV = HERE / ".env.example"
DEFAULT_LOCAL_SUFFIXES = ("localhost", "127.0.0.1", "::1", ".local", ".test", ".internal", ".lan")


@dataclass
class AutonomyConfig:
    route_domain: str
    browser_scheme: str
    browser_hostname: str
    feed_path: str
    bind_host: str
    bind_port: int
    verify_host: str
    map_browser_host: bool
    host_resolver_target: str
    local_suffixes: tuple[str, ...]


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


def _split_csv(value: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default


def _env_bool(value: str, default: bool = False) -> bool:
    if not value:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(value: str, default: int = 0) -> int:
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def autonomy_config(
    env_path: str | Path = DEFAULT_ENV,
    *,
    host: str | None = None,
    hostname: str | None = None,
    port: int | None = None,
) -> AutonomyConfig:
    env = mock_linkedin.load_env(env_path)
    route_domain = env.get("SOCIAL_ROUTE_DOMAIN") or "linkedin.com"
    browser_hostname = hostname or env.get("SOCIAL_BROWSER_HOSTNAME") or route_domain
    bind_host = host or env.get("SOCIAL_BIND_HOST") or "127.0.0.1"
    verify_host = env.get("SOCIAL_VERIFY_HOST") or ("127.0.0.1" if bind_host == "0.0.0.0" else bind_host)
    bind_port = int(port if port is not None else _env_int(env.get("SOCIAL_BIND_PORT", "0"), 0))
    return AutonomyConfig(
        route_domain=route_domain,
        browser_scheme=(env.get("SOCIAL_BROWSER_SCHEME") or "http").lower(),
        browser_hostname=browser_hostname,
        feed_path="/" + (env.get("SOCIAL_FEED_PATH") or "/feed").lstrip("/"),
        bind_host=bind_host,
        bind_port=bind_port,
        verify_host=verify_host,
        map_browser_host=_env_bool(env.get("SOCIAL_MAP_BROWSER_HOST", "true"), True),
        host_resolver_target=env.get("SOCIAL_HOST_RESOLVER_TARGET") or bind_host,
        local_suffixes=_split_csv(env.get("SOCIAL_LOCAL_SUFFIXES", ",".join(DEFAULT_LOCAL_SUFFIXES)),
                                  DEFAULT_LOCAL_SUFFIXES),
    )


def route_uri(env_path: str | Path = DEFAULT_ENV) -> str:
    return f"social://{autonomy_config(env_path).route_domain}/post/command/publish"


def browser_feed_url(config: AutonomyConfig, port: int) -> str:
    if config.map_browser_host:
        netloc = config.browser_hostname
    else:
        default_port = (config.browser_scheme == "http" and port == 80) or (
            config.browser_scheme == "https" and port == 443
        )
        netloc = config.browser_hostname if default_port else f"{config.browser_hostname}:{port}"
    return urllib.parse.urlunparse((config.browser_scheme, netloc, config.feed_path, "", "", ""))


def _local_host(host: str, local_suffixes: tuple[str, ...] = DEFAULT_LOCAL_SUFFIXES) -> bool:
    host = host.lower().strip("[]")
    return any(host == item or (item.startswith(".") and host.endswith(item)) for item in local_suffixes)


def _explicit_host(host: str, allowed: tuple[str, ...] | list[str]) -> bool:
    host = host.lower().strip("[]")
    return any(host == item.lower().strip("[]") for item in allowed if item)


def assert_local_url(
    url: str,
    mapped_hosts: tuple[str, ...] | list[str] = (),
    local_suffixes: tuple[str, ...] = DEFAULT_LOCAL_SUFFIXES,
) -> None:
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if _local_host(host, local_suffixes):
        return
    if _explicit_host(host, mapped_hosts) and parsed.scheme == "http":
        return
    raise ValueError(f"refusing autonomous write flow for non-local host: {host}")


def http_json(base: str, path: str, method: str = "GET") -> Any:
    req = urllib.request.Request(base.rstrip("/") + path, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


class CDPBrowser:
    def __init__(self, chrome: str, debug_port: int, host_rule: str, resolver_target: str, start_url: str) -> None:
        self.debug_port = debug_port
        self.start_url = start_url
        self.profile = tempfile.TemporaryDirectory(prefix="fake-linkedin-cdp-")
        args = [
            chrome,
            f"--remote-debugging-port={debug_port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={self.profile.name}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        if host_rule:
            args.append(f"--host-resolver-rules=MAP {host_rule} {resolver_target}")
        args.append(start_url)
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def run_autonomy(hostname: str | None, port: int, env_path: Path, post: str | None = None,
                 keep_browser: bool = False, config: AutonomyConfig | None = None) -> dict[str, Any]:
    env = mock_linkedin.load_env(env_path)
    config = config or autonomy_config(env_path, hostname=hostname, port=port)
    content = post or env.get("FAKE_LINKEDIN_POST", "Autonomous post.")
    target = browser_feed_url(config, port)
    mapped_hosts = (config.browser_hostname,) if config.map_browser_host else ()
    assert_local_url(target, mapped_hosts=mapped_hosts, local_suffixes=config.local_suffixes)
    chrome = chrome_binary()
    if not chrome:
        raise RuntimeError("Chrome/Chromium binary not found")
    debug_port = free_port()
    host_rule = config.browser_hostname if config.map_browser_host else ""
    resolver_target = f"{config.host_resolver_target}:{port}" if config.map_browser_host else config.host_resolver_target
    browser = CDPBrowser(chrome, debug_port, host_rule, resolver_target, target)
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
        api = http_json(f"http://{config.verify_host}:{port}", "/api/posts")
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
    parser = argparse.ArgumentParser(description="Autonomously log in and publish on the configured controlled social site.")
    parser.add_argument("--host", help="server bind host; defaults to 127.0.0.1")
    parser.add_argument("--hostname", help="browser hostname; defaults to SOCIAL_BROWSER_HOSTNAME from .env")
    parser.add_argument("--port", type=int, help="server bind port; defaults to a free port")
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--post")
    parser.add_argument("--keep-browser", action="store_true")
    args = parser.parse_args(argv)

    env_path = ensure_env(Path(args.env))
    config = autonomy_config(env_path, host=args.host, hostname=args.hostname, port=args.port)
    port = config.bind_port or free_port()
    server, _state = mock_linkedin.start_server(config.bind_host, port, env_path)
    try:
        result = run_autonomy(config.browser_hostname, port, env_path, post=args.post,
                              keep_browser=args.keep_browser, config=config)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
