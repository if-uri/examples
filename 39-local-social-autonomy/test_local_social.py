from __future__ import annotations

import http.cookiejar
import socket
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import autonomous_browser as auto
import mock_linkedin
import nl_autonomy


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


def env_file_with_social_config(tmp_path: Path) -> Path:
    path = env_file(tmp_path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(
            "SOCIAL_ROUTE_DOMAIN=linkjedin.example\n"
            "SOCIAL_BROWSER_SCHEME=http\n"
            "SOCIAL_BROWSER_HOSTNAME=linkjedin.example\n"
            "SOCIAL_FEED_PATH=/custom-feed\n"
            "SOCIAL_BIND_HOST=127.0.0.1\n"
            "SOCIAL_BIND_PORT=8088\n"
            "SOCIAL_VERIFY_HOST=127.0.0.1\n"
            "SOCIAL_MAP_BROWSER_HOST=true\n"
            "SOCIAL_HOST_RESOLVER_TARGET=127.0.0.1\n"
            "SOCIAL_LOCAL_SUFFIXES=localhost,127.0.0.1,.example\n"
        )
    return path


def test_load_env_reads_fake_credentials(tmp_path):
    env = mock_linkedin.load_env(env_file(tmp_path))
    assert env["FAKE_LINKEDIN_USER"] == "agent@example.local"
    assert env["FAKE_LINKEDIN_PASSWORD"] == "secret"


def test_autonomy_config_reads_domain_and_host_values_from_env(tmp_path):
    env = env_file_with_social_config(tmp_path)
    config = auto.autonomy_config(env)
    assert config.route_domain == "linkjedin.example"
    assert config.browser_hostname == "linkjedin.example"
    assert config.feed_path == "/custom-feed"
    assert config.bind_host == "127.0.0.1"
    assert config.bind_port == 8088
    assert config.verify_host == "127.0.0.1"
    assert config.host_resolver_target == "127.0.0.1"
    assert ".example" in config.local_suffixes
    assert auto.route_uri(env) == "social://linkjedin.example/post/command/publish"
    assert auto.browser_feed_url(config, 8088) == "http://linkjedin.example/custom-feed"
    config.map_browser_host = False
    assert auto.browser_feed_url(config, 8088) == "http://linkjedin.example:8088/custom-feed"


def test_binding_document_uses_env_domain_and_defaults(tmp_path):
    env = env_file_with_social_config(tmp_path)
    doc = nl_autonomy.binding_document(env)
    route = "social://linkjedin.example/post/command/publish"
    assert list(doc["bindings"]) == [route]
    props = doc["bindings"][route]["inputSchema"]["properties"]
    assert "hostname" not in props
    assert "host" not in props
    assert props["port"]["default"] == 8088


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


def test_autonomous_write_scope_allows_local_dev_suffix():
    auto.assert_local_url("http://portal.local:8080/feed")


def test_autonomous_write_scope_allows_explicit_mapped_linkedin_com():
    auto.assert_local_url("http://linkedin.com:8080/feed", mapped_hosts=("linkedin.com",))


def test_autonomous_write_scope_rejects_unmapped_linkedin_com():
    try:
        auto.assert_local_url("http://linkedin.com/feed")
    except ValueError as exc:
        assert "non-local host" in str(exc)
    else:
        raise AssertionError("public-looking host should require an explicit local mapping")


def test_autonomous_write_scope_rejects_real_https_linkedin_even_when_mapped():
    try:
        auto.assert_local_url("https://linkedin.com/feed", mapped_hosts=("linkedin.com",))
    except ValueError as exc:
        assert "non-local host" in str(exc)
    else:
        raise AssertionError("real https LinkedIn should not be accepted by the local write scope")


def test_js_helpers_embed_values_safely():
    login = auto.js_login("a@example.local", "p'\"<")
    publish = auto.js_publish("hello </script>")
    assert "a@example.local" in login
    assert "hello" in publish


def test_nl_extracts_quoted_post():
    assert nl_autonomy.extract_post('opublikuj "tekst testowy"', env_file(Path(tempfile.mkdtemp()))) == "tekst testowy"


def test_nl_planner_returns_social_publish_step():
    steps = nl_autonomy.planner("opublikuj post: lokalny test", [{"uri": nl_autonomy.ROUTE}])
    assert steps == [{
        "uri": nl_autonomy.ROUTE,
        "payload": {"post": "lokalny test"},
        "why": "NL prompt asks for a controlled social publication",
    }]
