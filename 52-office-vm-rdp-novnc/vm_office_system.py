#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A self-contained, stateful "office over a virtual machine" simulator exposed as
# urirun URI routes. It models the real corporate pattern:
#
#     VM fleet  ──rdp://──►  RDP gateway session  ──novnc://──►  HTML5 canvas in a
#     browser  ──desktop://──►  office apps inside the VM (Excel/Outlook/forms)
#
# i.e. an office worker (or an agent) reaches a Windows/Linux VM over RDP, the RDP
# session is surfaced through a noVNC (HTML5) view in the browser, and office tasks
# run *inside the VM* over typed URI routes. Every route mutates a shared JSON state
# (VM_OFFICE_STATE) so a flow's later steps SEE earlier steps and a verification step
# can check whether the task actually happened — including teardown correctness
# (no dangling RDP sessions / noVNC views) and error behaviour (no connect to a
# powered-off VM). Nothing touches a real machine, but the schemas, the RDP/noVNC
# state transitions and the verification are real, so the same plan drives an actual
# noVNC desktop (see run.py --live, which reuses example 28's noVNC connector).

from __future__ import annotations

import argparse
import json
import os
import sys
import time

STATE = os.environ.get("VM_OFFICE_STATE", "/tmp/vm_office_state.json")

# the VM fleet the gateway can reach (name -> os, powered off until started)
FLEET = {
    "win11-finance": {"os": "Windows 11", "role": "finance workstation"},
    "win-sales": {"os": "Windows 10", "role": "sales workstation"},
    "ubuntu-dev": {"os": "Ubuntu 24.04", "role": "dev box"},
}

# deterministic mock OCR for invoice/receipt images dropped into a VM
_IMAGE_TEXT = {
    "invoice.png": "FAKTURA 11/2026  Kwota: 2 460,00 PLN  NIP: 765-432-10-98",
    "receipt.png": "PARAGON  Razem: 84,00 PLN",
}


def _load() -> dict:
    if os.path.exists(STATE):
        try:
            return json.loads(open(STATE, encoding="utf-8").read() or "{}")
        except ValueError:
            pass
    vms = {name: {**meta, "power": "off", "files": {}} for name, meta in FLEET.items()}
    return {"vms": vms, "sessions": {}, "views": {}, "clipboard": "",
            "screenshots": [], "ocr_log": [], "notifications": [], "_seq": {}}


def _save(s: dict) -> None:
    open(STATE, "w", encoding="utf-8").write(json.dumps(s, ensure_ascii=False, indent=2))


def _nid(s: dict, prefix: str) -> str:
    seq = s.setdefault("_seq", {})
    seq[prefix] = int(seq.get(prefix, 0)) + 1
    return f"{prefix}{seq[prefix]}"


def _session(s: dict, sid: str) -> dict | None:
    return s["sessions"].get(sid)


# --- route implementations (op -> fn(state, args) -> result dict) -----------

OPS = {}
def op(name):  # noqa: D401 - small registrar
    def deco(fn):
        OPS[name] = fn
        return fn
    return deco


# -- VM fleet lifecycle -------------------------------------------------------

@op("vm-list")
def _vm_list(s, a):
    vms = [{"name": n, "os": v["os"], "role": v["role"], "power": v["power"]} for n, v in s["vms"].items()]
    return {"ok": True, "vms": vms, "count": len(vms)}

@op("vm-start")
def _vm_start(s, a):
    vm = s["vms"].get(a.vm)
    if not vm:
        return {"ok": False, "error": f"no such VM {a.vm}"}
    vm["power"] = "on"
    return {"ok": True, "vm": a.vm, "power": "on"}

@op("vm-stop")
def _vm_stop(s, a):
    vm = s["vms"].get(a.vm)
    if not vm:
        return {"ok": False, "error": f"no such VM {a.vm}"}
    vm["power"] = "off"
    # powering off a VM tears down its RDP sessions and their noVNC views
    dead = [sid for sid, ss in s["sessions"].items() if ss["vm"] == a.vm]
    for sid in dead:
        s["views"] = {vid: v for vid, v in s["views"].items() if v["session"] != sid}
        s["sessions"].pop(sid, None)
    return {"ok": True, "vm": a.vm, "power": "off", "sessionsClosed": len(dead)}


# -- RDP gateway session ------------------------------------------------------

@op("rdp-connect")
def _rdp_connect(s, a):
    vm = s["vms"].get(a.vm)
    if not vm:
        return {"ok": False, "error": f"no such VM {a.vm}"}
    if vm["power"] != "on":
        return {"ok": False, "error": f"VM {a.vm} is powered off — start it before connecting"}
    sid = _nid(s, "s")
    s["sessions"][sid] = {"vm": a.vm, "user": a.user or "operator", "focused": None,
                          "screen": f"{vm['os']} desktop", "saved": False}
    return {"ok": True, "session": sid, "vm": a.vm, "user": a.user or "operator"}

@op("rdp-disconnect")
def _rdp_disconnect(s, a):
    if a.session not in s["sessions"]:
        return {"ok": False, "error": f"no session {a.session}"}
    views = [vid for vid, v in s["views"].items() if v["session"] == a.session]
    for vid in views:
        s["views"].pop(vid, None)
    s["sessions"].pop(a.session, None)
    return {"ok": True, "disconnected": a.session, "viewsClosed": len(views)}

@op("rdp-list")
def _rdp_list(s, a):
    return {"ok": True, "sessions": [{"id": sid, **{k: ss[k] for k in ("vm", "user")}}
                                     for sid, ss in s["sessions"].items()], "count": len(s["sessions"])}


# -- noVNC HTML5 view over the RDP session ------------------------------------

@op("novnc-open")
def _novnc_open(s, a):
    if a.session not in s["sessions"]:
        return {"ok": False, "error": f"no session {a.session} — connect over RDP first"}
    vid = _nid(s, "v")
    url = f"https://gateway.corp/novnc/{vid}/vnc.html?session={a.session}"
    s["views"][vid] = {"session": a.session, "live": True, "url": url, "canvas": "1280x720"}
    return {"ok": True, "view": vid, "url": url, "session": a.session}

@op("novnc-close")
def _novnc_close(s, a):
    if a.view not in s["views"]:
        return {"ok": False, "error": f"no view {a.view}"}
    s["views"].pop(a.view, None)
    return {"ok": True, "closed": a.view}

@op("novnc-status")
def _novnc_status(s, a):
    v = s["views"].get(a.view)
    if not v:
        return {"ok": False, "error": f"no view {a.view}"}
    return {"ok": True, "view": a.view, "live": v["live"], "canvas": v["canvas"], "url": v["url"]}


# -- desktop control inside the connected VM (driven via the noVNC canvas) ----

def _append_screen(ss: dict, text: str) -> None:
    ss["screen"] = (ss.get("screen", "") + "\n" + text).strip()

@op("desktop-launch")
def _desktop_launch(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    ss["focused"] = a.app
    _append_screen(ss, f"[{a.app}] window")
    return {"ok": True, "session": a.session, "launched": a.app}

@op("desktop-type")
def _desktop_type(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    _append_screen(ss, a.text)
    return {"ok": True, "session": a.session, "typed": a.text, "into": ss.get("focused")}

@op("desktop-hotkey")
def _desktop_hotkey(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    if a.keys.lower().replace(" ", "") in ("ctrl+s", "cmd+s"):
        ss["saved"] = True
    return {"ok": True, "session": a.session, "keys": a.keys, "saved": ss["saved"]}

@op("desktop-screenshot")
def _desktop_screenshot(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    sid = _nid(s, "shot")
    s["screenshots"].append({"id": sid, "session": a.session, "vm": ss["vm"], "at": int(time.time())})
    return {"ok": True, "screenshot": sid, "session": a.session}

@op("desktop-ocr")
def _desktop_ocr(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    text = ss.get("screen", "")
    s["ocr_log"].append({"session": a.session, "vm": ss["vm"], "text": text})
    return {"ok": True, "session": a.session, "text": text}

@op("screen-ocr-image")
def _screen_ocr_image(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    text = _IMAGE_TEXT.get(a.image, f"[text recognised from {a.image}]")
    _append_screen(ss, text)
    s["ocr_log"].append({"session": a.session, "vm": ss["vm"], "text": text, "image": a.image})
    return {"ok": True, "session": a.session, "image": a.image, "text": text}


# -- files inside the VM (persist across sessions on that VM) ------------------

@op("fs-save")
def _fs_save(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    s["vms"][ss["vm"]]["files"][a.path] = a.content
    return {"ok": True, "vm": ss["vm"], "saved": a.path, "bytes": len(a.content)}

@op("fs-read")
def _fs_read(s, a):
    ss = _session(s, a.session)
    if not ss:
        return {"ok": False, "error": f"no session {a.session}"}
    files = s["vms"][ss["vm"]]["files"]
    return {"ok": a.path in files, "path": a.path, "content": files.get(a.path, "")}


# -- RDP clipboard redirection (shared across all gateway sessions) -----------

@op("clipboard-set")
def _clipboard_set(s, a):
    s["clipboard"] = a.text
    return {"ok": True, "copied": len(a.text)}

@op("clipboard-get")
def _clipboard_get(s, a):
    return {"ok": True, "text": s["clipboard"]}


# -- notifications ------------------------------------------------------------

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
                  "inputSchema": schema, "meta": {"connector": "vm-office", "label": label}, "uri": uri}}


S = lambda: {"type": "string"}  # noqa: E731


def bindings() -> dict:
    b: dict = {}
    # VM fleet lifecycle
    b.update(_route("vm://fleet/catalog/query/list", "vm-list", {}, "List the VM fleet and power state"))
    b.update(_route("vm://fleet/instance/command/start", "vm-start", {"vm": S()}, "Power on a VM", ["vm"]))
    b.update(_route("vm://fleet/instance/command/stop", "vm-stop", {"vm": S()}, "Power off a VM (closes its sessions)", ["vm"]))
    # RDP gateway session
    b.update(_route("rdp://gateway/session/command/connect", "rdp-connect", {"vm": S(), "user": S()}, "Open an RDP session to a VM", ["vm"]))
    b.update(_route("rdp://gateway/session/command/disconnect", "rdp-disconnect", {"session": S()}, "Disconnect an RDP session", ["session"]))
    b.update(_route("rdp://gateway/session/query/list", "rdp-list", {}, "List active RDP sessions"))
    # noVNC HTML5 view over the session
    b.update(_route("novnc://gateway/view/command/open", "novnc-open", {"session": S()}, "Open an HTML5 noVNC view of the session", ["session"]))
    b.update(_route("novnc://gateway/view/command/close", "novnc-close", {"view": S()}, "Close a noVNC view", ["view"]))
    b.update(_route("novnc://gateway/view/query/status", "novnc-status", {"view": S()}, "Check the noVNC canvas status", ["view"]))
    # desktop control inside the VM
    b.update(_route("desktop://vm/app/command/launch", "desktop-launch", {"session": S(), "app": S()}, "Launch an app inside the VM", ["session", "app"]))
    b.update(_route("desktop://vm/input/command/type", "desktop-type", {"session": S(), "text": S()}, "Type text into the focused window", ["session", "text"]))
    b.update(_route("desktop://vm/input/command/hotkey", "desktop-hotkey", {"session": S(), "keys": S()}, "Press a key chord (e.g. ctrl+s)", ["session", "keys"]))
    b.update(_route("desktop://vm/screen/query/screenshot", "desktop-screenshot", {"session": S()}, "Capture the VM screen via noVNC", ["session"]))
    b.update(_route("desktop://vm/screen/query/ocr", "desktop-ocr", {"session": S()}, "OCR the current VM screen", ["session"]))
    b.update(_route("screen://vm/ocr/query/image", "screen-ocr-image", {"session": S(), "image": S()}, "OCR an image dropped into the VM", ["session", "image"]))
    # files inside the VM
    b.update(_route("fs://vm/file/command/save", "fs-save", {"session": S(), "path": S(), "content": S()}, "Save a file inside the VM", ["session", "path", "content"]))
    b.update(_route("fs://vm/file/query/read", "fs-read", {"session": S(), "path": S()}, "Read a file inside the VM", ["session", "path"]))
    # RDP clipboard redirection
    b.update(_route("clipboard://gateway/buffer/command/set", "clipboard-set", {"text": S()}, "Set the shared RDP clipboard", ["text"]))
    b.update(_route("clipboard://gateway/buffer/query/get", "clipboard-get", {}, "Read the shared RDP clipboard"))
    # notifications
    b.update(_route("notify://gateway/desktop/command/send", "notify-send", {"message": S()}, "Show a desktop notification", ["message"]))
    return {"version": "urirun.bindings.v2", "bindings": b}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "bindings":
        print(json.dumps(bindings())); return 0
    parser = argparse.ArgumentParser()
    parser.add_argument("op")
    for key in ("vm", "user", "session", "view", "app", "text", "keys", "image",
                "path", "content", "message"):
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
