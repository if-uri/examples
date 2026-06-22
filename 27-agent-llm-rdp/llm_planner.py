#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A REAL LLM planner for `urirun agent`: (goal, action_space) -> [{uri, payload, why}].
# It calls an OpenRouter model via liteLLM (config from urirun/.env), constrained to
# choose only URIs that exist in the action space, and to thread step outputs with
# `$ref:<step>.<field>`. If no API key / liteLLM / a bad response, it falls back to a
# deterministic heuristic so the example still runs offline.

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

DEFAULT_ENV = "/home/tom/github/if-uri/urirun/.env"


def _load_env(path: str | None = None) -> None:
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


def _concrete(uri: str) -> str:
    return (uri.replace("{host}", "host1").replace("{target}", "desktop")
               .replace("{monitor}", "0").replace("{image_id}", "latest"))


def _find(space: list[dict], *needles: str) -> dict | None:
    for route in space:
        hay = (route.get("uri", "") + " " + route.get("label", "")).lower()
        if any(n in hay for n in needles):
            return route
    return None


def heuristic_plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    """Deterministic computer-control plan: prepare RDP -> kvm screenshot -> OCR -> decide."""
    rdp = _find(space, "prepare-target", "rdp://")
    shot = _find(space, "screenshot", "/capture")
    ocr = _find(space, "ocr://", "/image/")
    decide = _find(space, "decide", "analyze", "/text/plan")
    steps: list[dict[str, Any]] = []
    idx: dict[str, int] = {}
    if rdp:
        idx["rdp"] = len(steps)
        steps.append({"uri": _concrete(rdp["uri"]), "payload": {"target": "desktop"},
                      "why": "open/prepare the RDP target before driving it"})
    if shot:
        idx["shot"] = len(steps)
        steps.append({"uri": _concrete(shot["uri"]), "payload": {"monitor": 0},
                      "why": "capture the remote screen with the kvm screenshot connector"})
    if ocr and "shot" in idx:
        idx["ocr"] = len(steps)
        steps.append({"uri": _concrete(ocr["uri"]), "payload": {},
                      "why": "read the captured screen's text"})
    if decide:
        steps.append({"uri": _concrete(decide["uri"]),
                      "payload": {"prompt": f"$ref:{idx.get('ocr', 0)}.text"},
                      "why": "decide the next computer-control action from what's on screen"})
    return steps


def _extract_json(text: str) -> list[dict]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1:
        return json.loads(text[start:end + 1])
    return []


def plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    _load_env()
    key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("URIRUN_LLM_MODEL") or os.environ.get("LLM_MODEL")
    if not key or not model:
        return heuristic_plan(goal, space)
    try:
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        import litellm

        litellm.suppress_debug_info = True
        routes = [{"uri": r["uri"], "kind": r.get("kind"), "inputs": r.get("inputs", [])} for r in space]
        system = (
            "You are a planning agent for the urirun URI runtime. Compose a plan that "
            "achieves the goal using ONLY uris from the provided action space. Return a "
            "JSON array of steps; each step is {\"uri\":..., \"payload\":{...}, \"why\":...}. "
            "Replace {host}->host1, {target}->desktop, {monitor}->0, {image_id}->latest in "
            "uris. To pass an earlier step's output into a later step, use the string "
            "\"$ref:<stepIndex>.<field>\" as a payload value. Output ONLY the JSON array."
        )
        user = f"GOAL: {goal}\n\nACTION SPACE:\n{json.dumps(routes, indent=2)}"
        resp = litellm.completion(
            model=model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            timeout=60, max_tokens=1500, temperature=0,
        )
        steps = _extract_json(resp.choices[0].message.content or "")
        schemes = {r["uri"].split("://", 1)[0] for r in space}
        steps = [s for s in steps if isinstance(s, dict)
                 and isinstance(s.get("uri"), str)
                 and s["uri"].split("://", 1)[0] in schemes]
        return steps or heuristic_plan(goal, space)
    except Exception:
        return heuristic_plan(goal, space)
