#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive the deployed surface on a node and report — including REAL browser
# control (read a page + screenshot) when Chrome is on the node.

from __future__ import annotations

import json
import os
import sys
import urllib.request

NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8765")


def run(uri: str, payload: dict | None = None, timeout: float = 60) -> dict:
    body = json.dumps({"uri": uri, "payload": payload or {}}).encode()
    req = urllib.request.Request(NODE + "/run", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def value(env: dict):
    r = env.get("result") or {}
    return r.get("value", r) if isinstance(r, dict) else r


CHECKS = [
    ("sys://laptop/host/query/info", {}, lambda v: "hostname" in v),
    ("sys://laptop/disk/query/usage", {}, lambda v: "free_gb" in v),
    ("codec://laptop/text/query/base64", {"text": "ifuri"}, lambda v: v.get("result") == "aWZ1cmk="),
    ("hash://laptop/text/query/sha256", {"text": "ifuri"}, lambda v: len(v.get("sha256", "")) == 64),
    ("uuid://laptop/id/query/v4", {"count": 2}, lambda v: len(v.get("ids", [])) == 2),
    ("httpcheck://laptop/url/query/status", {"url": "https://example.com"}, lambda v: v.get("status") == 200),
    ("office://laptop/note/command/write", {"text": "deploy verify"}, lambda v: v.get("ok")),
    ("browser://laptop/page/query/text", {"url": "https://example.com", "max": 200}, lambda v: "Example Domain" in v.get("text", "")),
    ("browser://laptop/page/query/screenshot", {"url": "https://example.com"}, lambda v: v.get("bytes", 0) > 0),
]


def main() -> int:
    print(f"verifying deployed surface on {NODE}\n")
    ok = 0
    for uri, payload, check in CHECKS:
        env = run(uri, payload)
        v = value(env)
        passed = bool(env.get("ok")) and check(v if isinstance(v, dict) else {})
        ok += passed
        mark = "✓" if passed else "✗"
        print(f"  {mark} {uri:42} {json.dumps(v)[:70] if passed else env.get('error', v)}")
    print(f"\n{ok}/{len(CHECKS)} routes verified on the remote node")
    return 0 if ok == len(CHECKS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
