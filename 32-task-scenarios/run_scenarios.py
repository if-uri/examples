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


def _get(url: str, timeout: float = 6.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url: str, body: dict, timeout: float = 60.0) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class Node:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        h = _get(self.base + "/health")
        self.name = h.get("name", "node")
        self.has_events = "events" in h

    def concretize(self, uri: str) -> str:
        from urllib.parse import unquote
        uri = unquote(uri)  # /routes percent-encodes inner braces: %7Bmonitor%7D
        for ph, default in PLACEHOLDERS.items():
            uri = uri.replace(ph, default if default is not None else self.name)
        return uri

    def run(self, uri: str, payload: dict) -> dict:
        return _post(self.base + "/run", {"uri": uri, "payload": payload})

    def recent_log(self, limit: int = 12) -> list:
        """Read the node's own log back (the other direction): handles both the default
        node's `logs` key and this example's base-route `lines` key."""
        uri = f"log://{self.name}/session/query/recent"
        try:
            env = self.run(uri, {"limit": limit})
            out = (env.get("result") or {}).get("stdout") or "{}"
            data = json.loads(out)
            return data.get("logs") or data.get("lines") or []
        except Exception:
            return []


def watch_thread(base: str, stop: threading.Event, sink: list) -> None:
    """Background SSE subscriber: collect the node's live events while steps dispatch."""
    try:
        req = urllib.request.Request(base.rstrip("/") + "/events",
                                     headers={"Accept": "text/event-stream"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            for raw in resp:
                if stop.is_set():
                    return
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("data:") and line[5:].strip():
                    try:
                        ev = json.loads(line[5:].strip())
                    except Exception:
                        continue
                    sink.append(ev)
                    mark = "" if ev.get("ok") is None else ("ok" if ev.get("ok") else "FAIL")
                    print(f"      ░ node-event: {ev.get('event'):5} {ev.get('uri')} {mark} "
                          f"{ev.get('category') or ''}".rstrip(), flush=True)
    except Exception:
        return


def _resolve_refs(payload, results):
    if isinstance(payload, dict):
        return {k: _resolve_refs(v, results) for k, v in payload.items()}
    if isinstance(payload, list):
        return [_resolve_refs(v, results) for v in payload]
    if isinstance(payload, str) and payload.startswith("$ref:"):
        m = re.match(r"\$ref:(\d+)\.([\w.]+)", payload)
        if m and int(m.group(1)) < len(results):
            cur = results[int(m.group(1))]
            for part in m.group(2).split("."):
                cur = (cur or {}).get(part) if isinstance(cur, dict) else None
            return cur if cur is not None else payload
    return payload


def _value(env: dict):
    res = env.get("result") or {}
    if "value" in res:
        return res["value"]
    out = res.get("stdout")
    if isinstance(out, str):
        try:
            return json.loads(out)
        except Exception:
            return out
    return res if env.get("ok") else env.get("error")


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
