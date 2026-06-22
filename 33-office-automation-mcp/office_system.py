#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A self-contained, stateful "office computer" simulator exposed as urirun URI
# routes — a realistic MCP tool surface (windows, apps, browser, email, files,
# clipboard, calendar, screen/OCR, notifications). Every route mutates a shared
# JSON state file (OFFICE_STATE), so a flow's later steps SEE earlier steps and a
# verification step can check whether the task actually happened. Nothing touches
# the real machine — but the schemas, the state transitions and the verification
# are real, so it stands in for driving an actual desktop over the same URIs.

from __future__ import annotations

import argparse
import json
import os
import sys
import time

STATE = os.environ.get("OFFICE_STATE", "/tmp/office_state.json")


def _load() -> dict:
    if os.path.exists(STATE):
        try:
            return json.loads(open(STATE, encoding="utf-8").read() or "{}")
        except ValueError:
            pass
    return {"apps": [], "windows": [], "browser": {"tabs": [], "active": None},
            "email": {"draft": None, "sent": [], "inbox": [
                {"id": "m1", "from": "boss@corp", "subject": "Q2 report?", "body": "Please send the Q2 numbers."},
                {"id": "m2", "from": "hr@corp", "subject": "Town hall", "body": "Friday 15:00."}]},
            "files": {}, "clipboard": "", "calendar": [], "screenshots": [], "notifications": [], "_seq": 0}


def _save(s: dict) -> None:
    open(STATE, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=2))


def _nid(s: dict, prefix: str) -> str:
    s["_seq"] = int(s.get("_seq", 0)) + 1
    return f"{prefix}{s['_seq']}"


# --- route implementations (op -> fn(state, args) -> result dict) -----------

def _open_window(s, app, title):
    wid = _nid(s, "w")
    for w in s["windows"]:
        w["focused"] = False
    s["windows"].append({"id": wid, "app": app, "title": title, "focused": True})
    return wid


OPS = {}
def op(name):  # noqa: D401 - small registrar
    def deco(fn):
        OPS[name] = fn
        return fn
    return deco


@op("app-open")
def _app_open(s, a):
    if a.app not in s["apps"]:
        s["apps"].append(a.app)
    wid = _open_window(s, a.app, a.app.capitalize())
    return {"ok": True, "app": a.app, "window": wid, "running": len(s["apps"])}

@op("app-close")
def _app_close(s, a):
    s["apps"] = [x for x in s["apps"] if x != a.app]
    s["windows"] = [w for w in s["windows"] if w["app"] != a.app]
    return {"ok": True, "closed": a.app, "running": len(s["apps"])}

@op("app-running")
def _app_running(s, a):
    return {"ok": True, "apps": s["apps"]}

@op("window-list")
def _window_list(s, a):
    return {"ok": True, "windows": s["windows"], "count": len(s["windows"])}

@op("window-focus")
def _window_focus(s, a):
    found = False
    for w in s["windows"]:
        w["focused"] = (w["id"] == a.id)
        found = found or w["focused"]
    return {"ok": found, "focused": a.id} if found else {"ok": False, "error": f"no window {a.id}"}

@op("window-close")
def _window_close(s, a):
    before = len(s["windows"])
    s["windows"] = [w for w in s["windows"] if w["id"] != a.id]
    return {"ok": len(s["windows"]) < before, "closed": a.id, "count": len(s["windows"])}

@op("browser-open")
def _browser_open(s, a):
    title = a.url.split("//")[-1].split("/")[0]
    content = f"<page url={a.url}> Welcome to {title}. Invoice total: 199.00 PLN. Contact: sales@{title}. </page>"
    tab = {"id": _nid(s, "t"), "url": a.url, "title": title, "content": content, "fields": {}}
    s["browser"]["tabs"].append(tab)
    s["browser"]["active"] = tab["id"]
    _open_window(s, "browser", title)
    return {"ok": True, "tab": tab["id"], "url": a.url, "title": title}

@op("browser-read")
def _browser_read(s, a):
    tab = next((t for t in s["browser"]["tabs"] if t["id"] == s["browser"]["active"]), None)
    return {"ok": bool(tab), "content": tab["content"] if tab else "", "url": tab["url"] if tab else None}

@op("browser-type")
def _browser_type(s, a):
    tab = next((t for t in s["browser"]["tabs"] if t["id"] == s["browser"]["active"]), None)
    if not tab:
        return {"ok": False, "error": "no active tab"}
    tab["fields"][a.selector] = a.text
    return {"ok": True, "typed": a.text, "into": a.selector}

@op("browser-click")
def _browser_click(s, a):
    tab = next((t for t in s["browser"]["tabs"] if t["id"] == s["browser"]["active"]), None)
    if not tab:
        return {"ok": False, "error": "no active tab"}
    if a.selector in ("submit", "#submit", "Send", "Pay"):
        tab["submitted"] = dict(tab.get("fields", {}))
        tab["content"] = f"<page> Submitted: {json.dumps(tab['submitted'])}. Confirmation #OK-{s['_seq']}. </page>"
    return {"ok": True, "clicked": a.selector}

@op("browser-screenshot")
def _browser_screenshot(s, a):
    sid = _nid(s, "shot")
    s["screenshots"].append({"id": sid, "of": "browser", "at": int(time.time())})
    return {"ok": True, "screenshot": sid}

@op("email-compose")
def _email_compose(s, a):
    s["email"]["draft"] = {"to": a.to, "subject": a.subject, "body": a.body, "attachments": []}
    _open_window(s, "email", f"Compose: {a.subject}")
    return {"ok": True, "draft": {"to": a.to, "subject": a.subject}}

@op("email-attach")
def _email_attach(s, a):
    if not s["email"]["draft"]:
        return {"ok": False, "error": "no draft — compose first"}
    if a.path not in s["files"]:
        return {"ok": False, "error": f"no such file {a.path}"}
    s["email"]["draft"]["attachments"].append(a.path)
    return {"ok": True, "attached": a.path}

@op("email-send")
def _email_send(s, a):
    if not s["email"]["draft"]:
        return {"ok": False, "error": "no draft to send"}
    msg = dict(s["email"]["draft"]); msg["id"] = _nid(s, "sent"); msg["at"] = int(time.time())
    s["email"]["sent"].append(msg)
    s["email"]["draft"] = None
    return {"ok": True, "sent": msg["id"], "to": msg["to"], "attachments": len(msg["attachments"])}

@op("email-inbox")
def _email_inbox(s, a):
    return {"ok": True, "inbox": s["email"]["inbox"], "count": len(s["email"]["inbox"])}

@op("email-search")
def _email_search(s, a):
    q = (a.q or "").lower()
    hits = [m for m in s["email"]["inbox"] if q in (m["subject"] + m["body"]).lower()]
    return {"ok": True, "hits": hits, "count": len(hits)}

@op("fs-write")
def _fs_write(s, a):
    s["files"][a.path] = a.content
    return {"ok": True, "wrote": a.path, "bytes": len(a.content)}

@op("fs-read")
def _fs_read(s, a):
    return {"ok": a.path in s["files"], "path": a.path, "content": s["files"].get(a.path, "")}

@op("fs-list")
def _fs_list(s, a):
    pref = a.dir.rstrip("/") + "/" if a.dir not in ("", "/") else ""
    names = [p for p in s["files"] if p.startswith(pref)]
    return {"ok": True, "dir": a.dir, "files": names, "count": len(names)}

@op("fs-copy")
def _fs_copy(s, a):
    if a.src not in s["files"]:
        return {"ok": False, "error": f"no such file {a.src}"}
    s["files"][a.dst] = s["files"][a.src]
    return {"ok": True, "copied": a.src, "to": a.dst}

@op("clipboard-copy")
def _clip_copy(s, a):
    s["clipboard"] = a.text
    return {"ok": True, "copied": len(a.text)}

@op("clipboard-paste")
def _clip_paste(s, a):
    return {"ok": True, "text": s["clipboard"]}

@op("calendar-create")
def _cal_create(s, a):
    ev = {"id": _nid(s, "ev"), "title": a.title, "when": a.when, "invitees": a.invitees}
    s["calendar"].append(ev)
    return {"ok": True, "event": ev["id"], "title": a.title}

@op("calendar-list")
def _cal_list(s, a):
    return {"ok": True, "events": s["calendar"], "count": len(s["calendar"])}

@op("screen-ocr")
def _screen_ocr(s, a):
    # deterministic mock OCR keyed by the image name
    text = {"invoice.png": "FAKTURA 7/2026  Kwota: 199,00 PLN  NIP: 123-456-78-90",
            "receipt.png": "PARAGON  Razem: 42,00 PLN"}.get(a.image, f"[text recognised from {a.image}]")
    return {"ok": True, "image": a.image, "text": text}

@op("notify-send")
def _notify(s, a):
    s["notifications"].append({"id": _nid(s, "n"), "message": a.message, "at": int(time.time())})
    return {"ok": True, "notified": a.message}


# --- the URI action space (MCP tool surface), with JSON Schemas -------------

def _route(uri, op_name, props, label, required=None):
    argv = [sys.executable, os.path.abspath(__file__), op_name]
    for key in props:
        argv += [f"--{key}", "{" + key + "}"]
    schema = {"type": "object", "additionalProperties": False, "properties": props}
    if required:
        schema["required"] = required
    return {uri: {"adapter": "argv-template", "kind": "command", "argv": argv,
                  "inputSchema": schema, "meta": {"connector": "office", "label": label}, "uri": uri}}


S = lambda: {"type": "string"}  # noqa: E731


def bindings() -> dict:
    b: dict = {}
    b.update(_route("app://office/launch/command/open", "app-open", {"app": S()}, "Launch an application", ["app"]))
    b.update(_route("app://office/launch/command/quit", "app-close", {"app": S()}, "Quit an application", ["app"]))
    b.update(_route("app://office/state/query/running", "app-running", {}, "List running apps"))
    b.update(_route("window://office/manager/query/list", "window-list", {}, "List open windows"))
    b.update(_route("window://office/manager/command/focus", "window-focus", {"id": S()}, "Focus a window", ["id"]))
    b.update(_route("window://office/manager/command/close", "window-close", {"id": S()}, "Close a window", ["id"]))
    b.update(_route("browser://office/tab/command/open", "browser-open", {"url": S()}, "Open a URL in a new tab", ["url"]))
    b.update(_route("browser://office/page/query/read", "browser-read", {}, "Read the active page text"))
    b.update(_route("browser://office/page/command/type", "browser-type", {"selector": S(), "text": S()}, "Type into a field", ["selector", "text"]))
    b.update(_route("browser://office/page/command/click", "browser-click", {"selector": S()}, "Click an element", ["selector"]))
    b.update(_route("browser://office/page/query/screenshot", "browser-screenshot", {}, "Screenshot the page"))
    b.update(_route("email://office/message/command/compose", "email-compose", {"to": S(), "subject": S(), "body": S()}, "Compose a new email", ["to", "subject", "body"]))
    b.update(_route("email://office/message/command/attach", "email-attach", {"path": S()}, "Attach a file to the draft", ["path"]))
    b.update(_route("email://office/message/command/send", "email-send", {}, "Send the drafted email"))
    b.update(_route("email://office/inbox/query/list", "email-inbox", {}, "List inbox messages"))
    b.update(_route("email://office/inbox/query/search", "email-search", {"q": S()}, "Search the inbox", ["q"]))
    b.update(_route("fs://office/file/command/write", "fs-write", {"path": S(), "content": S()}, "Write a file", ["path", "content"]))
    b.update(_route("fs://office/file/query/read", "fs-read", {"path": S()}, "Read a file", ["path"]))
    b.update(_route("fs://office/dir/query/list", "fs-list", {"dir": S()}, "List a directory", ["dir"]))
    b.update(_route("fs://office/file/command/copy", "fs-copy", {"src": S(), "dst": S()}, "Copy a file", ["src", "dst"]))
    b.update(_route("clipboard://office/buffer/command/copy", "clipboard-copy", {"text": S()}, "Copy text to clipboard", ["text"]))
    b.update(_route("clipboard://office/buffer/query/paste", "clipboard-paste", {}, "Read the clipboard"))
    b.update(_route("calendar://office/event/command/create", "calendar-create", {"title": S(), "when": S(), "invitees": S()}, "Create a calendar event", ["title", "when"]))
    b.update(_route("calendar://office/event/query/list", "calendar-list", {}, "List calendar events"))
    b.update(_route("screen://office/ocr/query/text", "screen-ocr", {"image": S()}, "OCR text from an image", ["image"]))
    b.update(_route("notify://office/desktop/command/send", "notify-send", {"message": S()}, "Show a desktop notification", ["message"]))
    return {"version": "urirun.bindings.v2", "bindings": b}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "bindings":
        print(json.dumps(bindings())); return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("op")
    for key in ("app", "id", "url", "selector", "text", "to", "subject", "body", "path",
                "content", "dir", "src", "dst", "q", "title", "when", "invitees", "image", "message"):
        parser.add_argument(f"--{key}", default="")
    args = parser.parse_args(argv)
    fn = OPS.get(args.op)
    if not fn:
        print(json.dumps({"ok": False, "error": f"unknown op {args.op}"})); return 1
    state = _load()
    result = fn(state, args)
    _save(state)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
