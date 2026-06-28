#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
"""Run a corpus of natural-language prompts through dashboard chat.

The dashboard URL is UI state; the actual command is POST /api/chat/ask.
This runner uses the same endpoint and records one JSONL row per prompt.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_PROMPTS = HERE / "prompts.json"
DEFAULT_BASE = "http://127.0.0.1:8194"


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _bool_query(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def defaults_from_url(url: str | None) -> dict:
    if not url:
        return {"base": DEFAULT_BASE, "targets": ["host"], "nodes": [], "no_llm": False}
    parsed = urllib.parse.urlparse(url)
    base = f"{parsed.scheme or 'http'}://{parsed.netloc}" if parsed.netloc else DEFAULT_BASE
    query = urllib.parse.parse_qs(parsed.query)
    one = lambda key, fallback="": (query.get(key) or [fallback])[0]
    return {
        "base": base,
        "targets": _split_csv(one("targets", "host")) or ["host"],
        "nodes": _split_csv(one("nodes", "")),
        "no_llm": _bool_query(one("no_llm", one("noLlm", "")), False),
        "target_explicit": _bool_query(one("target_explicit", one("targetExplicit", "true")), True),
    }


def load_cases(path: Path) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("prompts") or raw.get("cases") or []
    cases: list[dict] = []
    for idx, item in enumerate(raw, 1):
        if isinstance(item, str):
            case = {"id": f"prompt-{idx:03d}", "category": "default", "prompt": item}
        elif isinstance(item, dict):
            case = dict(item)
            case.setdefault("id", f"prompt-{idx:03d}")
            case.setdefault("category", "default")
        else:
            raise TypeError(f"unsupported prompt case #{idx}: {type(item).__name__}")
        if not str(case.get("prompt") or "").strip():
            raise ValueError(f"empty prompt in case {case.get('id')}")
        cases.append(case)
    ids = [str(case["id"]) for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("prompt ids must be unique")
    return cases


def select_cases(cases: list[dict], categories: set[str], limit: int | None) -> list[dict]:
    selected = [
        case for case in cases
        if not categories or str(case.get("category") or "") in categories
    ]
    return selected[:limit] if limit else selected


def build_payload(case: dict, defaults: dict, *, execute: bool, no_llm: bool | None,
                  include_side_effects: bool, artifact_dir: str | None) -> tuple[dict, bool]:
    execute_allowed = bool(case.get("executeAllowed", True))
    skipped = bool(execute and not execute_allowed and not include_side_effects)
    payload = {
        "prompt": str(case["prompt"]),
        "nodes": case.get("nodes", defaults.get("nodes") or []),
        "targets": case.get("targets", defaults.get("targets") or ["host"]),
        "target_explicit": bool(case.get("target_explicit", defaults.get("target_explicit", True))),
        "execute": bool(execute and not skipped),
        "no_llm": bool(defaults.get("no_llm", False) if no_llm is None else no_llm),
        "inline_artifacts": False,
    }
    if artifact_dir:
        payload["artifact_dir"] = artifact_dir
    return payload, skipped


def post_chat(base: str, payload: dict, timeout: float) -> tuple[int, dict]:
    url = urllib.parse.urljoin(base.rstrip("/") + "/", "api/chat/ask")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        parsed = json.loads(data.decode("utf-8")) if data else {}
        return int(resp.status), parsed


def _dig(obj: Any, path: list[str]) -> Any:
    cur = obj
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _flow_steps(response: dict) -> list[dict]:
    steps = _dig(response, ["flow", "steps"])
    return steps if isinstance(steps, list) else []


def _routing(response: dict) -> dict:
    routing = response.get("routing")
    return routing if isinstance(routing, dict) else {}


def _has_human_signal(response: dict) -> bool:
    return bool(
        response.get("humanTask")
        or response.get("humanEscalation")
        or _dig(response, ["next", "kind"]) == "human-task"
        or _dig(response, ["notify", "sound"])
    )


def _has_block_signal(response: dict) -> bool:
    routing = _routing(response)
    return bool(
        response.get("error")
        or response.get("degraded")
        or _has_human_signal(response)
        or routing.get("accepted") is False
        or routing.get("violations")
        or response.get("needsSelection")
    )


def summarize(case: dict, payload: dict, status: int | None, response: dict | None,
              elapsed_ms: int, error: str = "", skipped: bool = False) -> dict:
    response = response or {}
    routing = _routing(response)
    flow_steps = _flow_steps(response)
    timeline = response.get("timeline") if isinstance(response.get("timeline"), list) else []
    expect = str(case.get("expect") or "")
    ok = bool(response.get("ok")) if response else False
    expected_block = expect.startswith("blocked") or expect.startswith("human")
    passed = False if error else (expected_block and _has_block_signal(response)) or (ok and not skipped)
    return {
        "id": case.get("id"),
        "category": case.get("category"),
        "prompt": case.get("prompt"),
        "expect": expect,
        "skipped": skipped,
        "passed": bool(passed),
        "httpStatus": status,
        "elapsedMs": elapsed_ms,
        "ok": ok,
        "error": error or response.get("error"),
        "degraded": bool(response.get("degraded")),
        "degradedReason": response.get("degradedReason"),
        "execute": payload.get("execute"),
        "no_llm": payload.get("no_llm"),
        "selectedTargets": response.get("selectedTargets"),
        "selectedNodes": response.get("selectedNodes"),
        "generator": response.get("generator"),
        "routingAccepted": routing.get("accepted", routing.get("ok")),
        "routingViolations": routing.get("violations") or [],
        "runsOnByStep": routing.get("runsOnByStep") or {},
        "flowStepCount": len(flow_steps),
        "flowUris": [step.get("uri") for step in flow_steps if isinstance(step, dict)],
        "timeline": [
            {"id": step.get("id"), "ok": step.get("ok"), "target": step.get("target"), "uri": step.get("uri")}
            for step in timeline if isinstance(step, dict)
        ],
        "attachmentCount": len(response.get("attachments") or []),
        "artifactCount": len(response.get("artifacts") or []),
        "humanSignal": _has_human_signal(response),
        "raw": response,
    }


def write_reports(rows: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "chat-prompt-results.jsonl"
    with jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    summary = {
        "total": len(rows),
        "passed": sum(1 for row in rows if row.get("passed")),
        "ok": sum(1 for row in rows if row.get("ok")),
        "skipped": sum(1 for row in rows if row.get("skipped")),
        "failed": [row["id"] for row in rows if not row.get("passed") and not row.get("skipped")],
        "categories": {},
    }
    for row in rows:
        cat = str(row.get("category") or "default")
        bucket = summary["categories"].setdefault(cat, {"total": 0, "passed": 0, "ok": 0})
        bucket["total"] += 1
        bucket["passed"] += int(bool(row.get("passed")))
        bucket["ok"] += int(bool(row.get("ok")))
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Chat Prompt Sweep",
        "",
        f"- total: {summary['total']}",
        f"- passed: {summary['passed']}",
        f"- ok: {summary['ok']}",
        f"- skipped: {summary['skipped']}",
        "",
        "| id | category | pass | ok | target | steps | ms | error |",
        "|---|---|---:|---:|---|---:|---:|---|",
    ]
    for row in rows:
        target = ",".join(row.get("selectedTargets") or [])
        err = str(row.get("error") or row.get("degradedReason") or "")[:80].replace("|", "\\|")
        lines.append(
            f"| {row['id']} | {row.get('category')} | {int(bool(row.get('passed')))} | "
            f"{int(bool(row.get('ok')))} | {target} | {row.get('flowStepCount')} | "
            f"{row.get('elapsedMs')} | {err} |"
        )
    (out_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    defaults = defaults_from_url(args.from_url)
    if args.base_url:
        defaults["base"] = args.base_url
    if args.targets is not None:
        defaults["targets"] = _split_csv(args.targets) or []
    if args.nodes is not None:
        defaults["nodes"] = _split_csv(args.nodes)
    categories = set(_split_csv(args.category))
    cases = select_cases(load_cases(Path(args.prompts)), categories, args.limit)
    out_dir = Path(args.out or (HERE / "generated" / _dt.datetime.now().strftime("%Y%m%dT%H%M%S")))
    artifact_dir = str(out_dir / "artifacts")
    rows: list[dict] = []
    print(f"chat: {defaults['base'].rstrip('/')}/api/chat/ask")
    print(f"cases: {len(cases)}  execute={args.execute}  no_llm={args.no_llm}")
    for idx, case in enumerate(cases, 1):
        payload, skipped = build_payload(
            case, defaults,
            execute=args.execute,
            no_llm=args.no_llm,
            include_side_effects=args.include_side_effects,
            artifact_dir=artifact_dir,
        )
        started = time.time()
        status: int | None = None
        response: dict | None = None
        error = ""
        if skipped:
            error = "skipped: executeAllowed=false"
        else:
            try:
                status, response = post_chat(defaults["base"], payload, args.timeout)
            except urllib.error.HTTPError as exc:
                status = exc.code
                error = f"HTTP {exc.code}: {exc.reason}"
                try:
                    response = json.loads(exc.read().decode("utf-8"))
                except Exception:  # noqa: BLE001
                    response = {}
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
        elapsed_ms = int((time.time() - started) * 1000)
        row = summarize(case, payload, status, response, elapsed_ms, error=error, skipped=skipped)
        rows.append(row)
        marker = "SKIP" if skipped else ("ok" if row["passed"] else "FAIL")
        print(
            f"[{idx:03d}/{len(cases):03d}] {marker:4} {row['id']} "
            f"ok={int(row['ok'])} steps={row['flowStepCount']} "
            f"target={','.join(row.get('selectedTargets') or []) or '-'} "
            f"{row['elapsedMs']}ms"
        )
        if args.stop_on_fail and not row["passed"] and not skipped:
            break
        if args.delay > 0 and idx < len(cases):
            time.sleep(args.delay)
    write_reports(rows, out_dir)
    passed = sum(1 for row in rows if row.get("passed"))
    rate = (passed / len(rows)) if rows else 0.0
    print(f"\nreport: {out_dir / 'REPORT.md'}")
    print(f"jsonl:  {out_dir / 'chat-prompt-results.jsonl'}")
    print(f"summary: {passed}/{len(rows)} passed ({rate:.1%})")
    return 0 if rate >= args.min_ok_rate else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-url", help="Dashboard chat URL to read base URL/targets/no_llm from.")
    parser.add_argument("--base-url", help=f"Dashboard base URL. Default: {DEFAULT_BASE}")
    parser.add_argument("--prompts", default=str(DEFAULT_PROMPTS), help="JSON prompt corpus.")
    parser.add_argument("--targets", help="Comma-separated default targets, e.g. host,node:lenovo.")
    parser.add_argument("--nodes", help="Comma-separated default nodes.")
    parser.add_argument("--category", help="Comma-separated categories to run.")
    parser.add_argument("--limit", type=int, help="Run only first N selected cases.")
    parser.add_argument("--execute", action="store_true", help="Execute accepted flows. Omitted means dry-run.")
    parser.add_argument("--include-side-effects", action="store_true",
                        help="When --execute is set, also run cases with executeAllowed=false.")
    parser.add_argument("--no-llm", action="store_true", default=None, help="Send no_llm=true.")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--out", help="Output directory.")
    parser.add_argument("--stop-on-fail", action="store_true")
    parser.add_argument("--min-ok-rate", type=float, default=0.0,
                        help="Exit 2 when passed/total is below this fraction.")
    return run(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
