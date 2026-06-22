#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A SCHEMA-AWARE planner: it hands the LLM each route's full input JSON Schema (the
# same schema MCP tools expose) so the model picks a command AND fills its typed
# parameters straight from the user's natural-language intent. Generic — it knows
# nothing about desktops; it just reads the action space. Offline heuristic fallback
# keeps the example runnable without an API key.

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_ENV = "/home/tom/github/if-uri/urirun/.env"


def _load_env() -> None:
    p = Path(os.environ.get("URIRUN_ENV", DEFAULT_ENV))
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.split(" #", 1)[0].strip().strip('"').strip("'"))


def _extract_json(text: str) -> list[dict]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("["), text.rfind("]")
    return json.loads(text[start:end + 1]) if start != -1 and end != -1 else []


def _by_op(space: list[dict], suffix: str) -> dict | None:
    for r in space:
        if r["uri"].endswith(suffix):
            return r
    return None


def heuristic_plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    """Offline fallback for the desktop task: start -> terminal -> type -> shot -> stop.
    Fills each step's parameters per its schema (text from quotes in the goal)."""
    quoted = re.search(r"['\"]([^'\"]+)['\"]", goal)
    text = quoted.group(1) if quoted else "hello from the urirun LLM agent"
    steps: list[dict[str, Any]] = []

    def add(route, payload, why):
        if route:
            steps.append({"uri": route["uri"], "payload": payload, "why": why})

    add(_by_op(space, "/session/command/start"), {}, "start the noVNC desktop")
    add(_by_op(space, "/app/command/launch"), {"command": "lxterminal"}, "open a terminal")
    add(_by_op(space, "/input/command/type"), {"text": f"echo {text}", "enter": True},
        "type the requested text and run it")
    add(_by_op(space, "/screen/query/screenshot"), {"name": "result"}, "capture the screen")
    add(_by_op(space, "/session/command/stop"), {}, "stop the desktop")
    return steps


def plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    _load_env()
    key, model = os.environ.get("OPENROUTER_API_KEY"), os.environ.get("URIRUN_LLM_MODEL") or os.environ.get("LLM_MODEL")
    if not key or not model:
        return heuristic_plan(goal, space)
    try:
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        import litellm

        litellm.suppress_debug_info = True
        # hand the LLM the full schema per route — that is what lets it fill params
        catalog = [{"uri": r["uri"], "kind": r["kind"], "label": r.get("label", ""), "schema": r["schema"]}
                   for r in space]
        system = (
            "You drive the urirun runtime. Achieve the goal using ONLY uris from the "
            "catalog. For each step return {\"uri\":..., \"payload\":{...}, \"why\":...} where "
            "payload satisfies that uri's JSON Schema (respect types, required, defaults, "
            "enums). Pass an earlier step's output with the string \"$ref:<stepIndex>.<field>\". "
            "Order matters (start a session before using it; stop it last). Output ONLY a JSON array."
        )
        user = f"GOAL: {goal}\n\nCATALOG (uri + JSON Schema):\n{json.dumps(catalog, indent=2)}"
        resp = litellm.completion(
            model=model, temperature=0, timeout=90, max_tokens=2000,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        steps = _extract_json(resp.choices[0].message.content or "")
        uris = {r["uri"] for r in space}
        steps = [s for s in steps if isinstance(s, dict) and s.get("uri") in uris]
        return steps or heuristic_plan(goal, space)
    except Exception:
        return heuristic_plan(goal, space)
