#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Read-only LinkedIn session probe. It does not launch a browser, type, click, or
# navigate. It scans existing Chrome DevTools Protocol endpoints and reports which
# already-running browser/profile has a LinkedIn session cookie.

from __future__ import annotations

import argparse
import base64
import json
import os
import socket
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import mock_linkedin
from websocket_frames import recv_json, send_text


DEFAULT_ENV = HERE / ".env"
ROUTE = "browser://local/linkedin/session/query/find"
LINKEDIN_URL = "https://www.linkedin.com/"


@dataclass(frozen=True)
class CDPEndpoint:
    label: str
    base: str


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _base_from_port(port: str | int) -> str:
    return f"http://127.0.0.1:{int(port)}"


def parse_endpoints(endpoints: str = "", debug_ports: str = "", env_path: str | Path = DEFAULT_ENV) -> list[CDPEndpoint]:
    """Parse endpoint config from payload or .env.

    Accepted endpoint forms:
    - `chrome=http://127.0.0.1:9222`
    - `http://127.0.0.1:9222`
    - `chrome:9222`
    """
    env = mock_linkedin.load_env(env_path)
    raw_endpoints = endpoints or env.get("LI_CDP_ENDPOINTS", "")
    out: list[CDPEndpoint] = []
    for index, item in enumerate(_split_csv(raw_endpoints), 1):
        label = f"cdp-{index}"
        value = item
        if "=" in item:
            label, value = [part.strip() for part in item.split("=", 1)]
        elif ":" in item and not item.startswith(("http://", "https://")):
            label, value = [part.strip() for part in item.split(":", 1)]
        base = value if value.startswith(("http://", "https://")) else _base_from_port(value)
        out.append(CDPEndpoint(label or f"cdp-{index}", base.rstrip("/")))

    if out:
        return out

    ports = debug_ports or env.get("LI_DEBUG_PORTS") or env.get("LI_DEBUG_PORT") or "9222"
    return [CDPEndpoint(f"cdp-{port}", _base_from_port(port)) for port in _split_csv(ports)]


def _http_json(base: str, path: str, timeout: float = 2.0) -> Any:
    req = urllib.request.Request(base.rstrip("/") + path)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _ws_command(ws_url: str, method: str, params: dict[str, Any] | None = None, timeout: float = 4.0) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(ws_url)
    sock = socket.create_connection((parsed.hostname, parsed.port), timeout=timeout)
    try:
        key = base64.b64encode(os.urandom(16)).decode()
        sock.sendall((f"GET {parsed.path} HTTP/1.1\r\n"
                      f"Host: {parsed.hostname}:{parsed.port}\r\n"
                      "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                      f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += sock.recv(4096)
        msg_id = 1
        send_text(sock, json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            message = recv_json(sock)
            if message.get("id") == msg_id:
                return message
    finally:
        sock.close()


def _safe_tabs(tabs: Any) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for tab in tabs if isinstance(tabs, list) else []:
        if tab.get("type") != "page":
            continue
        url = str(tab.get("url") or "")
        if "linkedin.com" not in url.lower():
            continue
        parsed = urllib.parse.urlparse(url)
        path = parsed.path or "/"
        out.append({
            "title": str(tab.get("title") or "")[:160],
            "url": url,
            "loginLikely": str(path).startswith("/login") or "session_redirect" in parsed.query,
        })
    return out


def probe_endpoint(endpoint: CDPEndpoint, cookie_names: tuple[str, ...] = ("li_at",)) -> dict[str, Any]:
    try:
        version = _http_json(endpoint.base, "/json/version")
        tabs = _http_json(endpoint.base, "/json")
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "label": endpoint.label,
            "endpoint": endpoint.base,
            "reachable": False,
            "error": str(exc),
        }

    pages = [tab for tab in tabs if isinstance(tab, dict) and tab.get("type") == "page" and tab.get("webSocketDebuggerUrl")]
    cookie_result: dict[str, Any] = {"result": {"cookies": []}}
    if pages:
        try:
            cookie_result = _ws_command(
                str(pages[0]["webSocketDebuggerUrl"]),
                "Network.getCookies",
                {"urls": [LINKEDIN_URL]},
            )
        except Exception as exc:  # noqa: BLE001
            cookie_result = {"error": str(exc), "result": {"cookies": []}}

    cookies = (cookie_result.get("result") or {}).get("cookies") or []
    present = sorted({str(cookie.get("name")) for cookie in cookies if cookie.get("name") in cookie_names})
    linkedin_tabs = _safe_tabs(tabs)
    has_session = bool(present)
    return {
        "ok": True,
        "label": endpoint.label,
        "endpoint": endpoint.base,
        "reachable": True,
        "browser": version.get("Browser"),
        "protocol": version.get("Protocol-Version"),
        "hasLinkedInSession": has_session,
        "sessionCookieNames": present,
        "linkedinTabs": linkedin_tabs,
        "linkedinTabCount": len(linkedin_tabs),
        "reason": "li_at cookie present" if has_session else "no LinkedIn session cookie found",
    }


def find_linkedin_session(
    env: str = "",
    endpoints: str = "",
    debug_ports: str = "",
    cookie_names: str = "li_at",
) -> dict[str, Any]:
    env_path = Path(env) if env else DEFAULT_ENV
    wanted_cookies = tuple(_split_csv(cookie_names or "li_at")) or ("li_at",)
    candidates = [probe_endpoint(endpoint, wanted_cookies) for endpoint in parse_endpoints(endpoints, debug_ports, env_path)]
    selected = next((item for item in candidates if item.get("hasLinkedInSession")), None)
    return {
        "ok": True,
        "found": selected is not None,
        "selected": selected,
        "candidates": candidates,
        "route": ROUTE,
    }


def binding_document() -> dict[str, Any]:
    return {
        "version": "urirun.bindings.v2",
        "bindings": {
            ROUTE: {
                "kind": "query",
                "adapter": "local-function",
                "ref": "session_probe:find_linkedin_session",
                "python": {"type": "python", "module": "session_probe", "export": "find_linkedin_session"},
                "inputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "env": {"type": "string", "default": ""},
                        "endpoints": {"type": "string", "default": "", "description": "CSV: chrome=http://127.0.0.1:9222,brave=http://127.0.0.1:9223"},
                        "debug_ports": {"type": "string", "default": "", "description": "CSV fallback: 9222,9223"},
                        "cookie_names": {"type": "string", "default": "li_at"},
                    },
                },
                "policy": {"allowExecute": False},
                "meta": {
                    "label": "Find an existing browser with a LinkedIn session",
                    "description": "Read-only CDP probe; does not launch, navigate, type, click, or expose cookie values.",
                },
            }
        },
    }


def write_bindings(path: str | Path) -> None:
    Path(path).write_text(json.dumps(binding_document(), indent=2, ensure_ascii=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find which existing CDP browser has a LinkedIn session.")
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--endpoints", default="")
    parser.add_argument("--debug-ports", default="")
    parser.add_argument("--cookie-names", default="li_at")
    parser.add_argument("--write-bindings")
    args = parser.parse_args(argv)
    if args.write_bindings:
        write_bindings(args.write_bindings)
        return 0
    result = find_linkedin_session(args.env, args.endpoints, args.debug_ports, args.cookie_names)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
