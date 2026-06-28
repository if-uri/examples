#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Live host/node scenario matrix for safe autonomy smoke tests.

The goal is not to prove one happy path. It separates:
  * host dashboard reachability,
  * node reachability and route surface,
  * transport success,
  * inner URI result success,
  * degraded GUI/capture results.

Default scenarios are read-only or low-impact. The web scenario may reuse/open a CDP browser
session and navigate it to example.com, but does not click or type into arbitrary pages.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
GENERATED = HERE / "generated"

try:
    from urirun.node.client import NodeClient
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))
    for _m in [k for k in list(sys.modules) if k == "urirun" or k.startswith("urirun.")]:
        del sys.modules[_m]
    from urirun.node.client import NodeClient


@dataclass(frozen=True)
class Step:
    id: str
    uri: str
    payload: dict[str, Any] = field(default_factory=dict)
    expect: str = "ok"  # ok | non_degraded_capture


@dataclass(frozen=True)
class Scenario:
    id: str
    description: str
    steps: tuple[Step, ...]


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        "node-basics",
        "runtime health, process listing, and shell facts",
        (
            Step("health", "env://{node}/runtime/query/health"),
            Step("processes", "proc://{node}/process/query/list", {"limit": 5}),
            Step("date", "shell://{node}/command/date"),
            Step("uname", "shell://{node}/command/uname"),
            Step("which-python", "shell://{node}/command/which", {"binary": "python3"}),
        ),
    ),
    Scenario(
        "node-log-roundtrip",
        "write a node log note and read it back",
        (
            Step("write-log", "log://{node}/session/command/write", {"text": "host-node-matrix smoke"}),
            Step("read-log", "log://{node}/session/query/recent", {"limit": 5}),
        ),
    ),
    Scenario(
        "gui-diagnostics",
        "non-mutating KVM environment and desktop diagnostics",
        (
            Step("kvm-env", "kvm://host/env/query/profile"),
            Step("display", "kvm://host/display/query/info"),
            Step("doctor", "kvm://host/doctor/query/report"),
            Step("windows", "kvm://host/window/query/list"),
            Step("surface", "kvm://host/surface/query/current"),
        ),
    ),
    Scenario(
        "cdp-web-readonly",
        "ensure CDP, navigate to example.com, wait for readiness, capture with quality check",
        (
            Step("cdp-ensure", "kvm://host/cdp/session/command/ensure"),
            Step("cdp-ready", "kvm://host/cdp/session/query/ready"),
            Step("navigate-example", "kvm://host/cdp/page/command/navigate", {"url": "https://example.com/"}),
            Step("page-ready", "kvm://host/cdp/page/query/ready"),
            Step("capture", "kvm://host/screen/query/capture", {"base64": False}, "non_degraded_capture"),
        ),
    ),
)


def _json_get(url: str, timeout: float = 4.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _load_mesh(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"nodes": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"nodes": [], "error": str(exc), "path": str(path)}


def _mesh_nodes() -> list[dict[str, Any]]:
    candidates = [
        Path(os.environ.get("URIRUN_MESH", "")) if os.environ.get("URIRUN_MESH") else None,
        ROOT / "urirun" / ".urirun" / "mesh.json",
        ROOT / ".urirun" / "mesh.json",
    ]
    out: list[dict[str, Any]] = []
    seen = set()
    for path in [p for p in candidates if p]:
        for node in _load_mesh(path).get("nodes") or []:
            name, url = node.get("name"), node.get("url")
            if not name or not url or (name, url) in seen:
                continue
            seen.add((name, url))
            out.append({"name": name, "url": url, "tags": node.get("tags") or [], "source": str(path)})
    extra = os.environ.get("NODE_URLS", "")
    for item in [x.strip() for x in extra.split(",") if x.strip()]:
        if "=" in item:
            name, url = item.split("=", 1)
        else:
            url = item
            name = url.rsplit(":", 1)[-1].replace("/", "") or "node"
        if (name, url) not in seen:
            out.append({"name": name, "url": url, "tags": ["env:NODE_URLS"], "source": "env"})
    return out


def _route_key(uri: str) -> tuple[str, str]:
    try:
        scheme, rest = uri.split("://", 1)
        parts = rest.split("/", 1)
        return scheme, parts[1] if len(parts) > 1 else ""
    except ValueError:
        return uri, ""


def _available(routes: list[dict[str, Any]], uri: str) -> bool:
    want = _route_key(uri)
    return any(_route_key(str(route.get("uri", ""))) == want for route in routes)


def _contains_degraded(value: Any) -> bool:
    if isinstance(value, dict):
        if value.get("degraded") is True:
            return True
        return any(_contains_degraded(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_degraded(v) for v in value)
    return False


def _verdict(step: Step, env: dict[str, Any], value: Any) -> tuple[str, str]:
    if not env.get("ok"):
        return "fail", str(env.get("error") or "transport not ok")
    if isinstance(value, dict) and value.get("ok") is False:
        return "fail", str(value.get("error") or "inner result not ok")
    if _contains_degraded(value):
        return "degraded", "inner result is degraded"
    if step.expect == "non_degraded_capture":
        if not isinstance(value, dict):
            return "fail", "capture did not return an object"
        size = int(value.get("bytes") or 0)
        if size < int(os.environ.get("MIN_REAL_CAPTURE_BYTES", "20000")):
            return "degraded", f"capture too small ({size} bytes)"
        if not value.get("path"):
            return "fail", "capture missing path"
    return "pass", ""


def _summarize(value: Any, limit: int = 420) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= limit else text[:limit] + "..."


def probe_dashboard(url: str) -> dict[str, Any]:
    base = url.rstrip("/")
    out: dict[str, Any] = {"url": base, "ok": False}
    try:
        out["health"] = _json_get(base + "/health")
        out["ok"] = bool(out["health"].get("ok", True))
    except Exception as exc:  # noqa: BLE001
        out["error"] = str(exc)
        return out
    try:
        nodes = _json_get(base + "/api/nodes", timeout=8.0)
        out["nodes"] = nodes.get("nodes") or []
        out["reachableNodes"] = [n.get("name") for n in out["nodes"] if n.get("reachable")]
    except Exception as exc:  # noqa: BLE001
        out["nodesError"] = str(exc)
    return out


def run_node_matrix(node_def: dict[str, Any], scenarios: tuple[Scenario, ...]) -> dict[str, Any]:
    node_report: dict[str, Any] = {
        "name": node_def.get("name"),
        "url": node_def.get("url"),
        "tags": node_def.get("tags") or [],
        "source": node_def.get("source"),
        "ok": False,
        "scenarios": [],
    }
    try:
        node = NodeClient(str(node_def["url"]))
        node_report.update({"ok": True, "nodeName": node.name, "version": node.version, "hasEvents": node.has_events})
        routes = node.routes()
        node_report["routeCount"] = len(routes)
        node_report["schemes"] = sorted({str(r.get("uri", "")).split("://", 1)[0] for r in routes})
    except Exception as exc:  # noqa: BLE001
        node_report["error"] = str(exc)
        return node_report

    for scenario in scenarios:
        scenario_report = {"id": scenario.id, "description": scenario.description, "steps": []}
        for step in scenario.steps:
            uri = step.uri.format(node=node.name)
            record: dict[str, Any] = {"id": step.id, "uri": uri, "payload": step.payload}
            if not _available(routes, uri):
                record.update({"status": "skip", "reason": "route not advertised"})
                scenario_report["steps"].append(record)
                continue
            started = time.time()
            try:
                env = node.run(uri, step.payload, timeout=45)
                value = NodeClient.value(env)
                status, reason = _verdict(step, env, value)
                record.update({
                    "status": status,
                    "reason": reason,
                    "elapsedMs": round((time.time() - started) * 1000),
                    "value": value,
                    "summary": _summarize(value),
                })
            except Exception as exc:  # noqa: BLE001
                record.update({
                    "status": "fail",
                    "reason": str(exc),
                    "elapsedMs": round((time.time() - started) * 1000),
                })
            scenario_report["steps"].append(record)
            time.sleep(0.1)
        counts = {}
        for rec in scenario_report["steps"]:
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
        scenario_report["counts"] = counts
        node_report["scenarios"].append(scenario_report)
    return node_report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Host/Node Scenario Matrix",
        "",
        f"- generated: `{report['generatedAt']}`",
        f"- dashboard: `{report['dashboard'].get('url')}` -> {'ok' if report['dashboard'].get('ok') else 'fail'}",
        "",
        "## Scenario Ideas",
        "",
    ]
    for scenario in SCENARIOS:
        lines.append(f"- `{scenario.id}`: {scenario.description}")
    lines += ["", "## Results", ""]
    for node in report["nodes"]:
        lines.append(f"### {node.get('name')} @ {node.get('url')}")
        if not node.get("ok"):
            lines += ["", f"FAIL: `{node.get('error')}`", ""]
            continue
        lines += ["", f"routes: `{node.get('routeCount')}`, schemes: `{', '.join(node.get('schemes') or [])}`", ""]
        lines += ["| scenario | pass | degraded | fail | skip |", "|---|---:|---:|---:|---:|"]
        for scenario in node["scenarios"]:
            counts = scenario["counts"]
            lines.append(
                f"| `{scenario['id']}` | {counts.get('pass', 0)} | {counts.get('degraded', 0)} | "
                f"{counts.get('fail', 0)} | {counts.get('skip', 0)} |"
            )
        lines.append("")
        for scenario in node["scenarios"]:
            bad = [s for s in scenario["steps"] if s["status"] in {"fail", "degraded"}]
            if not bad:
                continue
            lines.append(f"Problems in `{scenario['id']}`:")
            for step in bad:
                lines.append(f"- `{step['id']}` `{step['uri']}` -> {step['status']}: {step.get('reason')}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", default=os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8194"))
    parser.add_argument("--node", action="append", help="Limit to node name (repeatable)")
    parser.add_argument("--scenario", action="append", help="Limit to scenario id (repeatable)")
    args = parser.parse_args()

    wanted_nodes = set(args.node or [])
    wanted_scenarios = set(args.scenario or [])
    scenarios = tuple(s for s in SCENARIOS if not wanted_scenarios or s.id in wanted_scenarios)
    nodes = [n for n in _mesh_nodes() if not wanted_nodes or n.get("name") in wanted_nodes]

    report = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dashboard": probe_dashboard(args.dashboard),
        "nodes": [run_node_matrix(node, scenarios) for node in nodes],
    }
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "host-node-matrix-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (GENERATED / "host-node-matrix-report.md").write_text(render_markdown(report), encoding="utf-8")

    for node in report["nodes"]:
        if not node.get("ok"):
            print(f"FAIL {node.get('name')} unreachable: {node.get('error')}")
            continue
        print(f"{node.get('name')} @ {node.get('url')}: {node.get('routeCount')} routes")
        for scenario in node["scenarios"]:
            counts = scenario["counts"]
            print(
                f"  {scenario['id']}: pass={counts.get('pass', 0)} "
                f"degraded={counts.get('degraded', 0)} fail={counts.get('fail', 0)} skip={counts.get('skip', 0)}"
            )
            for step in scenario["steps"]:
                if step["status"] in {"fail", "degraded"}:
                    print(f"    {step['status']}: {step['id']} -> {step.get('reason')}")
    print(f"report: {GENERATED / 'host-node-matrix-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
