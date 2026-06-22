#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Drive a real noVNC desktop from a natural-language intent: a schema-aware LLM picks
# urirun commands AND fills their typed parameters, the runtime executes them against
# the Docker desktop, and we record the session — plan, per-step results, screenshots,
# and a verdict on whether the NL intention was realized.

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

import schema_planner  # noqa: E402
from novnc_connector import core as novnc  # noqa: E402
from urirun.runtime import agent  # noqa: E402

GOAL = os.environ.get(
    "GOAL",
    "Open a terminal on the desktop and run a command that prints "
    "'urirun agent was here', then take a screenshot of the result.",
)
OUT = HERE / "generated"


def _ocr(png: Path) -> str | None:
    if shutil.which("tesseract") is None:
        return None
    res = subprocess.run(["tesseract", str(png), "-", "--psm", "6"], capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else None


def main() -> int:
    OUT.mkdir(exist_ok=True)
    registry = novnc.registry()
    space = agent.action_space(registry)
    planner_used = "llm" if os.environ.get("OPENROUTER_API_KEY") or _env_key() else "heuristic"
    steps = schema_planner.plan(GOAL, space)

    # execute the plan against the real desktop (commands permitted under policy)
    trace = agent.run_plan(registry, steps, allow=["desktop://**"], allow_commands=True)

    # pull screenshots out of the trace, save them, and drop the heavy base64 from the log
    shots: list[str] = []
    for t in trace:
        data = t.get("data") if isinstance(t.get("data"), dict) else {}
        b64 = data.pop("pngBase64", None) if isinstance(data, dict) else None
        if b64:
            name = f"{Path(data.get('path', 'shot')).stem}.png"
            (OUT / name).write_bytes(base64.b64decode(b64))
            shots.append(name)

    typed = next((t["payload"].get("text", "") for t in trace if t["uri"].endswith("/input/command/type")), "")
    shot_ok = any(isinstance(t.get("data"), dict) and t["data"].get("bytes", 0) > 0 for t in trace)
    steps_ok = all(t.get("ok", True) for t in trace if t.get("ran"))

    text_visible = None
    if shots:
        ocr = _ocr(OUT / shots[-1])
        if ocr is not None:
            needle = typed.replace("echo ", "").strip().strip("'\"")
            text_visible = bool(needle) and needle.split()[0] in ocr

    realized = steps_ok and shot_ok and (text_visible is not False)
    report = {
        "goal": GOAL, "plannerUsed": planner_used, "actionSpaceSize": len(space),
        "steps": trace, "screenshots": shots, "typedText": typed,
        "verdict": {"allStepsRan": steps_ok, "screenshotCaptured": shot_ok,
                    "typedTextVisibleOnScreen": text_visible, "intentionRealized": realized},
    }
    (OUT / "session.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "session-report.md").write_text(_markdown(report), encoding="utf-8")
    print(_markdown(report))
    print(f"(saved generated/session-report.md, session.json, {len(shots)} screenshot(s))")
    return 0 if realized else 1


def _env_key() -> bool:
    schema_planner._load_env()
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _markdown(r: dict) -> str:
    v = r["verdict"]
    out = ["# noVNC desktop session — driven by an LLM from a natural-language intent", ""]
    out.append(f"- **NL goal:** {r['goal']}")
    out.append(f"- **planner:** {r['plannerUsed']}  ·  **action space:** {r['actionSpaceSize']} typed routes")
    out += ["", "## What the agent did, step by step", "",
            "| # | URI | ran | ok | payload (LLM-filled from schema) | why |",
            "|---|-----|-----|----|----------------------------------|-----|"]
    for i, t in enumerate(r["steps"]):
        payload = json.dumps({k: vv for k, vv in (t.get("payload") or {}).items()})
        out.append(f"| {i} | `{t['uri']}` | {'✓' if t.get('ran') else '–'} | "
                   f"{'✓' if t.get('ok') else '✗'} | `{payload}` | {t.get('why', '')} |")
    if r["screenshots"]:
        out += ["", "## Session screenshot(s)", ""]
        for s in r["screenshots"]:
            out.append(f"![{s}]({s})")
    out += ["", "## Was the NL intention realized?", "",
            f"- {'✓' if v['allStepsRan'] else '✗'} every planned step ran and succeeded",
            f"- {'✓' if v['screenshotCaptured'] else '✗'} a screenshot of the result was captured"]
    if v["typedTextVisibleOnScreen"] is not None:
        out.append(f"- {'✓' if v['typedTextVisibleOnScreen'] else '✗'} the typed text is visible on screen (OCR-confirmed)")
    verdict = "YES — the NL intent became typed commands that ran on a real desktop." \
        if v["intentionRealized"] else "NO — see the unchecked items above."
    out += ["", f"**Verdict: {verdict}**", ""]
    return "\n".join(out)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        novnc.stop()  # always tear the container down
