from __future__ import annotations

from pathlib import Path

import session_probe


def test_parse_endpoints_reads_named_urls_from_env(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text(
        "LI_CDP_ENDPOINTS=chrome=http://127.0.0.1:9222,brave=http://127.0.0.1:9223\n",
        encoding="utf-8",
    )
    endpoints = session_probe.parse_endpoints(env_path=env)
    assert [(item.label, item.base) for item in endpoints] == [
        ("chrome", "http://127.0.0.1:9222"),
        ("brave", "http://127.0.0.1:9223"),
    ]


def test_parse_endpoints_falls_back_to_debug_ports(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("LI_DEBUG_PORTS=9444,9555\n", encoding="utf-8")
    endpoints = session_probe.parse_endpoints(env_path=env)
    assert [(item.label, item.base) for item in endpoints] == [
        ("cdp-9444", "http://127.0.0.1:9444"),
        ("cdp-9555", "http://127.0.0.1:9555"),
    ]


def test_safe_tabs_reports_linkedin_login_likely():
    tabs = [
        {"type": "page", "title": "Login", "url": "https://www.linkedin.com/login/?session_redirect=x"},
        {"type": "page", "title": "Feed", "url": "https://www.linkedin.com/feed/"},
        {"type": "page", "title": "Other", "url": "https://example.com/"},
    ]
    out = session_probe._safe_tabs(tabs)
    assert [item["title"] for item in out] == ["Login", "Feed"]
    assert out[0]["loginLikely"] is True
    assert out[1]["loginLikely"] is False


def test_probe_endpoint_detects_li_at_cookie_without_value(monkeypatch):
    def fake_http_json(base, path, timeout=2.0):
        if path == "/json/version":
            return {"Browser": "Chrome/150", "Protocol-Version": "1.3"}
        if path == "/json":
            return [{
                "type": "page",
                "title": "LinkedIn Feed",
                "url": "https://www.linkedin.com/feed/",
                "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/page/1",
            }]
        raise AssertionError(path)

    def fake_ws_command(ws_url, method, params=None, timeout=4.0):
        return {"result": {"cookies": [
            {"name": "li_at", "value": "secret-auth-cookie"},
            {"name": "JSESSIONID", "value": "secret-session"},
        ]}}

    monkeypatch.setattr(session_probe, "_http_json", fake_http_json)
    monkeypatch.setattr(session_probe, "_ws_command", fake_ws_command)

    result = session_probe.probe_endpoint(session_probe.CDPEndpoint("chrome", "http://127.0.0.1:9222"))
    assert result["hasLinkedInSession"] is True
    assert result["sessionCookieNames"] == ["li_at"]
    assert "secret-auth-cookie" not in str(result)
    assert result["linkedinTabCount"] == 1


def test_binding_document_exposes_query_route():
    doc = session_probe.binding_document()
    assert list(doc["bindings"]) == [session_probe.ROUTE]
    binding = doc["bindings"][session_probe.ROUTE]
    assert binding["kind"] == "query"
    assert binding["policy"]["allowExecute"] is False
