# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# WordPress as a URI — create an article on your own blog via the WordPress REST API,
# the proper automation path: authenticate with an Application Password (NOT your login
# password; create one in WP admin → Users → Profile → Application Passwords). The
# credential is read BY REFERENCE from the environment (WP_APP_PASSWORD) — this code
# never asks for or stores it, and on a urirun node you'd back it with secret://.
#
# Defaults to status="draft": nothing is published. The article lands in WP admin for
# you to review and publish. Publishing is a deliberate status="publish" you opt into.

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request


def _auth_header() -> tuple[str, str] | dict:
    url = (os.environ.get("WP_URL") or "").rstrip("/")
    user = os.environ.get("WP_USER")
    app_pw = os.environ.get("WP_APP_PASSWORD")  # WordPress Application Password, by reference
    if not (url and user and app_pw):
        return {"error": "set WP_URL, WP_USER and WP_APP_PASSWORD (an Application Password from "
                         "WP admin → Users → Application Passwords) — never your login password"}
    token = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    return url, token


def create_post(title: str = "", content: str = "", status: str = "draft",
                excerpt: str = "", categories: str = "", **_p) -> dict:
    """Create a post via /wp-json/wp/v2/posts. status defaults to 'draft' (private until
    you publish it). Use status='publish' only deliberately — that makes it public."""
    if not title and not content:
        return {"ok": False, "error": "title or content is required"}
    auth = _auth_header()
    if isinstance(auth, dict):
        return {"ok": False, **auth}
    url, token = auth
    payload: dict = {"title": title, "content": content, "status": status}
    if excerpt:
        payload["excerpt"] = excerpt
    if categories:
        payload["categories"] = [int(c) for c in str(categories).split(",") if c.strip().isdigit()]
    req = urllib.request.Request(f"{url}/wp-json/wp/v2/posts", data=json.dumps(payload).encode(),
                                 method="POST", headers={"Content-Type": "application/json",
                                                         "Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "id": data.get("id"), "status": data.get("status"),
            "link": data.get("link"), "title": (data.get("title") or {}).get("rendered")}


def list_posts(status: str = "draft", per_page: int = 5, **_p) -> dict:
    """List recent posts (default: your drafts) — read-only, to confirm what's there."""
    auth = _auth_header()
    if isinstance(auth, dict):
        return {"ok": False, **auth}
    url, token = auth
    req = urllib.request.Request(f"{url}/wp-json/wp/v2/posts?status={status}&per_page={int(per_page)}",
                                 headers={"Authorization": f"Basic {token}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "posts": [{"id": p["id"], "status": p["status"],
                                   "title": (p.get("title") or {}).get("rendered"), "link": p.get("link")}
                                  for p in data]}


def urirun_bindings() -> dict:
    mk = lambda uri, exp, props, req: {uri: {  # noqa: E731
        "kind": "command" if "/command/" in uri else "query", "adapter": "local-function",
        "ref": f"wp_connector:{exp}", "python": {"type": "python", "module": "wp_connector", "export": exp},
        "inputSchema": {"type": "object", "properties": props, **({"required": req} if req else {})}, "uri": uri}}
    b = {}
    b.update(mk("wordpress://blog/post/command/create", "create_post",
                {"title": {"type": "string"}, "content": {"type": "string"},
                 "status": {"type": "string", "enum": ["draft", "pending", "publish"], "default": "draft"},
                 "excerpt": {"type": "string"}, "categories": {"type": "string"}}, []))
    b.update(mk("wordpress://blog/post/query/list", "list_posts",
                {"status": {"type": "string"}, "per_page": {"type": "integer"}}, []))
    return {"version": "urirun.bindings.v2", "bindings": b}
