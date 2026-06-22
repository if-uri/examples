#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Run YAML task scenarios against a urirun node over the mesh, AND watch the node's live
# event stream (SSE) in parallel — so you see each step dispatched (host side) next to
# the run/error events the node emits back as URIs (node side), in real time.
#
#   ./run_scenarios.sh                       # every scenarios/*.yaml against $NODE_URL
#   ./run_scenarios.sh scenarios/web-login.yaml
#   NODE_URL=http://192.168.188.201:8765 ./run_scenarios.sh scenarios/system-audit.yaml
#
# A scenario file is { name, description, steps: [ {uri, payload?, why?} ] } where uri
# may contain {host}/{monitor}/… placeholders (resolved to the node's name / defaults).

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8765")
PLACEHOLDERS = {"{target}": None, "{session}": None, "{host}": None,
                "{monitor}": "0", "{image_id}": "latest"}


def _load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except ModuleNotFoundError:
        return _mini_yaml(path.read_text(encoding="utf-8"))


def _mini_yaml(text: str) -> dict:
    """Tiny fallback parser for the simple scenario subset (no PyYAML required)."""
    import ast
    doc: dict = {"steps": []}
    cur: dict | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - "):
            cur = {}
            doc["steps"].append(cur)
            line = "    " + line[4:]
        m = re.match(r"\s+(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        target = cur if (cur is not None and key != "name" and key != "description"
                         and line.startswith("    ")) else doc
        if val == "":
            continue
        try:
            target[key] = ast.literal_eval(val) if val[:1] in "{[\"'" else val
        except Exception:
            target[key] = val
    return doc


# Host-side plumbing (dispatch, envelope-unwrap, $ref chaining, SSE watch) now lives in
# urirun's reusable NodeClient — the example just adds its placeholder map and event print.
try:
    from urirun.node.client import NodeClient
except ModuleNotFoundError:
    # An installed urirun that predates NodeClient leaves `urirun` bound in sys.modules,
    # so just inserting the in-repo path isn't enough — purge the cached package first so
    # the re-import resolves the monorepo source (which has urirun.node.client).
    sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))
    for _m in [k for k in list(sys.modules) if k == "urirun" or k.startswith("urirun.")]:
        del sys.modules[_m]
    from urirun.node.client import NodeClient


class Node(NodeClient):
    def concretize(self, uri: str) -> str:
        return super().concretize(uri, PLACEHOLDERS)


def watch_thread(base: str, stop: threading.Event, sink: list) -> None:
    """Background SSE subscriber: collect the node's live events while steps dispatch."""
    try:
        for ev in NodeClient(base).watch(stop=stop):
            sink.append(ev)
            mark = "" if ev.get("ok") is None else ("ok" if ev.get("ok") else "FAIL")
            print(f"      ░ node-event: {ev.get('event'):5} {ev.get('uri')} {mark} "
                  f"{ev.get('category') or ''}".rstrip(), flush=True)
    except Exception:
        return


_resolve_refs = NodeClient.resolve_refs
_value = NodeClient.value


def run_scenario(node: Node, scenario: dict) -> dict:
    name = scenario.get("name", "scenario")
    print(f"\n== scenario: {name} — {scenario.get('description', '')}")
    results: list = []
    trace: list = []
    for i, step in enumerate(scenario.get("steps", [])):
        uri = node.concretize(step.get("uri", ""))
        payload = _resolve_refs(step.get("payload", {}) or {}, [t.get("_v") for t in trace])
        try:
            env = node.run(uri, payload)
            ok = bool(env.get("ok"))
            val = _value(env)
        except urllib.error.HTTPError as e:
            ok, val = False, f"HTTP {e.code}"
        except Exception as e:  # noqa: BLE001
            ok, val = False, str(e)
        print(f"  [{i}] {uri}\n      -> {'ok' if ok else 'FAIL'}: {json.dumps(val, ensure_ascii=False)[:140]}")
        trace.append({"i": i, "uri": uri, "ok": ok, "value": val, "_v": val if ok else None,
                      "why": step.get("why", "")})
        time.sleep(0.15)  # let the matching node-event print interleave
    ok_n = sum(1 for t in trace if t["ok"])
    print(f"  result: {ok_n}/{len(trace)} steps ok")
    return {"name": name, "ok": ok_n, "total": len(trace), "trace": trace}


def main() -> int:
    base = DEFAULT_NODE
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    files = [Path(a) for a in args] if args else sorted((HERE / "scenarios").glob("*.yaml"))

    node = Node(base)
    print(f"node: {node.name} @ {base}  (live events: {'yes' if node.has_events else 'no'})")

    stop = threading.Event()
    events: list = []
    if node.has_events:
        threading.Thread(target=watch_thread, args=(base, stop, events), daemon=True).start()
        time.sleep(0.5)  # let the subscription establish before steps fire

    reports = [run_scenario(node, _load_yaml(f)) for f in files]
    time.sleep(0.5)
    stop.set()

    out = {"node": {"name": node.name, "url": base}, "scenarios": reports,
           "node_events": events}
    (HERE / "generated" / "scenarios-report.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    total_ok = sum(r["ok"] for r in reports)
    total = sum(r["total"] for r in reports)
    print(f"\n== {len(reports)} scenario(s): {total_ok}/{total} steps ok; "
          f"{len(events)} live node-events received ==")
    print("record: generated/scenarios-report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
