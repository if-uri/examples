#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# RUN THIS ON THE HOST (your controlling machine). Turn a natural-language office task
# into a URI plan and delegate it to a remote urirun node over the mesh — with logging
# on BOTH sides so you can see what happened on the host and on the node.
#
#   ./office_cli.sh "open https://example.com in the browser and screenshot it"
#   python3 office_agent.py "type 'Faktura 07/2026' then take a screenshot" --yes
#
# Pipeline:  /health + /routes (the node's live action space)
#         -> LLM plans [{uri, payload, why}] constrained to that action space
#         -> POST /run each step to the node, logging each on the host AND the node
#         -> read the node's own log back -> write generated/run-log.{md,json}
#
# Config (model + key) comes from examples/.env (OPENROUTER_API_KEY, LLM_MODEL), the
# same liteLLM setup as examples 27/28. No key -> a deterministic heuristic planner so
# the loop still runs offline.

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
DEFAULT_ENV = HERE.parent / ".env"  # examples/.env
DEFAULT_NODE = "http://192.168.188.201:8765"

PLACEHOLDERS = {"{target}": None, "{session}": None, "{host}": None,
                "{monitor}": "0", "{image_id}": "latest"}

# The schemes that make "office work" (browse/type/click/screenshot/document) possible.
# A node serving only base routes (env/log/proc/shell) can't do any of it.
OFFICE_SCHEMES = {"browser", "him", "kvm", "urioffice", "screen"}


# --------------------------------------------------------------------------- env
def load_env(path: str | None = None) -> None:
    p = Path(path or os.environ.get("URIRUN_ENV", DEFAULT_ENV))
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        val = val.split(" #", 1)[0].strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), val)


# ------------------------------------------------------------------- node client
def _get(url: str, timeout: float = 6.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _post(url: str, body: dict, timeout: float = 120.0) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class Node:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        health = _get(self.base + "/health")
        self.name = health.get("name", "node")
        self.routes = _get(self.base + "/routes").get("routes", [])

    def concretize(self, uri: str) -> str:
        uri = urllib.parse.unquote(uri)  # /routes percent-encodes braces: %7Bmonitor%7D
        for ph, default in PLACEHOLDERS.items():
            uri = uri.replace(ph, default if default is not None else self.name)
        return uri

    def action_space(self) -> list[dict]:
        space = []
        for r in self.routes:
            space.append({
                "uri": self.concretize(r["uri"]),
                "kind": r.get("kind"),
                "title": r.get("title", ""),
                "inputSchema": r.get("inputSchema", {}),
            })
        return space

    def run(self, uri: str, payload: dict) -> dict:
        return _post(self.base + "/run", {"uri": uri, "payload": payload})

    def log(self, text: str) -> None:
        """Best-effort: record a line in the node's OWN log (visible on the node side)."""
        uri = f"log://{self.name}/session/command/write"
        if any(r["uri"] == uri for r in self.routes):
            try:
                self.run(uri, {"text": text})
            except Exception:
                pass

    def recent_log(self, limit: int = 20) -> list[str]:
        uri = f"log://{self.name}/session/query/recent"
        if not any(r["uri"] == uri for r in self.routes):
            return []
        try:
            env = self.run(uri, {"limit": limit})
            out = (env.get("result") or {}).get("stdout") or "{}"
            data = json.loads(out)
            # the default node uses "logs"; this example's base route uses "lines"
            return data.get("logs") or data.get("lines") or []
        except Exception:
            return []


# ------------------------------------------------------------------- planning
def _schemes(space: list[dict]) -> set[str]:
    return {s["uri"].split("://", 1)[0] for s in space}


def _find(space: list[dict], *needles: str) -> dict | None:
    for r in space:
        hay = (r["uri"] + " " + r.get("title", "")).lower()
        if any(n in hay for n in needles):
            return r
    return None


def heuristic_plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    """Cover the common office verbs without a model so the loop always runs."""
    g = goal.lower()
    steps: list[dict[str, Any]] = []
    url = (re.search(r"https?://\S+", goal) or [None])
    url = url.group(0) if hasattr(url, "group") else None
    if url and (r := _find(space, "browser") and _find(space, "page/command/open", "page/open")):
        steps.append({"uri": r["uri"], "payload": {"url": url}, "why": f"open {url} in the browser"})
    if ("type" in g or "wpisz" in g or "login" in g or "zaloguj" in g) and (r := _find(space, "keyboard/command/type")):
        m = re.search(r"['\"]([^'\"]+)['\"]", goal)
        steps.append({"uri": r["uri"], "payload": {"text": m.group(1) if m else goal},
                      "why": "type the requested text on the remote machine"})
    if ("screenshot" in g or "zrzut" in g or "screen" in g) and (r := _find(space, "screenshot")):
        steps.append({"uri": r["uri"], "payload": {}, "why": "capture the screen"})
    if not steps and (r := _find(space, "runtime/query/health", "env://")):
        steps.append({"uri": r["uri"], "payload": {}, "why": "no office verb matched; probe node health"})
    return steps


def _extract_json(text: str) -> list[dict]:
    text = re.sub(r"```(?:json)?|```", "", text or "").strip()
    a, b = text.find("["), text.rfind("]")
    return json.loads(text[a:b + 1]) if a != -1 and b != -1 else []


def llm_plan(goal: str, space: list[dict]) -> tuple[list[dict], str]:
    key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("URIRUN_OFFICE_MODEL") or os.environ.get("LLM_MODEL")
    if not key or not model:
        return heuristic_plan(goal, space), "heuristic"
    try:
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        import litellm

        litellm.suppress_debug_info = True
        routes = [{"uri": r["uri"], "kind": r["kind"], "title": r["title"],
                   "inputSchema": r["inputSchema"]} for r in space]
        system = (
            "You are an office-automation planner for the urirun URI runtime. Compose a "
            "plan that achieves the user's goal using ONLY uris from the action space. "
            "Return a JSON array; each step is {\"uri\":..., \"payload\":{...}, \"why\":...}. "
            "Fill payload strictly from each route's inputSchema.properties. Use the uris "
            "verbatim (they are already concrete). To pass an earlier step's output into a "
            "later step, use the string \"$ref:<stepIndex>.<field>\" as a payload value. "
            "Output ONLY the JSON array, no prose."
        )
        user = f"GOAL: {goal}\n\nACTION SPACE:\n{json.dumps(routes, indent=2)}"
        resp = litellm.completion(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            timeout=60, max_tokens=1500, temperature=0,
        )
        steps = _extract_json(resp.choices[0].message.content or "")
        valid_uris = {r["uri"] for r in space}
        steps = [s for s in steps if isinstance(s, dict) and s.get("uri") in valid_uris]
        return (steps or heuristic_plan(goal, space)), ("llm" if steps else "heuristic")
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"[plan] llm failed ({e}); using heuristic\n")
        return heuristic_plan(goal, space), "heuristic"


# ------------------------------------------------------------------- $ref threading
def resolve_refs(payload: Any, results: list[dict]) -> Any:
    if isinstance(payload, dict):
        return {k: resolve_refs(v, results) for k, v in payload.items()}
    if isinstance(payload, list):
        return [resolve_refs(v, results) for v in payload]
    if isinstance(payload, str) and payload.startswith("$ref:"):
        m = re.match(r"\$ref:(\d+)\.([\w.]+)", payload)
        if m:
            idx, field = int(m.group(1)), m.group(2)
            cur: Any = results[idx] if idx < len(results) else {}
            for part in field.split("."):
                cur = (cur or {}).get(part) if isinstance(cur, dict) else None
            return cur if cur is not None else payload
    return payload


def _value(env: dict) -> Any:
    """Unwrap a node /run envelope: local-function -> result.value; argv -> result.stdout(json)."""
    res = env.get("result") or {}
    if "value" in res:
        return res["value"]
    out = res.get("stdout")
    if isinstance(out, str):
        try:
            return json.loads(out)
        except Exception:
            return out
    return res


# ------------------------------------------------------------------- run
def main() -> int:
    ap = argparse.ArgumentParser(description="LLM -> URI office automation over the urirun mesh")
    ap.add_argument("goal", help="natural-language office task")
    ap.add_argument("--node", default=os.environ.get("NODE_URL", DEFAULT_NODE))
    ap.add_argument("--yes", action="store_true", help="execute commands (no per-step prompt)")
    ap.add_argument("--dry-run", action="store_true", help="plan + show, do not dispatch")
    ap.add_argument("--json", action="store_true", help="machine-readable trace to stdout")
    args = ap.parse_args()

    load_env()
    node = Node(args.node)
    space = node.action_space()
    plan, planner = llm_plan(args.goal, space)

    ts = time.strftime("%Y%m%d-%H%M%S")
    hostlog = HERE / "generated" / f"host-run-{ts}.log"
    hostlog.parent.mkdir(parents=True, exist_ok=True)

    def hlog(msg: str) -> None:
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        if not args.json:
            print(line)
        hostlog.open("a", encoding="utf-8").write(line + "\n")

    hlog(f"node      : {node.name} @ {args.node}  ({len(space)} routes)")
    hlog(f"goal      : {args.goal}")
    hlog(f"planner   : {planner}  (model={os.environ.get('URIRUN_OFFICE_MODEL') or os.environ.get('LLM_MODEL') or 'n/a'})")
    hlog(f"plan      : {len(plan)} step(s)")

    # If the node exposes no office capabilities, the model can only fall back to base
    # routes — say so loudly rather than letting it look like a planning failure.
    present = {s["uri"].split("://", 1)[0] for s in space}
    missing = OFFICE_SCHEMES - present
    if missing == OFFICE_SCHEMES:
        hlog(f"\n  ⚠ node '{node.name}' exposes only {len(space)} base routes "
             f"({', '.join(sorted(present))}) — no office actions "
             f"({', '.join(sorted(OFFICE_SCHEMES))}).")
        hlog(f"  ⚠ run  ./node_serve.sh  on the node ({args.node}) to enable them, "
             f"then re-run this command.")
    node.log(f"[host] new task: {args.goal!r} ({len(plan)} steps, planner={planner})")

    results: list[dict] = []
    trace: list[dict] = []
    for i, step in enumerate(plan):
        uri = node.concretize(step.get("uri", ""))
        payload = resolve_refs(step.get("payload", {}), [r.get("_value") for r in results])
        why = step.get("why", "")
        kind = next((s["kind"] for s in space if s["uri"] == uri), "?")

        hlog(f"\n  [{i}] {uri}")
        hlog(f"      why    : {why}")
        hlog(f"      payload: {json.dumps(payload, ensure_ascii=False)}")

        if args.dry_run or (kind == "command" and not args.yes):
            note = "dry-run" if args.dry_run else "skipped (command; pass --yes to execute)"
            hlog(f"      -> {note}")
            trace.append({"i": i, "uri": uri, "why": why, "payload": payload, "status": note})
            continue

        node.log(f"[host->node] step {i}: {uri} payload={json.dumps(payload, ensure_ascii=False)}")
        try:
            env = node.run(uri, payload)
        except urllib.error.HTTPError as e:
            env = {"ok": False, "error": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"}
        except Exception as e:  # noqa: BLE001
            env = {"ok": False, "error": str(e)}

        ok = bool(env.get("ok"))
        val = _value(env) if ok else env.get("error")
        results.append({"_value": val})
        node.log(f"[node] step {i} {'ok' if ok else 'FAIL'}: {json.dumps(val, ensure_ascii=False)[:300]}")
        hlog(f"      -> {'ok' if ok else 'FAIL'}: {json.dumps(val, ensure_ascii=False)[:300]}")
        trace.append({"i": i, "uri": uri, "why": why, "payload": payload,
                      "ok": ok, "value": val,
                      "decision": (env.get("decision") or {}).get("allowed")})

    # both-sides proof: read the node's own log back
    node_log = node.recent_log(limit=max(6, len(plan) * 3))
    hlog("\n== node-side log (read back from the node) ==")
    for line in node_log[-(len(plan) * 3 + 1):]:
        try:
            entry = json.loads(line)
            hlog(f"  node: {entry.get('text', line)}")
        except Exception:
            hlog(f"  node: {line}")

    report = {
        "goal": args.goal, "node": {"name": node.name, "url": args.node},
        "planner": planner, "plan": plan, "trace": trace,
        "node_log_tail": node_log, "host_log": str(hostlog), "at": ts,
    }
    (HERE / "generated" / "run-log.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_md(report)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        ok_n = sum(1 for t in trace if t.get("ok"))
        hlog(f"\nrecord: generated/run-log.md  (host log: {hostlog.name})")
        hlog(f"done: {ok_n}/{len([t for t in trace if 'ok' in t])} dispatched step(s) ok")
    return 0


def _write_md(report: dict) -> None:
    lines = [f"# office run — {report['at']}", "",
             f"- **goal**: {report['goal']}",
             f"- **node**: `{report['node']['name']}` @ {report['node']['url']}",
             f"- **planner**: {report['planner']}", "",
             "| # | URI | status | why |", "|---|-----|--------|-----|"]
    for t in report["trace"]:
        status = "ok" if t.get("ok") else (t.get("status") or "FAIL")
        lines.append(f"| {t['i']} | `{t['uri']}` | {status} | {t['why']} |")
    lines += ["", "## node-side log (both sides see the run)", "```"]
    lines += [json.loads(l).get("text", l) if l.strip().startswith("{") else l
              for l in report["node_log_tail"]]
    lines.append("```")
    (HERE / "generated" / "run-log.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
