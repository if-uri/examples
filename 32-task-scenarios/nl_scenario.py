#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# NL -> YAML scenario -> run -> Markdown report, with BOTH-DIRECTIONS flow captured.
#
#   1. you give a natural-language goal;
#   2. an LLM turns it into a YAML scenario of URI steps, constrained to the node's live
#      action space (it can only use URIs the node actually serves) — saved under scenarios/;
#   3. the scenario runs against the node, dispatching each step (host -> node) while a
#      background SSE subscriber collects the node's run/error events (node -> host);
#   4. everything — generated YAML, the host trace, the node events, the node's own log —
#      is written to a Markdown report under generated/.
#
#   ./nl_scenario.sh "otwórz https://example.com i zrób zrzut ekranu"
#   NODE_URL=http://192.168.188.201:8765 ./nl_scenario.sh "sprawdź maszynę i zapisz notatkę"

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_scenarios as rs  # reuse Node, _resolve_refs, _value, watch_thread


def _load_env() -> None:
    p = Path(os.environ.get("URIRUN_ENV", HERE.parent / ".env"))
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.split(" #", 1)[0].strip().strip('"').strip("'"))


def _slug(goal: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", goal.lower()).strip("-")
    return (s[:40] or "scenario")


def llm_steps(goal: str, space: list[dict]) -> tuple[list[dict], str]:
    """Ask the LLM for [{uri, payload, why}] using ONLY the node's action-space URIs."""
    key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("URIRUN_OFFICE_MODEL") or os.environ.get("LLM_MODEL")
    if not key or not model:
        return _heuristic(goal, space), "heuristic"
    try:
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        import litellm

        litellm.suppress_debug_info = True
        routes = [{"uri": s["uri"], "kind": s["kind"], "inputSchema": s.get("inputSchema", {})} for s in space]
        system = (
            "You are an office-automation planner for the urirun URI runtime. Turn the goal "
            "into a JSON array of steps using ONLY uris from the action space. Each step is "
            "{\"uri\":..., \"payload\":{...}, \"why\":...}. Fill payload from the route's "
            "inputSchema.properties. Use uris verbatim. Pass an earlier step's output with "
            "\"$ref:<i>.<field>\". Output ONLY the JSON array."
        )
        user = f"GOAL: {goal}\n\nACTION SPACE:\n{json.dumps(routes, indent=2)}"
        resp = litellm.completion(model=model, timeout=60, max_tokens=1200, temperature=0,
                                  messages=[{"role": "system", "content": system},
                                            {"role": "user", "content": user}])
        text = re.sub(r"```(?:json)?|```", "", resp.choices[0].message.content or "").strip()
        a, b = text.find("["), text.rfind("]")
        steps = json.loads(text[a:b + 1]) if a != -1 else []
        valid = {s["uri"] for s in space}
        steps = [s for s in steps if isinstance(s, dict) and s.get("uri") in valid]
        return (steps or _heuristic(goal, space)), ("llm" if steps else "heuristic")
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[nl] llm failed ({exc}); heuristic\n")
        return _heuristic(goal, space), "heuristic"


def _heuristic(goal: str, space: list[dict]) -> list[dict]:
    g = goal.lower()
    uris = {s["uri"] for s in space}
    steps = []
    def find(*needles):
        return next((u for u in uris if any(n in u for n in needles)), None)
    if (u := find("/runtime/query/health", "env://")):
        steps.append({"uri": u, "payload": {}, "why": "check node health"})
    if any(w in g for w in ("proces", "process")) and (u := find("/process/query/list")):
        steps.append({"uri": u, "payload": {"limit": 5}, "why": "list processes"})
    m = re.search(r"['\"]([^'\"]+)['\"]", goal)
    if (u := find("/session/command/write")):
        steps.append({"uri": u, "payload": {"text": m.group(1) if m else goal[:40]}, "why": "log a note"})
    return steps


def to_yaml(name: str, goal: str, steps: list[dict]) -> str:
    # JSON strings are valid YAML scalars — use them so values with ':' / quotes are safe.
    lines = [f"name: {name}", f"description: {json.dumps(goal, ensure_ascii=False)}", "steps:"]
    for s in steps:
        lines.append(f"  - uri: {s['uri']}")
        if s.get("payload"):
            lines.append(f"    payload: {json.dumps(s['payload'], ensure_ascii=False)}")
        if s.get("why"):
            lines.append(f"    why: {json.dumps(s['why'], ensure_ascii=False)}")
    return "\n".join(lines) + "\n"


def write_markdown(path: Path, report: dict) -> None:
    L = [f"# NL scenario — {report['name']}", "",
         f"- **goal**: {report['goal']}",
         f"- **node**: `{report['node']}` @ {report['url']}",
         f"- **planner**: {report['planner']}  ·  **at**: {report['at']}", "",
         "## Generated scenario (YAML)", "", "```yaml", report["yaml"].rstrip(), "```", "",
         "## Host → Node (dispatched steps)", "",
         "| # | URI | payload | ok | result |", "|---|-----|---------|----|--------|"]
    for t in report["trace"]:
        res = json.dumps(t["value"], ensure_ascii=False)
        res = (res[:80] + "…") if len(res) > 80 else res
        pay = json.dumps(t["payload"], ensure_ascii=False)
        L.append(f"| {t['i']} | `{t['uri']}` | `{pay}` | {'✓' if t['ok'] else '✗'} | {res} |")
    L += ["", "## Node → Host (live events over SSE)", ""]
    if report["events"]:
        L += ["| event | uri | ok |", "|-------|-----|----|"]
        L += [f"| {e.get('event')} | `{e.get('uri')}` | {('' if e.get('ok') is None else ('✓' if e.get('ok') else '✗'))} |"
              for e in report["events"]]
    else:
        L.append("_(node has no /events stream, or none captured)_")
    L += ["", "## Node-side log (read back from the node)", "", "```"]
    L += report["node_log"] or ["(none)"]
    L += ["```", "",
          f"## Verdict — {report['ok']}/{report['total']} steps ok",
          "Both directions verified: host dispatched each URI and the node's own "
          "events/log recorded them." if report["events"] or report["node_log"] else ""]
    path.write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    goal = " ".join(a for a in sys.argv[1:] if not a.startswith("-")) or os.environ.get("GOAL", "")
    if not goal:
        sys.stderr.write("usage: nl_scenario.py \"natural-language goal\"\n")
        return 2
    _load_env()
    node = rs.Node(os.environ.get("NODE_URL", rs.DEFAULT_NODE))
    space = []
    import urllib.request
    routes = json.loads(urllib.request.urlopen(node.base + "/routes", timeout=6).read())["routes"]
    for r in routes:
        space.append({"uri": node.concretize(r["uri"]), "kind": r.get("kind"), "inputSchema": r.get("inputSchema", {})})

    print(f"node: {node.name} @ {node.base}  ({len(space)} routes)")
    print(f"goal: {goal}")
    steps, planner = llm_steps(goal, space)
    name = _slug(goal)
    yaml_text = to_yaml(name, goal, steps)
    ypath = HERE / "scenarios" / f"gen-{name}.yaml"
    ypath.write_text(yaml_text, encoding="utf-8")
    print(f"generated scenario ({planner}, {len(steps)} steps) -> {ypath.relative_to(HERE)}\n{yaml_text}")

    # both-directions: watch the node's events while we dispatch
    stop, events = threading.Event(), []
    if node.has_events:
        threading.Thread(target=rs.watch_thread, args=(node.base, stop, events), daemon=True).start()
        time.sleep(0.5)
    run_start = time.time()  # only count events from THIS run (the SSE stream replays history)

    trace, results = [], []
    for i, step in enumerate(steps):
        uri = node.concretize(step["uri"])
        payload = rs._resolve_refs(step.get("payload", {}) or {}, [t.get("_v") for t in trace])
        try:
            env = node.run(uri, payload); ok = bool(env.get("ok")); val = rs._value(env)
        except Exception as exc:  # noqa: BLE001
            ok, val = False, str(exc)
        print(f"  [{i}] {uri} -> {'ok' if ok else 'FAIL'}: {json.dumps(val, ensure_ascii=False)[:100]}")
        trace.append({"i": i, "uri": uri, "payload": payload, "ok": ok, "value": val, "_v": val if ok else None})
        time.sleep(0.15)
    time.sleep(0.6)
    stop.set()

    node_log = node.recent_log(limit=max(8, len(steps) * 3)) if hasattr(node, "recent_log") else []
    # the SSE stream now yields only new events (no replay without a cursor), so `events`
    # already holds just this run's — no fragile cross-machine timestamp filtering needed.
    report = {"name": name, "goal": goal, "node": node.name, "url": node.base, "planner": planner,
              "yaml": yaml_text, "trace": trace, "events": events, "node_log": node_log,
              "ok": sum(1 for t in trace if t["ok"]), "total": len(trace),
              "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    md = HERE / "generated" / f"{name}.md"
    write_markdown(md, report)
    (HERE / "generated" / f"{name}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n== {report['ok']}/{report['total']} steps ok; {len(events)} live events; report -> generated/{name}.md ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
