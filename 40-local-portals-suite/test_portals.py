from __future__ import annotations

import http.cookiejar
import json
import socket
import urllib.parse
import urllib.request
from pathlib import Path

import portal_autonomy
import portal_server


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def env_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env"
    path.write_text(
        "PORTAL_USER=agent@example.local\n"
        "PORTAL_PASSWORD=secret\n"
        "PORTAL_NAME=Agent Local\n"
        "CRM_CUSTOMER=Fallback Customer\n",
        encoding="utf-8",
    )
    return path


def test_load_env_reads_portal_credentials(tmp_path):
    env = portal_server.load_env(env_file(tmp_path))
    assert env["PORTAL_USER"] == "agent@example.local"
    assert env["PORTAL_PASSWORD"] == "secret"


def test_server_login_and_create_crm_record(tmp_path):
    env = env_file(tmp_path)
    port = free_port()
    server, state = portal_server.start_server("127.0.0.1", port, env)
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    base = f"http://127.0.0.1:{port}"
    headers = {"Host": "crm.local"}
    try:
        login = urllib.parse.urlencode({"username": state.user, "password": state.password}).encode()
        opener.open(urllib.request.Request(base + "/login", data=login, headers=headers), timeout=5).read()
        form = urllib.parse.urlencode({"customer": "Acme", "note": "test"}).encode()
        opener.open(urllib.request.Request(base + "/action", data=form, headers=headers), timeout=5).read()
        raw = opener.open(urllib.request.Request(base + "/api/records", headers=headers), timeout=5).read()
        data = json.loads(raw.decode())
        assert data["records"][0]["fields"]["customer"] == "Acme"
    finally:
        server.shutdown()


def test_choose_portal_from_nl():
    assert portal_autonomy.choose_portal("utwórz lead dla klienta") == "crm"
    assert portal_autonomy.choose_portal("zgłoszenie support") == "support"
    assert portal_autonomy.choose_portal("zamów produkt") == "shop"
    assert portal_autonomy.choose_portal("stwórz dokument") == "docs"


def test_planner_maps_goal_to_route():
    steps = portal_autonomy.planner("support: zgłoszenie \"Nie działa\"", [{"uri": portal_autonomy.ROUTES["support"]}])
    assert steps[0]["uri"] == portal_autonomy.ROUTES["support"]
    assert steps[0]["payload"]["title"] == "Nie działa"


def test_payload_for_shop_extracts_quantity():
    payload = portal_autonomy.payload_for_goal("shop", "zamów produkt \"Plan testowy\" qty 3")
    assert payload["product"] == "Plan testowy"
    assert payload["qty"] == 3
