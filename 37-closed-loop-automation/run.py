#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive the three closed loops against a LIVE node with a real LLM, and save a
# session under ~/.urirun/<node>/session/closed-loop-<UTC-ts>/.
#
#   NODE_URL=http://192.168.188.201:8765 LLM_MODEL=openrouter/... python3 run.py
# (LLM_MODEL + OPENROUTER_API_KEY are read from examples/.env if you `set -a; . .env`)

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from urirun.node.client import NodeClient

import closed_loop
from planners import make_llm_decider, make_llm_planner

NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8765")
MODEL = os.environ.get("LLM_MODEL") or os.environ.get("URIRUN_LLM_MODEL")


def main() -> int:
    if not MODEL:
        print("set LLM_MODEL (and OPENROUTER_API_KEY) — e.g. `set -a; . ../.env; set +a`")
        return 2
    client = NodeClient(NODE)
    name = json.loads(urllib.request.urlopen(NODE + "/health", timeout=8).read())["name"]
    plan = make_llm_planner(MODEL)
    decide = make_llm_decider(MODEL)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sess = Path.home() / ".urirun" / name / "session" / f"closed-loop-{ts}"
    sess.mkdir(parents=True, exist_ok=True)
    report = {"node": name, "model": MODEL, "at": ts, "patterns": {}}

    print(f"node {name} · model {MODEL}\n")

    # A. self-repair
    print("== A. self-repair: NL -> flow -> execute -> repair on node error ==")
    a = closed_loop.self_repair_loop(client, "Read the kernel via uname and write a one-line audit note to the log.", plan)
    print(f"   ok={a['ok']} in {a['iterations']} iteration(s)")
    report["patterns"]["self_repair"] = {"ok": a["ok"], "iterations": a["iterations"]}

    # B. goal-verify: keep adding notes until the log holds >= 3 entries
    print("== B. goal-verify: act -> probe -> re-plan until the goal is observed ==")

    def verify(c):
        rec = c.run("log://%s/session/query/recent" % name, {"limit": 5})
        from urirun import result_data
        logs = (result_data(rec) or {}).get("logs", [])
        return (len(logs) >= 3, {"count": len(logs)})

    b = closed_loop.goal_verify_loop(client, "Make sure the session log holds at least three entries by adding notes.",
                                     plan, verify)
    print(f"   ok={b['ok']} in {b['iterations']} iteration(s)")
    report["patterns"]["goal_verify"] = {"ok": b["ok"], "iterations": b["iterations"]}

    # C. agent: observe -> one action -> repeat until done
    print("== C. agent: observe -> decide one action -> act -> repeat ==")
    c = closed_loop.agent_loop(client, "Audit this node: capture its OS, its top processes, then stop.", decide)
    print(f"   ok={c['ok']} in {c['steps']} step(s); reason: {c.get('reason')}")
    report["patterns"]["agent"] = {"ok": c["ok"], "steps": c["steps"]}

    (sess / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nsession saved: {sess}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
