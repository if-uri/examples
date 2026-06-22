#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive a remote node's REAL browser from the host over the URI contract, using
# the browser-control connector's Chrome DevTools Protocol surface
# (browser://<node>/cdp/...). CDP works headed under Wayland and needs no
# xdotool/ydotool — the practical way to control Chrome on a Linux desktop node.
#
# The surface is stateful: launch a browser, then navigate / eval / screenshot /
# list tabs against the live page.
#
#   NODE_URL=http://192.168.188.201:8765 NODE=laptop python3 drive_cdp.py [url]

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.request

NODE_URL = os.environ.get("NODE_URL", "http://192.168.188.201:8765")
NODE = os.environ.get("NODE", "laptop")
URL = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"


def run(uri: str, payload: dict | None = None, timeout: float = 60) -> dict:
    body = json.dumps({"uri": uri, "payload": payload or {}}).encode()
    req = urllib.request.Request(NODE_URL + "/run", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def value(env: dict):
    r = env.get("result") or {}
    v = r.get("value") if isinstance(r, dict) and "value" in r else r
    if isinstance(v, str):
        try:
            return json.loads(v)
        except (ValueError, TypeError):
            return v
    return v


def cdp(op: str, payload: dict | None = None, **kw) -> dict:
    """Call a browser://<node>/cdp/... route."""
    return run(f"browser://{NODE}/cdp/{op}", payload, **kw)


def _save_screenshot(v: dict) -> str | None:
    """The screenshot route returns the PNG as base64 under one of a few keys."""
    if not isinstance(v, dict):
        return None
    for key in ("data", "png", "base64", "screenshot", "image"):
        blob = v.get(key)
        if isinstance(blob, str) and len(blob) > 100:
            raw = blob.split(",", 1)[1] if blob.startswith("data:") else blob
            try:
                out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remote-shot.png")
                with open(out, "wb") as fh:
                    fh.write(base64.b64decode(raw))
                return out
            except (ValueError, OSError):
                return None
    return None


def main() -> int:
    print(f"driving the browser on {NODE} ({NODE_URL})  ->  {URL}\n")
    ok = 0

    e = cdp("session/command/launch", {"browser": "chrome", "headless": True, "url": "about:blank"})
    v = value(e)
    print(f"  {'✓' if e.get('ok') else '✗'} launch        {json.dumps(v)[:90] if e.get('ok') else e.get('error')}")
    ok += bool(e.get("ok"))
    time.sleep(2)

    e = cdp("page/command/navigate", {"url": URL})
    print(f"  {'✓' if e.get('ok') else '✗'} navigate      {URL}")
    ok += bool(e.get("ok"))
    time.sleep(2)

    e = cdp("page/query/eval", {"expr": "document.title"})
    title = value(e).get("value") if isinstance(value(e), dict) else value(e)
    print(f"  {'✓' if e.get('ok') else '✗'} eval title    {title!r}")
    ok += bool(e.get("ok"))

    e = cdp("page/query/eval", {"expr": "document.querySelectorAll('a').length"})
    links = value(e).get("value") if isinstance(value(e), dict) else value(e)
    print(f"  {'✓' if e.get('ok') else '✗'} eval links    {links} <a> on the page")
    ok += bool(e.get("ok"))

    e = cdp("page/query/screenshot", {})
    v = value(e)
    shot = _save_screenshot(v)
    nbytes = v.get("bytes") if isinstance(v, dict) else None
    detail = ("saved " + shot) if shot else (f"{nbytes}-byte PNG" if nbytes else "taken")
    print(f"  {'✓' if e.get('ok') else '✗'} screenshot    {detail}")
    ok += bool(e.get("ok"))

    e = cdp("page/query/tabs", {})
    tabs = value(e).get("tabs", []) if isinstance(value(e), dict) else []
    print(f"  {'✓' if e.get('ok') else '✗'} tabs          {[t.get('title') for t in tabs][:3]}")
    ok += bool(e.get("ok"))

    print(f"\n{ok}/6 CDP browser steps ok on {NODE}")
    return 0 if ok == 6 else 1


if __name__ == "__main__":
    raise SystemExit(main())
