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

HERE = os.path.dirname(os.path.abspath(__file__))


def _ensure_urirun() -> None:
    """Let `import urirun` work even when it isn't installed — OR when an old urirun
    is installed (e.g. a base conda with 0.3.x) — by falling back to the adapter
    checkout beside this repo. The example needs the v2 public API (`compile_registry`),
    so a stale install is treated the same as a missing one. Keeps `pytest` /
    `python3 agent.py` runnable from any environment without activating a venv."""
    try:
        import urirun
        if hasattr(urirun, "compile_registry"):
            return  # installed urirun is recent enough
    except ModuleNotFoundError:
        pass
    candidate = os.path.normpath(os.path.join(HERE, "..", "..", "urirun", "adapters", "python"))
    if not os.path.isdir(candidate):
        return  # no source checkout to fall back to; surface the original error later
    sys.path.insert(0, candidate)
    # propagate to child processes (the connector CLIs import urirun too)
    os.environ["PYTHONPATH"] = os.pathsep.join(
        p for p in (candidate, os.environ.get("PYTHONPATH", "")) if p
    )
    # drop a stale already-imported urirun so the checkout wins on the next import
    for name in [m for m in list(sys.modules) if m == "urirun" or m.startswith("urirun.")]:
        del sys.modules[name]


_ensure_urirun()

import urirun

TOOLS = [sys.executable, os.path.join(HERE, "tools.py")]

# The real browser connector lives beside this repo as a sibling package. When it
# is present we reuse it instead of tools.py's inline browser:// route — the same
# action space, but backed by a packaged connector (headless Chrome dom/text/
# screenshot + desktop open) rather than a demo stub.
BROWSER_CONNECTOR_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "urirun-connector-browser-control"))


def browser_control_bindings() -> dict | None:
    """Reuse the `urirun-connector-browser-control` package when available.

    The connector now ships ``local-function`` routes (``@handler``); with
    ``isolated=True`` they run out-of-process through the shared
    ``python -m urirun.exec`` runner, which already uses ``sys.executable``. The
    agent reuses those bindings as-is — it only needs the connector dir on
    ``PYTHONPATH`` (below) so the runner can import it. The argv rewrite further
    down is a harmless no-op for the migrated routes and still covers any legacy
    ``argv-template`` route whose argv starts with ``python3``.

    The connector dir is added to ``sys.path``/``PYTHONPATH`` so it imports here and
    in the spawned subprocess — no install needed. Returns None when the connector
    can't be loaded, in which case the agent falls back to tools.py's inline route.
    """
    if os.path.isdir(BROWSER_CONNECTOR_DIR):
        if BROWSER_CONNECTOR_DIR not in sys.path:
            sys.path.insert(0, BROWSER_CONNECTOR_DIR)
        os.environ["PYTHONPATH"] = os.pathsep.join(
            p for p in (BROWSER_CONNECTOR_DIR, os.environ.get("PYTHONPATH", "")) if p
        )
    try:
        import urirun_connector_browser_control as browser_control
    except Exception:  # noqa: BLE001 - connector is optional; fall back to the stub
        return None
    doc = browser_control.urirun_bindings()
    for binding in (doc.get("bindings") or {}).values():
        argv = binding.get("argv") or []
        if argv and argv[0] in ("python3", "python"):
            binding["argv"] = [sys.executable, *argv[1:]]
    return doc


def load_registry() -> dict:
    raw = subprocess.run(TOOLS + ["bindings"], capture_output=True, text=True, check=True).stdout
    doc = json.loads(raw)
    connector = browser_control_bindings()
    if connector and connector.get("bindings"):
        # the packaged connector owns the browser:// surface; drop tools.py's stub
        doc["bindings"] = {k: v for k, v in doc["bindings"].items() if not k.startswith("browser://")}
        doc["bindings"].update(connector["bindings"])
    return urirun.compile_registry(doc)


def browser_backend(registry: dict) -> str:
    """Which connector serves the browser:// routes in this registry."""
    uris = {r["uri"] for r in urirun.list_routes(registry)}
    return "urirun-connector-browser-control" if "browser://desktop/page/command/open" in uris else "tools.py (inline stub)"


def action_space(registry: dict) -> list[dict]:
    """The routes an LLM would choose from (uri + kind + input schema) — the public
    projection, identical to urirun's MCP tool list."""
    return urirun.action_space(registry)


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
    # the real connector adds a cleaner page/query/text route; prefer it when present
    read_uri = next((u for u in ("browser://chrome/page/query/text", "browser://chrome/page/query/dom") if u in have), None)
    if read_uri:
        steps.append({"uri": read_uri, "payload": {"url": url, "max": 300}, "why": "read the page"})
    if "log://host/run/command/write" in have:
        steps.append({"uri": "log://host/run/command/write", "payload": {"event": "agent-run", "detail": url}, "why": "record the run"})
    return steps


def run_step(registry: dict, step: dict, *, allow_commands: bool) -> dict:
    uri = step["uri"]
    is_query = "/query/" in uri
    scheme = uri.split("://", 1)[0]
    # query routes are read-only and run freely; command routes need permission
    if is_query or allow_commands:
        # public API: urirun.policy() builds the allow policy, urirun.result_data()
        # unwraps the connector payload from the run envelope (local-function value,
        # argv stdout JSON or fetch result) — no urirun.runtime._runtime needed.
        env = urirun.run(uri, registry, step["payload"], mode="execute",
                         policy=urirun.policy(allow=[f"{scheme}://*"]))
        data = urirun.result_data(env)
        ok = bool(env.get("ok")) and (data.get("ok", True) if isinstance(data, dict) else True)
        return {"ran": True, "ok": ok, "data": data}
    return {"ran": False, "skipped": "command not permitted (pass --allow-commands)", "uri": uri}


def load_flow_steps(path: str) -> list[dict]:
    """Read a ready urirun flow YAML into a list of {uri, payload} steps."""
    import yaml
    doc = yaml.safe_load(open(path, encoding="utf-8").read()) or {}
    return [{"uri": s["uri"], "payload": s.get("payload", {}), "why": f"flow step {s.get('id', '')}".strip()}
            for s in doc.get("steps", [])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent", description="LLM-over-URI agent demo")
    parser.add_argument("goal", nargs="?", default="check and read https://example.com")
    parser.add_argument("--allow-commands", action="store_true", help="permit /command/ routes to execute")
    parser.add_argument("--flow", metavar="YAML", help="run a ready YAML flow file instead of planning (e.g. flows/web-recon.yaml)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    registry = load_registry()
    routes = action_space(registry)
    steps = load_flow_steps(args.flow) if args.flow else plan(args.goal, routes)

    trace = []
    for step in steps:
        outcome = run_step(registry, step, allow_commands=args.allow_commands)
        trace.append({**step, **outcome})

    report = {"goal": args.goal, "browser": browser_backend(registry), "actionSpace": routes, "steps": trace,
              "ok": all(s.get("ok", True) for s in trace if s.get("ran"))}
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"goal: {args.goal}\naction space: {len(routes)} routes  (browser: {report['browser']})")
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
