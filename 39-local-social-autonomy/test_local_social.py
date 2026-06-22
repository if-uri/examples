from __future__ import annotations

import http.cookiejar
import socket
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import autonomous_browser as auto
import mock_linkedin


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def env_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env"
    path.write_text(
        "FAKE_LINKEDIN_USER=agent@example.local\n"
        "FAKE_LINKEDIN_PASSWORD=secret\n"
        "FAKE_LINKEDIN_NAME=Agent Smith\n"
        "FAKE_LINKEDIN_POST=hello from env\n",
        encoding="utf-8",
    )
    return path


def test_load_env_reads_fake_credentials(tmp_path):
    env = mock_linkedin.load_env(env_file(tmp_path))
    assert env["FAKE_LINKEDIN_USER"] == "agent@example.local"
    assert env["FAKE_LINKEDIN_PASSWORD"] == "secret"


def test_mock_server_login_and_post(tmp_path):
    env = env_file(tmp_path)
    port = free_port()
    server, state = mock_linkedin.start_server("127.0.0.1", port, env)
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base = f"http://127.0.0.1:{port}"
    try:
        login = urllib.parse.urlencode({"username": state.user, "password": state.password}).encode()
        opener.open(base + "/login", data=login, timeout=5).read()
        post = urllib.parse.urlencode({"content": "local autonomous post"}).encode()
        opener.open(base + "/post", data=post, timeout=5).read()
        api = opener.open(base + "/api/posts", timeout=5).read().decode()
        assert "local autonomous post" in api
    finally:
        server.shutdown()


def test_autonomous_write_scope_rejects_public_host():
    try:
        auto.assert_local_url("https://www.linkedin.com/feed/")
    except ValueError as exc:
        assert "non-local host" in str(exc)
    else:
        raise AssertionError("public host should be rejected")


def test_autonomous_write_scope_allows_linkedin_local():
    auto.assert_local_url("http://linkedin.local:8080/feed")


def test_js_helpers_embed_values_safely():
    login = auto.js_login("a@example.local", "p'\"<")
    publish = auto.js_publish("hello </script>")
    assert "a@example.local" in login
    assert "hello" in publish
