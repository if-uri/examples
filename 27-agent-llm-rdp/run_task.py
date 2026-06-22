#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive a computer-control task with the LLM planner over the REAL tellmesh URI
# surface (rdp + kvm + screen + ocr + llm), and RECORD what happened sequentially:
# the goal, the action space offered, the plan the agent chose (with its reasoning),
# each step's dispatch outcome, and a verdict on whether the intention was realized.
#
# Steps run in dry-run: the real tellmesh handlers need the whole monorepo to execute,
# but dry-run resolves each URI, validates it, and applies the policy gate — which is
# exactly what "did the agent produce a valid, permitted plan for the goal" needs.

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import llm_planner  # noqa: E402
from urirun import v2  # noqa: E402
from urirun.runtime import _runtime as runtime, adopt_pack, agent  # noqa: E402

TELLMESH = Path(os.environ.get("TELLMESH_DIR", HERE / ".." / ".." / ".." / "tellmesh")).resolve()
PACKS = ["urirdp", "urikvm", "uriscreen", "uriocr", "urillm"]
GOAL = os.environ.get(
    "GOAL",
    "Control the computer over RDP: open the RDP target, take a screenshot of the "
    "remote screen with the kvm connector, OCR the screen text, then decide the next action.",
)
ALLOW = ["rdp://**", "kvm://**", "screen://**", "ocr://**", "llm://**"]


def _manifest(pack: str) -> Path | None:
    hits = list((TELLMESH / pack).rglob("manifest.yaml"))
    return hits[0] if hits else None


def build_registry() -> dict:
    bindings: dict[str, dict] = {}
    for pack in PACKS:
        m = _manifest(pack)
        if not m:
            continue
        for uri, b in adopt_pack.adopt(str(m))["bindings"].items():
            bindings[uri] = b
    if not bindings:
        raise SystemExit(f"no tellmesh manifests under {TELLMESH}; set TELLMESH_DIR")
    return v2.compile_registry({"version": "urirun.bindings.v2", "bindings": bindings})


def run() -> dict:
    registry = build_registry()
    space = agent.action_space(registry)
    planner_used = "llm" if (os.environ.get("OPENROUTER_API_KEY") or _env_has_key()) else "heuristic"
    steps = llm_planner.plan(GOAL, space)

    policy = runtime.build_policy(None, ALLOW, None)
    trace = []
    for i, step in enumerate(steps):
        uri = step.get("uri", "")
        env = v2.run(uri, registry, payload=step.get("payload", {}), mode="dry-run", policy=policy)
        trace.append({
            "i": i, "uri": uri, "why": step.get("why", ""),
            "payload": step.get("payload", {}),
            "resolved": bool(env.get("ok")),
            "kind": env.get("kind"), "adapter": env.get("adapter"),
            "decision": (env.get("decision") or {}).get("allowed"),
        })

    # intention realized? the goal asks for RDP + a screenshot + OCR + a decision,
    # and every chosen step must resolve to a permitted URI.
    schemes = [t["uri"].split("://", 1)[0] for t in trace]
    uris = " ".join(t["uri"] for t in trace)
    covered = {
        "rdp": "rdp" in schemes,
        "screenshot": ("screenshot" in uris or "/capture" in uris),
        "ocr": "ocr" in schemes,
        "decide/analyze": any(k in uris for k in ("decide", "analyze", "/plan")),
    }
    all_resolved = all(t["resolved"] for t in trace) and bool(trace)
    realized = all(covered.values()) and all_resolved
    return {
        "goal": GOAL, "plannerUsed": planner_used,
        "actionSpaceSize": len(space), "steps": trace,
        "coverage": covered, "allStepsResolved": all_resolved, "intentionRealized": realized,
    }


def _env_has_key() -> bool:
    llm_planner._load_env()
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def to_markdown(report: dict) -> str:
    lines = ["# Agent run log — computer control over RDP (tellmesh URIs)", ""]
    lines.append(f"- **goal:** {report['goal']}")
    lines.append(f"- **planner:** {report['plannerUsed']}  ·  **action space:** {report['actionSpaceSize']} routes")
    lines.append("")
    lines.append("## What happened, step by step")
    lines.append("")
    lines.append("| # | URI | resolved | permitted | adapter | why |")
    lines.append("|---|-----|----------|-----------|---------|-----|")
    for t in report["steps"]:
        lines.append(f"| {t['i']} | `{t['uri']}` | {'✓' if t['resolved'] else '✗'} | "
                     f"{'✓' if t['decision'] else '✗'} | {t['adapter']} | {t['why']} |")
    lines.append("")
    lines.append("## Was the intention realized?")
    lines.append("")
    for cap, ok in report["coverage"].items():
        lines.append(f"- {'✓' if ok else '✗'} {cap}")
    lines.append(f"- {'✓' if report['allStepsResolved'] else '✗'} every chosen URI resolved + permitted")
    lines.append("")
    verdict = "YES — the agent composed a valid, permitted plan covering the whole goal." \
        if report["intentionRealized"] else "NO — see the unchecked items above."
    lines.append(f"**Verdict: {verdict}**")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = run()
    out_dir = HERE / "generated"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "run-log.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = to_markdown(report)
    (out_dir / "run-log.md").write_text(md, encoding="utf-8")
    print(md)
    print("(saved generated/run-log.md and run-log.json)")
    return 0 if report["intentionRealized"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
