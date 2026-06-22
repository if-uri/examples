#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# NL planner and URI handlers for the local portals suite. It reuses the local Chrome
# CDP driver from example 39 and exposes typed portal:// command routes.

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
EX39 = HERE.parent / "39-local-social-autonomy"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EX39))

import autonomous_browser as cdp
import portal_server


DEFAULT_ENV = HERE / ".env"
EXAMPLE_ENV = HERE / ".env.example"

ROUTES = {
    "crm": "portal://crm.local/lead/command/create",
    "support": "portal://support.local/ticket/command/create",
    "shop": "portal://shop.local/order/command/create",
    "docs": "portal://docs.local/doc/command/create",
}


def ensure_env(path: str | Path = DEFAULT_ENV) -> Path:
    env_path = Path(path)
    if env_path.exists():
        return env_path
    if env_path == DEFAULT_ENV and EXAMPLE_ENV.exists():
        env_path.write_text(EXAMPLE_ENV.read_text(encoding="utf-8"), encoding="utf-8")
        return env_path
    raise FileNotFoundError(env_path)


def _api_json(port: int, host: str, path: str = "/api/records") -> dict[str, Any]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers={"Host": host}, method="GET")
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _js_login(user: str, password: str) -> str:
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


def _js_submit(fields: dict[str, Any]) -> str:
    return f"""(() => {{
  const values = {json.dumps(fields, ensure_ascii=False)};
  const form = document.querySelector('[data-testid="action-form"]');
  if (!form) return {{ok:false, reason:'action form not found', href: location.href}};
  for (const [key, value] of Object.entries(values)) {{
    const el = document.querySelector(`[data-testid="${{key}}"]`);
    if (!el) return {{ok:false, reason:`field ${{key}} not found`, href: location.href}};
    el.value = String(value);
    el.dispatchEvent(new Event('input', {{bubbles:true}}));
  }}
  form.requestSubmit();
  return {{ok:true, fields: values}};
}})()"""


def env_defaults(portal: str, env: dict[str, str]) -> dict[str, Any]:
    if portal == "crm":
        return {"customer": env.get("CRM_CUSTOMER", "Acme Local"),
                "note": env.get("CRM_NOTE", "Lead created by local autonomous browser test.")}
    if portal == "support":
        return {"title": env.get("SUPPORT_TITLE", "Local support ticket"),
                "message": env.get("SUPPORT_MESSAGE", "Ticket created by local autonomous browser test.")}
    if portal == "shop":
        return {"product": env.get("SHOP_PRODUCT", "URI Test Subscription"),
                "qty": int(env.get("SHOP_QTY", "1") or "1")}
    if portal == "docs":
        return {"title": env.get("DOCS_TITLE", "Local automation note"),
                "body": env.get("DOCS_BODY", "Document created by local autonomous browser test.")}
    raise ValueError(f"unknown portal: {portal}")


def run_portal_action(portal: str, fields: dict[str, Any], env: str = "", keep_browser: bool = False) -> dict[str, Any]:
    if portal not in portal_server.PORTALS:
        raise ValueError(f"unknown portal: {portal}")
    env_path = ensure_env(Path(env) if env else DEFAULT_ENV)
    env_data = portal_server.load_env(env_path)
    payload = {**env_defaults(portal, env_data), **{k: v for k, v in fields.items() if v not in (None, "")}}
    bind_port = cdp.free_port()
    server, _state = portal_server.start_server("127.0.0.1", bind_port, env_path)
    host = portal_server.PORTALS[portal]["host"]
    target = f"http://{host}:{bind_port}/dashboard"
    cdp.assert_local_url(target)
    chrome = cdp.chrome_binary()
    if not chrome:
        raise RuntimeError("Chrome/Chromium binary not found")
    browser = cdp.CDPBrowser(chrome, cdp.free_port(), host, target)
    try:
        browser.command("Page.navigate", {"url": target})
        browser.wait_for("document.readyState === 'complete'", timeout=10)
        first = browser.eval("({title: document.title, href: location.href, text: document.body.innerText.slice(0, 300)})")
        login = browser.eval(_js_login(env_data["PORTAL_USER"], env_data["PORTAL_PASSWORD"]))
        browser.wait_for("location.pathname === '/dashboard' && !!document.querySelector('[data-testid=\"action-form\"]')",
                         timeout=10)
        submit = browser.eval(_js_submit(payload))
        probe_value = next((str(v) for v in payload.values() if str(v).strip()), "")
        browser.wait_for(f"document.body.innerText.includes({json.dumps(probe_value)})", timeout=10)
        page = browser.eval("({title: document.title, href: location.href, text: document.body.innerText.slice(0, 1200), records: document.querySelectorAll('[data-testid=\"record\"]').length})")
        api = _api_json(bind_port, host)
        return {
            "ok": bool(api.get("records")),
            "portal": portal,
            "url": target,
            "user": env_data["PORTAL_USER"],
            "payload": payload,
            "firstPage": first,
            "login": login,
            "submit": submit,
            "page": page,
            "records": api.get("records", []),
        }
    finally:
        if not keep_browser:
            try:
                browser.close()
            except OSError:
                pass
        server.shutdown()


def create_crm_lead(customer: str = "", note: str = "", env: str = "", keep_browser: bool = False) -> dict[str, Any]:
    return run_portal_action("crm", {"customer": customer, "note": note}, env=env, keep_browser=keep_browser)


def create_support_ticket(title: str = "", message: str = "", env: str = "", keep_browser: bool = False) -> dict[str, Any]:
    return run_portal_action("support", {"title": title, "message": message}, env=env, keep_browser=keep_browser)


def create_shop_order(product: str = "", qty: int = 1, env: str = "", keep_browser: bool = False) -> dict[str, Any]:
    return run_portal_action("shop", {"product": product, "qty": int(qty or 1)}, env=env, keep_browser=keep_browser)


def create_docs_document(title: str = "", body: str = "", env: str = "", keep_browser: bool = False) -> dict[str, Any]:
    return run_portal_action("docs", {"title": title, "body": body}, env=env, keep_browser=keep_browser)


def choose_portal(goal: str) -> str:
    text = goal.lower()
    if any(word in text for word in ("support", "ticket", "zgłosz", "zglosz", "zgłoszenie", "zgloszenie")):
        return "support"
    if any(word in text for word in ("shop", "sklep", "order", "zamów", "zamow", "produkt")):
        return "shop"
    if any(word in text for word in ("docs", "doc", "dokument", "notat", "wiki")):
        return "docs"
    return "crm"


def _quoted_or_tail(goal: str) -> str:
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', goal)
    if quoted:
        return (quoted.group(1) or quoted.group(2)).strip()
    marker = re.search(r"(?:lead|klient|ticket|zgłoszenie|zgloszenie|order|zamówienie|zamowienie|doc|dokument|post|treść|tresc|content)\s*:\s*(.+)$",
                       goal, flags=re.I)
    if marker:
        return marker.group(1).strip()
    words = " ".join(goal.split())
    return words[-80:] if words else ""


def payload_for_goal(portal: str, goal: str) -> dict[str, Any]:
    text = _quoted_or_tail(goal) or "Local autonomous test"
    if portal == "crm":
        return {"customer": text, "note": f"NL goal: {goal}"}
    if portal == "support":
        return {"title": text, "message": f"NL goal: {goal}"}
    if portal == "shop":
        qty_match = re.search(r"(?:qty|ilość|ilosc|x)\s*[:= ]\s*(\d+)", goal, flags=re.I)
        return {"product": text, "qty": int(qty_match.group(1)) if qty_match else 1}
    if portal == "docs":
        return {"title": text[:80], "body": f"NL goal: {goal}"}
    return {}


def planner(goal: str, action_space: list[dict[str, Any]]) -> list[dict[str, Any]]:
    portal = choose_portal(goal)
    wanted = ROUTES[portal]
    route = next((item["uri"] for item in action_space if item.get("uri") == wanted), wanted)
    return [{"uri": route, "payload": payload_for_goal(portal, goal),
             "why": f"NL prompt targets the local {portal} portal"}]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a local portal action from an NL prompt.")
    parser.add_argument("prompt", nargs="+")
    args = parser.parse_args(argv)
    goal = " ".join(args.prompt)
    portal = choose_portal(goal)
    result = run_portal_action(portal, payload_for_goal(portal, goal))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
