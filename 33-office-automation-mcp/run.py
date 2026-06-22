#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive the office computer from natural language: the user asks (NL); a planner
# turns it into a multi-step URI flow over the office MCP tool surface (the routes
# + JSON Schemas from office_system); urirun executes each step; then a
# verification step checks the simulator state to confirm the task is DONE.
#
#   NL request ──► action space (MCP tools, with schemas)
#             ──► plan: [{uri, payload}, ...]   (deterministic, or --llm)
#             ──► urirun.run each step (policy-gated)  ──► mutate office state
#             ──► verify(state): did the task actually happen?

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
import office_system  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402

STATE = os.path.join(HERE, ".office_state.json")
os.environ["OFFICE_STATE"] = STATE


def load_registry() -> dict:
    return urirun.compile_registry(office_system.bindings())


def mcp_tools(registry: dict) -> list[dict]:
    """The action space projected as MCP-style tools (uri + required inputs)."""
    return [{"uri": r["uri"], "required": r.get("required", []), "inputs": r.get("inputs", [])}
            for r in urirun.action_space(registry)]


def run_step(registry: dict, uri: str, payload: dict) -> dict:
    scheme = uri.split("://", 1)[0]
    env = urirun.run(uri, registry, payload, mode="execute", policy=urirun.policy(allow=[f"{scheme}://*"]))
    data = urirun.result_data(env)
    # argv-template routes return {stdout: "<json>"} — unwrap the tool's own JSON
    if isinstance(data, dict) and "stdout" in data:
        try:
            data = json.loads(data["stdout"])
        except (ValueError, TypeError):
            pass
    ok = bool(env.get("ok")) and (data.get("ok", True) if isinstance(data, dict) else True)
    return {"ok": ok, "data": data}


def llm_planner(tools: list[dict], model: str, base_url: str, provider: str):
    from urirun_connector_llm import complete

    def plan(nl: str) -> list[dict]:
        prompt = (
            "You drive an office computer by calling URI tools. Return ONLY a JSON array of steps "
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
        os.remove(STATE)  # fresh office for each task
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


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="run", description="Office automation from NL over MCP-style URI tools")
    p.add_argument("--scenario", help="run one scenario by id (default: all)")
    p.add_argument("--llm", action="store_true", help="plan with a real model from examples/.env (default: deterministic)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

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
        print(f"office MCP tool surface: {len(tools)} URI tools "
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
        print(f"\nRESULT: {done}/{len(results)} office tasks completed AND verified")
    if os.path.exists(STATE):
        os.remove(STATE)
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
