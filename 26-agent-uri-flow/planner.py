#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A pluggable agent PLANNER: (goal, action_space) -> [steps]. It does not know the
# URIs ahead of time — it discovers them from the action space (the registry's routes)
# and composes a capture -> OCR -> summarize chain, threading each step's output into
# the next with `$ref:<step>.<field>` placeholders that `urirun agent run` resolves at
# execution time. Swap this for an LLM planner with the same signature; the runtime,
# policy gate and data threading are unchanged.

from __future__ import annotations

from typing import Any


def _find(space: list[dict], *keywords: str) -> dict | None:
    """First route whose URI or label mentions any keyword (capability match)."""
    for route in space:
        hay = (route.get("uri", "") + " " + route.get("label", "")).lower()
        if any(k in hay for k in keywords):
            return route
    return None


def _concrete(uri: str, host: str = "host1") -> str:
    return uri.replace("{host}", host)


def plan(goal: str, space: list[dict]) -> list[dict[str, Any]]:
    """Compose the flow from whatever capture/ocr/llm routes the registry exposes."""
    capture = _find(space, "capture", "screenshot")
    ocr = _find(space, "ocr", "/image/")
    summarize = _find(space, "llm", "complete", "/chat/")

    steps: list[dict[str, Any]] = []
    index: dict[str, int] = {}

    if capture is not None:
        index["capture"] = len(steps)
        steps.append({
            "uri": _concrete(capture["uri"]),
            "payload": {"monitor": 0},
            "why": "goal needs an image: capture a monitor",
        })
    if ocr is not None and "capture" in index:
        index["ocr"] = len(steps)
        steps.append({
            "uri": _concrete(ocr["uri"]),
            "payload": {"image_id": f"$ref:{index['capture']}.image_id"},
            "why": "read the captured image's text (uses the capture's image_id)",
        })
    if summarize is not None and "ocr" in index:
        steps.append({
            "uri": _concrete(summarize["uri"]),
            "payload": {"prompt": f"$ref:{index['ocr']}.text"},
            "why": "summarize the OCR text (uses the OCR step's text)",
        })
    return steps
