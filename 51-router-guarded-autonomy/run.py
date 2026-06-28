#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The autonomy safety stack: DECIDE -> ROUTE -> EXECUTE -> GUARD.
#
# An autonomous agent turns a goal into a plan of URI actions. Before ANY action runs,
# two pre-flight gates make the autonomy safe and legible:
#
#   1. ROUTER  (router://, urirun-connector-router): diagnose WHERE each step runs
#      (host vs a named node) and BLOCK the plan if any step is unroutable — so the
#      agent never "acts" against a target that does not exist. You know the execution
#      LOCATION of every action before committing.
#   2. CONTRACT (urirun-contract): as each routable step executes, validate its envelope
#      against the connector's contract — so a drifted handler is caught at the boundary.
#
# `--rogue` makes the agent pick a step on a node that is NOT in the mesh; the router
# blocks the whole plan at the 'target' layer, before execution. Fully offline & deterministic.

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def _ensure_imports() -> None:
    cand = os.path.join(ROOT, "urirun", "adapters", "python")
    if os.path.isdir(cand) and cand not in sys.path:
        sys.path.insert(0, cand)


_ensure_imports()
import urirun  # noqa: E402
from urirun_connector_router import routing as router  # noqa: E402
from urirun_contract import Contract, conform, envelope_violation  # noqa: E402

# ── a tiny connector the agent can act with (host-local, deterministic) ──
audit = urirun.connector("audit", scheme="audit", target="host", meta={"label": "Node audit"})


@audit.handler("sys/query/info", meta={"label": "Read OS info"})
def sys_info() -> dict:
    import platform
    return urirun.ok(connector="audit", action="sys_info",
                     os=platform.system(), release=platform.release())


@audit.handler("proc/query/top", meta={"label": "Top process names"})
def proc_top(limit: int = 3) -> dict:
    names = ["systemd", "python3", "chrome"][:max(1, int(limit))]
    return urirun.ok(connector="audit", action="proc_top", processes=names, count=len(names))


CONTRACTS = {
    "sys/query/info": Contract(version="v1", effect="query", reversible=False, inp={},
        out={"ok": "const:true", "connector": "const:audit", "action": "const:sys_info",
             "os": "str", "release": "str"},
        examples=({"payload": {}, "result": {"ok": True, "connector": "audit",
                  "action": "sys_info", "os": "Linux", "release": "6.x"}},)),
    "proc/query/top": Contract(version="v1", effect="query", reversible=False, inp={"limit": "?int"},
        out={"ok": "const:true", "connector": "const:audit", "action": "const:proc_top",
             "processes": "list", "count": "int"},
        examples=({"payload": {}, "result": {"ok": True, "connector": "audit",
                  "action": "proc_top", "processes": [], "count": 0}},)),
}

MESH = {"nodes": [{"name": "lenovo", "url": "http://192.168.188.201:8765"}]}


def agent_plan(goal: str, rogue: bool) -> list[dict]:
    """The 'autonomous decision': a goal -> an ordered plan of URI actions. (Deterministic
    here so the example runs offline; swap for an LLM decider — see example 37.)"""
    target = "ghost" if rogue else "host"   # rogue: a node the mesh does not know
    plan = [{"uri": "audit://host/sys/query/info", "payload": {}}]
    if "process" in goal or "audit" in goal:
        plan.append({"uri": "audit://host/proc/query/top", "payload": {"limit": 3}})
    plan.append({"uri": f"kvm://{target}/screen/query/capture", "payload": {}})
    return plan


def _route_of(uri: str) -> str:
    return uri.split("://host/", 1)[1] if "://host/" in uri else ""


def run(rogue: bool = False) -> int:
    conform(CONTRACTS)
    goal = "audit this node: capture OS, top processes, then a screenshot"
    plan = agent_plan(goal, rogue)
    print(f"agent goal: {goal}")
    print(f"agent decided {len(plan)} step(s){' [ROGUE target]' if rogue else ''}\n")

    # ── GATE 1: ROUTER — where does each step run? block if any is unroutable ──
    diag = router.diagnose_plan(plan, MESH)
    print("router pre-flight — WHERE each action runs:")
    for step in diag["steps"]:
        loc = step["runsOn"] or "??"
        flag = "" if step["ok"] else f"  ✗ BLOCKED at '{step['blockedAt']}'"
        print(f"  {step['uri']:42} -> {loc}{flag}")
    if not diag["ok"]:
        print(f"\n→ plan NOT routable ({diag['blockedSteps']}) — ABORT before acting ✓")
        return 0   # the router correctly refused a doomed plan; that's success for --rogue

    # ── GATE 2: execute routable LOCAL steps, CONTRACT-guard each envelope ──
    print("\nexecuting (only routable steps) + contract guard:")
    registry = urirun.compile_registry(audit.bindings())
    violations = 0
    for step in plan:
        route = _route_of(step["uri"])
        if route not in CONTRACTS:        # e.g. the kvm screenshot routes to a node we don't run here
            print(f"  {step['uri']:42} -> routed to node (skipped in this offline demo)")
            continue
        env = urirun.run(step["uri"], registry, step["payload"], mode="execute")
        envelope = (env.get("result") or {}).get("value", {})
        problem = envelope_violation(CONTRACTS[route], envelope)
        print(f"  {step['uri']:42} -> {'OK ✓' if not problem else 'CONTRACT VIOLATION ✗ ' + str(problem)}")
        if problem:
            violations += 1
    print(f"\n→ autonomous plan routed + executed + guarded; violations: {violations}")
    return 0 if violations == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Router+contract-guarded autonomous plan")
    ap.add_argument("--rogue", action="store_true", help="agent picks an unroutable node; router blocks it")
    ap.add_argument("--both", action="store_true")
    args = ap.parse_args(argv)
    if args.both:
        print("══ routable plan ══"); a = run(False)
        print("\n══ rogue plan (router blocks) ══"); b = run(True)
        return a or b
    return run(args.rogue)


if __name__ == "__main__":
    raise SystemExit(main())
