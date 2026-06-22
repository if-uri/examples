#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A tiny self-contained "connector" for the LLM-over-URI agent demo. It exposes a
# handful of capabilities as v2 bindings and answers them via this same CLI, so
# the example runs with nothing installed but `urirun`. In production these would
# be real connector packages (time-tools, http-check, browser-control / a Chrome
# CDP connector, sqlite-context).

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.abspath(__file__)
SELF = [sys.executable, HERE]
LOG_FILE = os.path.join(os.path.dirname(HERE), "agent-run.log")


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


# --- bindings (the agent's action space) -----------------------------------

def _route(uri, argv, properties, label, *, required=None):
    schema = {"type": "object", "additionalProperties": False, "properties": properties}
    if required:
        schema["required"] = required
    return {uri: {"adapter": "argv-template", "kind": "command", "argv": argv,
                  "inputSchema": schema, "meta": {"connector": "agent-demo", "label": label}, "uri": uri}}


def bindings() -> dict:
    b: dict = {}
    b.update(_route("time://host/clock/query/now", SELF + ["now"], {}, "Current UTC time"))
    b.update(_route("httpcheck://host/url/query/status", SELF + ["http-status", "--url", "{url}"],
                    {"url": {"type": "string"}}, "Check an HTTP URL", required=["url"]))
    b.update(_route("browser://chrome/page/query/dom", SELF + ["browser-dom", "--url", "{url}", "--max", "{max}"],
                    {"url": {"type": "string"}, "max": {"type": "integer", "default": 600}},
                    "Read page text via headless Chrome", required=["url"]))
    b.update(_route("log://host/run/command/write", SELF + ["log", "--event", "{event}", "--detail", "{detail}"],
                    {"event": {"type": "string"}, "detail": {"type": "string", "default": ""}},
                    "Append a structured run log", required=["event"]))
    return {"version": "urirun.bindings.v2", "bindings": b}


# --- capability implementations --------------------------------------------

def now() -> dict:
    return {"ok": True, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def http_status(url: str) -> dict:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "ifuri-agent/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return {"ok": True, "url": url, "status": int(response.status), "finalUrl": response.geturl()}
    except urllib.error.HTTPError as exc:
        return {"ok": exc.code < 500, "url": url, "status": int(exc.code)}
    except Exception as exc:  # noqa: BLE001 - report network errors as JSON
        return {"ok": False, "url": url, "status": None, "error": str(exc)}


def _chrome_bin() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def browser_dom(url: str, max_chars: int = 600) -> dict:
    """Read page text via headless Chrome (CDP-less one-shot). Falls back to a dry
    plan when no Chrome binary is present, so the demo runs anywhere.

    This is the inline stub. When the `urirun-connector-browser-control` package is
    available, agent.py reuses that real connector for the browser:// routes instead
    (see agent.browser_control_bindings)."""
    chrome = _chrome_bin()
    if not chrome:
        return {"ok": True, "dryRun": True, "url": url, "tool": "chrome --headless --dump-dom",
                "note": "no Chrome binary found; install Chrome/Chromium or run a CDP browser connector to execute"}
    try:
        out = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--dump-dom", url],
                             capture_output=True, text=True, timeout=30)
        html = out.stdout or ""
        # crude text sample (the real connector would use CDP DOM/Runtime)
        text = " ".join(html.split())[:int(max_chars)]
        return {"ok": out.returncode == 0, "url": url, "bytes": len(html), "sample": text}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "url": url, "error": str(exc)}


def log_event(event: str, detail: str = "") -> dict:
    line = json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, "detail": detail})
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return {"ok": True, "logged": event, "file": LOG_FILE}


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    flags = {argv[i][2:]: argv[i + 1] for i in range(1, len(argv) - 1, 2) if argv[i].startswith("--")}
    if cmd == "bindings":
        emit(bindings()); return 0
    if cmd == "now":
        emit(now()); return 0
    if cmd == "http-status":
        emit(http_status(flags.get("url", ""))); return 0
    if cmd == "browser-dom":
        emit(browser_dom(flags.get("url", ""), int(flags.get("max", 600) or 600))); return 0
    if cmd == "log":
        emit(log_event(flags.get("event", ""), flags.get("detail", ""))); return 0
    print("usage: tools.py {bindings|now|http-status|browser-dom|log}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
