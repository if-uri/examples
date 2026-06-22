#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Roll every per-scenario run (generated/<slug>.json written by nl_scenario.py) into one
# Markdown overview: totals, a per-scenario table with both-direction stats, and links to
# the individual reports. Run after a batch of `./nl_scenario.sh "<goal>"` invocations.
#
#   python3 aggregate_report.py            # -> generated/REPORT.md

from __future__ import annotations

import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generated"


def main() -> int:
    runs = []
    for f in sorted(GEN.glob("*.json")):
        if f.name == "scenarios-report.json":
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if "trace" in d and "goal" in d:
            d["_file"] = f.with_suffix(".md").name
            runs.append(d)

    if not runs:
        print("no per-scenario reports in generated/ — run ./nl_scenario.sh first")
        return 1

    steps_ok = sum(r["ok"] for r in runs)
    steps_total = sum(r["total"] for r in runs)
    events_total = sum(len(r.get("events") or []) for r in runs)
    nodes = sorted({r.get("node", "?") for r in runs})

    L = [f"# NL scenarios — aggregate report", "",
         f"_{len(runs)} scenarios · {steps_ok}/{steps_total} steps ok · "
         f"{events_total} live node→host events · nodes: {', '.join(nodes)} · "
         f"generated {time.strftime('%Y-%m-%d %H:%M:%S')}_", "",
         "Each row is one natural-language goal turned into a YAML scenario of URIs by the "
         "LLM, dispatched to the node, with the node's events captured back — both "
         "directions of the flow verified per run.", "",
         "| scenario | goal | planner | steps ok | host→node | node→host events | report |",
         "|----------|------|---------|----------|-----------|------------------|--------|"]
    for r in runs:
        dispatched = len(r.get("trace") or [])
        evk = len(r.get("events") or [])
        L.append(f"| {r['name']} | {r['goal'][:54]} | {r.get('planner','?')} | "
                 f"{r['ok']}/{r['total']} | {dispatched} | {evk} | [md]({r['_file']}) |")

    L += ["", "## Per-scenario detail", ""]
    for r in runs:
        ev = r.get("events") or []
        ok_ev = sum(1 for e in ev if e.get("ok") is True)
        err_ev = sum(1 for e in ev if e.get("event") == "error")
        L += [f"### {r['name']}  —  {r['ok']}/{r['total']} ok",
              f"- goal: {r['goal']}",
              f"- node: `{r.get('node')}` @ {r.get('url')}  ·  planner: {r.get('planner')}",
              f"- host→node: {len(r.get('trace') or [])} steps dispatched; "
              f"node→host: {len(ev)} events ({ok_ev} ok, {err_ev} error)",
              f"- URIs: " + ", ".join(f"`{t['uri']}`" for t in (r.get('trace') or [])[:8]),
              f"- full report: [{r['_file']}]({r['_file']})", ""]

    out = GEN / "REPORT.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"== aggregate: {len(runs)} scenarios, {steps_ok}/{steps_total} steps ok, "
          f"{events_total} events -> {out.relative_to(HERE)} ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
