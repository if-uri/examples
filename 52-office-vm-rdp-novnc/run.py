#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive office work on a VIRTUAL MACHINE over RDP, surfaced through a noVNC (HTML5)
# view, from natural language: the user asks (NL); a planner turns it into a
# multi-step URI flow over the VM-office MCP tool surface (vm/rdp/novnc/desktop/fs/
# clipboard/screen routes + JSON Schemas); urirun executes each step; then a
# verification step checks the simulator state to confirm the task is DONE *and*
# the session was torn down cleanly.
#
#   NL request ──► action space (MCP tools, with schemas)
#             ──► plan: [{uri, payload}, ...]   (deterministic, or --llm)
#             ──► urirun.run each step (policy-gated)  ──► mutate VM-office state
#             ──► verify(state): did the task happen AND did RDP/noVNC close cleanly?
#
# --live runs the headline finance task against a REAL noVNC desktop in Docker
# (reusing example 28's connector), proving the same plan drives an actual canvas.

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _ensure_imports() -> None:
    for rel in (("..", "..", "urirun", "adapters", "python"), ("..", "..", "urirun-connector-llm")):
        cand = os.path.normpath(os.path.join(HERE, *rel))
        if os.path.isdir(cand) and cand not in sys.path:
            sys.path.insert(0, cand)
            os.environ["PYTHONPATH"] = os.pathsep.join(p for p in (cand, os.environ.get("PYTHONPATH", "")) if p)


_ensure_imports()
import urirun  # noqa: E402

sys.path.insert(0, HERE)
import vm_office_system  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

STATE = os.path.join(HERE, ".vm_office_state.json")
os.environ["VM_OFFICE_STATE"] = STATE


def load_registry() -> dict:
    return urirun.compile_registry(vm_office_system.bindings())


def mcp_tools(registry: dict) -> list[dict]:
    """The action space projected as MCP-style tools (uri + required inputs)."""
    return [{"uri": r["uri"], "required": r.get("required", []), "inputs": r.get("inputs", [])}
            for r in urirun.action_space(registry)]


def run_step(registry: dict, uri: str, payload: dict) -> dict:
    return urirun.run_steps([{"uri": uri, "payload": payload}], registry, execute=True)[0]


def llm_planner(tools: list[dict], model: str, base_url: str, provider: str):
    from urirun_connector_llm import complete

    def plan(nl: str) -> list[dict]:
        prompt = (
            "You drive office work on a virtual machine over RDP (surfaced via noVNC) by calling URI tools. "
            "Connect over RDP before opening a noVNC view; open a view before driving the desktop; always "
            "disconnect at the end. Return ONLY a JSON array of steps "
            '[{"uri": "...", "payload": {...}}], using ONLY these tools and filling every required field:\n'
            + json.dumps(tools, ensure_ascii=False) + "\nTASK: " + nl
        )
        res = complete(prompt, model=model, base_url=base_url, provider=provider)
        if not res.get("ok"):
            raise RuntimeError(res.get("error"))
        text = res["response"].strip()
        start, end = text.find("["), text.rfind("]")
        return json.loads(text[start:end + 1]) if start >= 0 else []

    return plan


def run_scenario(scn: dict, registry: dict, planner=None) -> dict:
    if os.path.exists(STATE):
        os.remove(STATE)  # fresh fleet for each task
    allowed = {r["uri"] for r in urirun.action_space(registry)}
    steps = planner(scn["nl"]) if planner else scn["steps"]
    steps = [s for s in steps if s.get("uri") in allowed]
    trace = []
    for s in steps:
        out = run_step(registry, s["uri"], s.get("payload", {}))
        trace.append({"uri": s["uri"], "ok": out["ok"]})
        if not out["ok"]:
            break
    state = json.loads(open(STATE, encoding="utf-8").read()) if os.path.exists(STATE) else {}
    ok, detail = scn["verify"](state) if state else (False, "no state")
    return {"id": scn["id"], "nl": scn["nl"], "steps": len(steps),
            "executed": len(trace), "all_ok": all(t["ok"] for t in trace) and len(trace) == len(steps),
            "verified": bool(ok), "detail": detail, "trace": trace}


def run_live_finance() -> int:
    """Drive the headline finance task on a REAL noVNC desktop (example 28's connector)."""
    import shutil
    if shutil.which("docker") is None:
        print("--live needs Docker (it boots a noVNC desktop container)."); return 2
    ex28 = os.path.normpath(os.path.join(HERE, "..", "28-llm-novnc-desktop"))
    sys.path.insert(0, ex28)
    from novnc_connector import core as novnc  # noqa: E402
    from urirun.runtime import agent  # noqa: E402

    line = "Przychod Q3 1480000 PLN"
    plan = [
        {"uri": "desktop://novnc/session/command/start", "payload": {}},
        {"uri": "desktop://novnc/app/command/launch", "payload": {"command": "lxterminal"}},
        {"uri": "desktop://novnc/input/command/type", "payload": {"text": f"echo '{line}'", "enter": True}},
        {"uri": "desktop://novnc/screen/query/screenshot", "payload": {"name": "finance_vm"}},
        {"uri": "desktop://novnc/session/command/stop", "payload": {}},
    ]
    try:
        trace = agent.run_plan(novnc.registry(), plan, allow=["desktop://**"], allow_commands=True)
    finally:
        novnc.stop()
    ok = all(t.get("ok", True) for t in trace if t.get("ran"))
    print(f"live finance VM over noVNC: {'OK' if ok else 'FAILED'} ({len(trace)} steps on a real desktop)")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="run", description="Office work on a VM over RDP/noVNC, from NL over MCP-style URI tools")
    p.add_argument("--scenario", help="run one scenario by id (default: all)")
    p.add_argument("--llm", action="store_true", help="plan with a real model from examples/.env (default: deterministic)")
    p.add_argument("--live", action="store_true", help="run the finance task on a real noVNC desktop in Docker")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if args.live:
        return run_live_finance()

    registry = load_registry()
    tools = mcp_tools(registry)
    planner = None
    if args.llm:
        envf = os.path.normpath(os.path.join(HERE, "..", ".env"))
        if os.path.isfile(envf):
            for line in open(envf, encoding="utf-8"):
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.split(" #", 1)[0].strip().strip('"'))
        model = os.environ.get("URIRUN_LLM_MODEL") or os.environ.get("LLM_MODEL") or "llama3"
        os.environ["PYTHONUNBUFFERED"] = "1"
        planner = llm_planner(tools, model, "http://localhost:11434", "")

    chosen = [s for s in SCENARIOS if not args.scenario or s["id"] == args.scenario]
    results = []
    if not args.json:
        print(f"VM-office MCP tool surface: {len(tools)} URI tools "
              f"(schemes: {', '.join(sorted({t['uri'].split('://')[0] for t in tools}))})")
        print(f"planner: {'LLM' if planner else 'deterministic'}\n")
    for scn in chosen:
        r = run_scenario(scn, registry, planner)
        results.append(r)
        if not args.json:
            mark = "✓" if (r["verified"] and r["all_ok"]) else "✗"
            print(f"{mark} [{r['id']}] {r['steps']} steps — {scn['title']}")
            print(f"    NL: \"{r['nl']}\"")
            print(f"    executed {r['executed']}/{r['steps']} ok={r['all_ok']}  ·  verified: {r['verified']} ({r['detail']})")
    ok_all = all(r["verified"] and r["all_ok"] for r in results)
    if args.json:
        print(json.dumps({"ok": ok_all, "results": results}, ensure_ascii=False, indent=2))
    else:
        done = sum(1 for r in results if r["verified"] and r["all_ok"])
        print(f"\nRESULT: {done}/{len(results)} VM-office tasks completed AND verified")
    if os.path.exists(STATE):
        os.remove(STATE)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
