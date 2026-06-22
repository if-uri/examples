#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Unattended browser observation runner. It may inspect the physical screen (KVM/OCR)
# and read/navigate pages over CDP, but it refuses external social actions such as
# posting, sending messages, commenting, logging in, purchases, and password entry.

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from urirun.node.client import NodeClient

DEFAULT_NODE_URL = os.environ.get("NODE_URL", "http://192.168.188.201:8766")
DEFAULT_NODE = os.environ.get("NODE", "laptop")
DEFAULT_DEV_HOSTS = ("localhost", "127.0.0.1", "::1", ".local", ".test", ".internal", ".lan")
PUBLIC_SOCIAL_HOSTS = ("linkedin.com", "www.linkedin.com")

BLOCKED_PATTERNS = [
    r"\bpost\b", r"\bpublish\b", r"\bsend\b", r"\bmessage\b", r"\bcomment\b",
    r"\breply\b", r"\bconnect\b", r"\bfollow\b", r"\blike\b", r"\breact\b",
    r"\bshare\b", r"\blog\s*in\b", r"\bsign\s*in\b", r"\bpassword\b",
    r"\bcheckout\b", r"\bpurchase\b", r"\bbuy\b",
    r"\bopublikuj\b", r"\bpublikuj\b", r"\bwyślij\b", r"\bwyslij\b",
    r"\bwiadomość\b", r"\bwiadomosc\b", r"\bkomentarz\b", r"\bkomentuj\b",
    r"\bodpisz\b", r"\bzaloguj\b", r"\bhasło\b", r"\bhaslo\b",
]


def _host_matches(host: str, allowed: list[str] | tuple[str, ...]) -> bool:
    host = host.lower().strip("[]")
    for item in allowed:
        item = item.lower().strip()
        if not item:
            continue
        if item.startswith(".") and host.endswith(item):
            return True
        if host == item:
            return True
    return False


def _target_host(url: str | None) -> str:
    return (urlparse(url or "").hostname or "").lower()


def policy_for_goal(
    goal: str,
    target_url: str | None = None,
    *,
    dev_allow_write_actions: bool = False,
    dev_allowed_hosts: list[str] | tuple[str, ...] = DEFAULT_DEV_HOSTS,
) -> dict[str, Any]:
    hits = [pat for pat in BLOCKED_PATTERNS if re.search(pat, goal, flags=re.I)]
    host = _target_host(target_url)
    public_social = bool(host and _host_matches(host, PUBLIC_SOCIAL_HOSTS))
    dev_allowed = bool(host and _host_matches(host, dev_allowed_hosts))
    if hits and dev_allow_write_actions and dev_allowed and not public_social:
        return {
            "ok": True,
            "mode": "dev-unattended-with-write-actions",
            "blockedPatterns": [],
            "detectedWritePatterns": hits,
            "targetHost": host,
            "devAllowedHosts": list(dev_allowed_hosts),
            "reason": "dev override enabled for an allowlisted non-public host",
        }
    return {
        "ok": not hits,
        "mode": "read-only-unattended",
        "blockedPatterns": hits,
        "detectedWritePatterns": hits,
        "targetHost": host,
        "devAllowedHosts": list(dev_allowed_hosts),
        "reason": None if not hits else "unattended mode refuses external write/social/login actions",
    }


def route_uris(client: NodeClient) -> set[str]:
    return {str(r.get("uri", "")) for r in client.routes()}


def run(client: NodeClient, uri: str, payload: dict | None = None, timeout: float = 30.0) -> dict:
    try:
        return client.run(uri, payload or {}, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "uri": uri}


def value(env: dict) -> Any:
    return NodeClient.value(env) if isinstance(env, dict) else env


def infer_url(goal: str, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    m = re.search(r"https?://\S+", goal)
    if m:
        return m.group(0).rstrip(".,)")
    if re.search(r"linkedin", goal, flags=re.I):
        return "https://www.linkedin.com/feed/"
    return None


def summarize_page(data: dict) -> dict:
    text = str(data.get("text") or "")
    href = str(data.get("href") or "")
    title = str(data.get("title") or "")
    return {
        "title": title,
        "href": href,
        "hasLogin": bool(re.search(r"sign in|login|zaloguj", text, flags=re.I)),
        "hasLinkedIn": "linkedin" in (href + " " + title + " " + text).lower(),
        "snippet": text[:700],
    }


def observe_physical_screen(client: NodeClient, node: str, routes: set[str], contains: str) -> dict:
    uri = f"browser://{node}/kvm/screen/query/inspect"
    if uri not in routes:
        return {"ok": False, "available": False, "reason": "kvm screen inspect route is not served"}
    env = run(client, uri, {"contains": contains}, timeout=30)
    data = value(env)
    return {"ok": bool(env.get("ok")), "available": True, "envOk": env.get("ok"), "data": data}


def observe_cdp(client: NodeClient, node: str, routes: set[str], url: str | None) -> dict:
    tabs_uri = f"browser://{node}/cdp/page/query/tabs"
    eval_uri = f"browser://{node}/cdp/page/query/eval"
    nav_uri = f"browser://{node}/cdp/page/command/navigate"
    if tabs_uri not in routes or eval_uri not in routes:
        return {"ok": False, "available": False, "reason": "cdp routes are not served"}
    actions: list[dict] = []
    if url and nav_uri in routes:
        actions.append({"action": "navigate", "url": url, "result": value(run(client, nav_uri, {"url": url}, timeout=30))})
        time.sleep(3)
    expr = (
        "(() => ({title: document.title, href: location.href, "
        "text: document.body ? document.body.innerText.slice(0, 2000) : ''}))()"
    )
    page_env = run(client, eval_uri, {"expr": expr}, timeout=20)
    page = value(page_env)
    if isinstance(page, dict) and isinstance(page.get("value"), dict):
        page = page["value"]
    tabs = value(run(client, tabs_uri, {}, timeout=10))
    return {
        "ok": bool(page_env.get("ok")),
        "available": True,
        "actions": actions,
        "page": summarize_page(page if isinstance(page, dict) else {}),
        "tabs": tabs.get("tabs", []) if isinstance(tabs, dict) else [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unattended read-only browser observation with KVM/OCR-first detection.")
    parser.add_argument("goal", nargs="+")
    parser.add_argument("--node-url", default=DEFAULT_NODE_URL)
    parser.add_argument("--node", default=DEFAULT_NODE)
    parser.add_argument("--url", help="optional page to navigate/read; inferred from goal when omitted")
    parser.add_argument("--unattended", action="store_true", help="run without prompts, read-only only")
    parser.add_argument("--dev-allow-write-actions", action="store_true",
                        help="allow write/social/password-like actions only on allowlisted dev hosts, never public social sites")
    parser.add_argument("--dev-allow-host", action="append", default=[],
                        help="extra dev host allowed for --dev-allow-write-actions; exact host or suffix like .test")
    args = parser.parse_args(argv)

    goal = " ".join(args.goal)
    client = NodeClient(args.node_url)
    routes = route_uris(client)
    url = infer_url(goal, args.url)
    dev_hosts = [*DEFAULT_DEV_HOSTS, *args.dev_allow_host]
    policy = policy_for_goal(goal, url, dev_allow_write_actions=args.dev_allow_write_actions,
                             dev_allowed_hosts=dev_hosts)
    physical = observe_physical_screen(client, args.node, routes, contains="LinkedIn" if "linkedin" in goal.lower() else "")
    result = {
        "ok": True,
        "goal": goal,
        "node": {"name": client.name, "url": args.node_url, "routeCount": len(routes)},
        "policy": policy,
        "observations": {"physicalScreen": physical},
        "actions": [],
    }
    if not args.unattended:
        result["ok"] = False
        result["blocked"] = True
        result["reason"] = "pass --unattended to run the read-only unattended path"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2
    if policy["ok"]:
        cdp = observe_cdp(client, args.node, routes, url)
        result["observations"]["cdp"] = cdp
        result["actions"].append({"type": "read-only-navigation", "url": url, "ok": cdp.get("ok")})
    else:
        result["ok"] = False
        result["blocked"] = True
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
