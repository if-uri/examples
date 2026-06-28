#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Reuse a urirun connector in a NEW flow, GUARDED BY ITS CONTRACT.
#
#   1. define a tiny `notes` connector (the standard `@conn.handler` authoring API)
#   2. declare its CONTRACTS (urirun_contract) and `conform()` them at startup
#   3. compile the bindings into a registry and run a 2-step flow over the wire
#      (`urirun.run` per step) — append a note, then list notes
#   4. GUARD every step: validate the returned envelope against the route's
#      contract with `envelope_violation()` — the contract gate, in a flow
#   5. `--drift` swaps in a buggy handler that returns a mis-shaped envelope;
#      the contract catches it AT THE FLOW BOUNDARY, before downstream steps trust it
#
# This is how you safely REUSE any urirun connector in a new example: its
# contract is the single declared truth, and it guards the flow in any language
# (the same `contracts.json` drives the JS/Go SDK guards too — see urirun-contract).

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))  # if-uri/


def _ensure_imports() -> None:
    cand = os.path.join(ROOT, "urirun", "adapters", "python")
    if os.path.isdir(cand) and cand not in sys.path:
        sys.path.insert(0, cand)


_ensure_imports()
import urirun  # noqa: E402
from urirun_contract import Contract, conform, envelope_violation  # noqa: E402

# ── 1. the connector (reusable; same authoring API as every urirun-connector-*) ──
notes = urirun.connector("notes", scheme="notes", target="host",
                         meta={"label": "In-memory notes"})
_STORE: list[dict] = []
_DRIFT = False  # flipped by run(drift=True) to simulate a connector that drifts


@notes.handler("entry/command/append", meta={"label": "Append a note"})
def append(text: str = "", tag: str = "") -> dict:
    _STORE.append({"id": f"n{len(_STORE)}", "text": text, "tag": tag})
    if _DRIFT:  # a connector that silently drifts from its declared output
        return {"ok": True, "action": "append", "id": "n?", "text": text,
                "tag": tag, "count": str(len(_STORE))}  # count:str + no connector
    return urirun.ok(connector="notes", action="append",
                     id=_STORE[-1]["id"], text=text, tag=tag, count=len(_STORE))


@notes.handler("entry/query/list", meta={"label": "List notes"})
def list_notes(tag: str = "") -> dict:
    items = [n for n in _STORE if not tag or n["tag"] == tag]
    return urirun.ok(connector="notes", action="list", entries=items, count=len(items))


# ── 2. the contract — the SINGLE declared truth for the connector's shape ──
CONTRACTS = {
    "entry/command/append": Contract(
        version="v1", effect="command", reversible=False,
        inp={"text": "?str", "tag": "?str"},
        out={"ok": "const:true", "connector": "const:notes", "action": "const:append",
             "id": "str", "text": "str", "tag": "?str", "count": "int"},
        errors=("precondition-unmet",),
        examples=({"payload": {"text": "buy milk"},
                   "result": {"ok": True, "connector": "notes", "action": "append",
                              "id": "n1", "text": "buy milk", "tag": "", "count": 1}},)),
    "entry/query/list": Contract(
        version="v1", effect="query", reversible=False,
        inp={"tag": "?str"},
        out={"ok": "const:true", "connector": "const:notes", "action": "const:list",
             "entries": "list", "count": "int"},
        examples=({"payload": {},
                   "result": {"ok": True, "connector": "notes", "action": "list",
                              "entries": [], "count": 0}},)),
}


def _route_of(uri: str) -> str:
    return uri.split("://host/", 1)[1]


def run(drift: bool = False) -> int:
    global _DRIFT
    _DRIFT = drift
    _STORE.clear()
    conform(CONTRACTS)  # the contract itself is gated first (effect↔verb, examples, reversible)
    print("✓ conform: contract is internally consistent\n")

    registry = urirun.compile_registry(notes.bindings())
    flow = [
        {"uri": "notes://host/entry/command/append", "payload": {"text": "buy milk", "tag": "todo"}},
        {"uri": "notes://host/entry/command/append", "payload": {"text": "call Ada", "tag": "todo"}},
        {"uri": "notes://host/entry/query/list", "payload": {"tag": "todo"}},
    ]

    print(f"flow: notes ({'DRIFT' if drift else 'honest'} handler) — contract guards every step")
    violations = 0
    for step in flow:
        route = _route_of(step["uri"])
        env = urirun.run(step["uri"], registry, step["payload"], mode="execute")
        envelope = (env.get("result") or {}).get("value", {})
        problem = envelope_violation(CONTRACTS[route], envelope)
        mark = "OK ✓" if not problem else f"CONTRACT VIOLATION ✗ — {problem}"
        print(f"  {route:24} -> {mark}")
        if problem:
            violations += 1

    print()
    if drift:
        # we EXPECT the drift to be caught — that's the whole point
        ok = violations > 0
        print(f"→ drift caught by contract: {'YES ✓' if ok else 'NO ✗ (gate failed!)'}")
        return 0 if ok else 1
    ok = violations == 0
    print(f"→ honest connector conforms across the flow: {'YES ✓' if ok else 'NO ✗'}")
    print(f"  notes stored: {json.dumps(_STORE, ensure_ascii=False)}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Reuse a urirun connector in a flow, guarded by its contract")
    ap.add_argument("--drift", action="store_true",
                    help="use a mis-shaped handler; the contract must catch it")
    ap.add_argument("--both", action="store_true", help="run honest then drift")
    args = ap.parse_args(argv)
    if args.both:
        print("══ honest run ══");  rc1 = run(drift=False)
        print("\n══ drift run ══");  rc2 = run(drift=True)
        return rc1 or rc2
    return run(drift=args.drift)


if __name__ == "__main__":
    raise SystemExit(main())
