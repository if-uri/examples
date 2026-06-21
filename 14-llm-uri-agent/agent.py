#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# LLM-over-URI agent loop:
#   bindings -> compile registry (the action space) -> a planner picks {uri,payload}
#   -> urirun runs it under policy (query freely, command only when allowed)
#   -> the result feeds the next step.
#
# The planner here is deterministic so the example runs in CI. To use a real LLM,
# replace `plan()` with a call to the `llm` connector (or any model): pass it the
# goal + the route list below and have it return the same {uri, payload} steps.

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

import urirun
from urirun.runtime import _runtime

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = [sys.executable, os.path.join(HERE, "tools.py")]


def load_registry() -> dict:
    raw = subprocess.run(TOOLS + ["bindings"], capture_output=True, text=True, check=True).stdout
    return urirun.compile_registry(json.loads(raw))


def action_space(registry: dict) -> list[dict]:
    """The routes an LLM would choose from (uri + input schema)."""
    return [{"uri": r["uri"], "kind": "query" if "/query/" in r["uri"] else "command",
             "label": (r.get("meta") or {}).get("label", ""),
             "inputs": list(((r.get("inputSchema") or {}).get("properties") or {}).keys())}
            for r in urirun.list_routes(registry)]


def plan(goal: str, routes: list[dict]) -> list[dict]:
    """Deterministic stand-in for an LLM. Maps a goal to a sequence of URI calls.

    A real planner sends `goal` + `routes` (the action space / MCP tools) to a
    model and gets back this same list of {uri, payload}.
    """
    have = {r["uri"] for r in routes}
    url = goal.split()[-1] if goal.split() and "://" in goal.split()[-1] else "https://example.com"
    steps = []
    if "time://host/clock/query/now" in have:
        steps.append({"uri": "time://host/clock/query/now", "payload": {}, "why": "stamp the run"})
    if "httpcheck://host/url/query/status" in have:
        steps.append({"uri": "httpcheck://host/url/query/status", "payload": {"url": url}, "why": "is the site up?"})
    if "browser://chrome/page/query/dom" in have:
        steps.append({"uri": "browser://chrome/page/query/dom", "payload": {"url": url, "max": 300}, "why": "read the page"})
    if "log://host/run/command/write" in have:
        steps.append({"uri": "log://host/run/command/write", "payload": {"event": "agent-run", "detail": url}, "why": "record the run"})
    return steps


def run_step(registry: dict, step: dict, *, allow_commands: bool) -> dict:
    uri = step["uri"]
    is_query = "/query/" in uri
    scheme = uri.split("://", 1)[0]
    policy = _runtime.build_policy(None, [f"{scheme}://*"], None)
    # query routes are read-only and run freely; command routes need permission
    if is_query or allow_commands:
        result = urirun.run(uri, registry, step["payload"], mode="execute", policy=policy)
        exec_out = result.get("result") if isinstance(result.get("result"), dict) else {}
        stdout = exec_out.get("stdout") if isinstance(exec_out, dict) else None
        try:
            data = json.loads(stdout) if stdout else exec_out
        except json.JSONDecodeError:
            data = {"stdout": stdout}
        ok = bool(result.get("ok")) and (data.get("ok", True) if isinstance(data, dict) else True)
        return {"ran": True, "ok": ok, "data": data}
    return {"ran": False, "skipped": "command not permitted (pass --allow-commands)", "uri": uri}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent", description="LLM-over-URI agent demo")
    parser.add_argument("goal", nargs="?", default="check and read https://example.com")
    parser.add_argument("--allow-commands", action="store_true", help="permit /command/ routes to execute")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    registry = load_registry()
    routes = action_space(registry)
    steps = plan(args.goal, routes)

    trace = []
    for step in steps:
        outcome = run_step(registry, step, allow_commands=args.allow_commands)
        trace.append({**step, **outcome})

    report = {"goal": args.goal, "actionSpace": routes, "steps": trace,
              "ok": all(s.get("ok", True) for s in trace if s.get("ran"))}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"goal: {args.goal}\naction space: {len(routes)} routes")
        for s in trace:
            mark = "·" if not s.get("ran") else ("✓" if s.get("ok") else "✗")
            print(f"  {mark} {s['uri']:42} {s.get('why','')}")
            if s.get("ran"):
                print(f"      -> {json.dumps(s['data'])[:140]}")
            else:
                print(f"      -> {s.get('skipped')}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
