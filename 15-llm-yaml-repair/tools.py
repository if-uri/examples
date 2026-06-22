#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A tiny self-contained "connector" for the YAML-flow repair demo. It exposes a
# few capabilities as v2 bindings and answers them via this same CLI, so the
# example runs with nothing installed but `urirun`. One route (`note put`)
# deliberately *fails on bad input* (empty key) — that failure is what the
# repair loop feeds back to the LLM to get a corrected flow.

from __future__ import annotations

import json
import os
import sys
import time

HERE = os.path.abspath(__file__)
SELF = [sys.executable, HERE]
NOTES_FILE = os.path.join(os.path.dirname(HERE), "notes.json")
LOG_FILE = os.path.join(os.path.dirname(HERE), "agent-run.log")


def emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


# --- bindings (the agent's action space) -----------------------------------

def _route(uri, argv, properties, label, *, required=None):
    schema = {"type": "object", "additionalProperties": False, "properties": properties}
    if required:
        schema["required"] = required
    return {uri: {"adapter": "argv-template", "kind": "command", "argv": argv,
                  "inputSchema": schema, "meta": {"connector": "repair-demo", "label": label}, "uri": uri}}


def bindings() -> dict:
    b: dict = {}
    b.update(_route("time://host/clock/query/now", SELF + ["now"], {}, "Current UTC time"))
    # note put REQUIRES a non-empty key — and reports ok:false when it is missing.
    b.update(_route("note://host/store/command/put",
                    SELF + ["note-put", "--key", "{key}", "--value", "{value}"],
                    {"key": {"type": "string"}, "value": {"type": "string", "default": ""}},
                    "Store a note under a key", required=["key"]))
    b.update(_route("log://host/run/command/write",
                    SELF + ["log", "--event", "{event}", "--detail", "{detail}"],
                    {"event": {"type": "string"}, "detail": {"type": "string", "default": ""}},
                    "Append a structured run log", required=["event"]))
    return {"version": "urirun.bindings.v2", "bindings": b}


# --- capability implementations --------------------------------------------

def now() -> dict:
    return {"ok": True, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def note_put(key: str, value: str = "") -> dict:
    # The intentional failure mode: an empty key is rejected with a clear, machine
    # -readable error — exactly the kind of signal an LLM can correct from.
    if not key.strip():
        return {"ok": False, "error": "key is required and must be non-empty"}
    notes = {}
    if os.path.exists(NOTES_FILE):
        try:
            notes = json.loads(open(NOTES_FILE, encoding="utf-8").read() or "{}")
        except ValueError:
            notes = {}
    notes[key] = value
    open(NOTES_FILE, "w", encoding="utf-8").write(json.dumps(notes, ensure_ascii=False, indent=2))
    return {"ok": True, "stored": key, "count": len(notes)}


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
    if cmd == "note-put":
        emit(note_put(flags.get("key", ""), flags.get("value", ""))); return 0
    if cmd == "log":
        emit(log_event(flags.get("event", ""), flags.get("detail", ""))); return 0
    print("usage: tools.py {bindings|now|note-put|log}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
