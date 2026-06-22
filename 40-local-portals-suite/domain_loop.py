#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Domain-first autonomous loop for local portals:
#
#   ./run_loop.sh 'support.local 3 razy zgłoszenie "Nie działa worker"'
#
# The prompt names the local domain and what should happen in a bounded autonomous
# loop. Execution uses urirun's agent action-space + run_plan policy gate.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))

from urirun.runtime import agent as urirun_agent  # noqa: E402
from urirun.runtime import v2  # noqa: E402

import portal_autonomy  # noqa: E402
import portal_server  # noqa: E402


DOMAIN_TO_PORTAL = {cfg["host"]: portal for portal, cfg in portal_server.PORTALS.items()}
PRIMARY_FIELD = {"crm": "customer", "support": "title", "shop": "product", "docs": "title"}
DETAIL_FIELD = {"crm": "note", "support": "message", "shop": "", "docs": "body"}


def extract_domain(prompt: str) -> str:
    match = re.search(r"\b([a-z0-9-]+\.local)\b", prompt, flags=re.I)
    if not match:
        raise ValueError("prompt must include a known local domain, e.g. crm.local or support.local")
    domain = match.group(1).lower()
    if domain not in DOMAIN_TO_PORTAL:
        known = ", ".join(sorted(DOMAIN_TO_PORTAL))
        raise ValueError(f"unknown local domain {domain!r}; known: {known}")
    return domain


def extract_iterations(prompt: str, default: int = 3, limit: int = 10) -> int:
    patterns = [
        r"\b(\d+)\s*(?:razy|x|iteracj[ei]|krok(?:i|ów|ow)?|loops?)\b",
        r"\b(?:razy|iteracj[ei]|loop|pętla|petla)\s*[:=]?\s*(\d+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.I)
        if match:
            return max(1, min(int(match.group(1)), limit))
    return default


def clean_action_prompt(prompt: str, domain: str) -> str:
    text = re.sub(rf"\b{re.escape(domain)}\b", " ", prompt, flags=re.I)
    text = re.sub(r"\b\d+\s*(?:razy|x|iteracj[ei]|krok(?:i|ów|ow)?|loops?)\b", " ", text, flags=re.I)
    text = re.sub(r"\b(?:razy|iteracj[ei]|loop|pętla|petla)\s*[:=]?\s*\d+\b", " ", text, flags=re.I)
    text = re.sub(r"\bw\s+(?:pętli|petli|loopie)\b", " ", text, flags=re.I)
    text = re.sub(r"\b(?:autonomicznie|autonomicznej)\b", " ", text, flags=re.I)
    return " ".join(text.split()).strip() or prompt


def parse_loop_prompt(prompt: str, *, default_iterations: int = 3, limit: int = 10) -> dict[str, Any]:
    domain = extract_domain(prompt)
    portal = DOMAIN_TO_PORTAL[domain]
    iterations = extract_iterations(prompt, default=default_iterations, limit=limit)
    action = clean_action_prompt(prompt, domain)
    return {"domain": domain, "portal": portal, "iterations": iterations, "action": action}


def iteration_payload(portal: str, action: str, iteration: int, total: int) -> dict[str, Any]:
    payload = dict(portal_autonomy.payload_for_goal(portal, action))
    primary = PRIMARY_FIELD[portal]
    base = str(payload.get(primary) or portal_autonomy.env_defaults(portal, {}).get(primary) or "Local loop item")
    payload[primary] = f"{base} #{iteration}"
    detail = DETAIL_FIELD[portal]
    if detail:
        existing = str(payload.get(detail) or "")
        payload[detail] = f"{existing}\nLoop iteration {iteration}/{total}: {action}".strip()
    return payload


def route_for_portal(portal: str, space: list[dict[str, Any]]) -> str:
    wanted = portal_autonomy.ROUTES[portal]
    return next((item["uri"] for item in space if item.get("uri") == wanted), wanted)


def run_domain_loop(prompt: str, registry: dict, *, default_iterations: int = 3, limit: int = 10) -> dict[str, Any]:
    parsed = parse_loop_prompt(prompt, default_iterations=default_iterations, limit=limit)
    space = urirun_agent.action_space(registry)
    uri = route_for_portal(parsed["portal"], space)
    steps = []
    for iteration in range(1, parsed["iterations"] + 1):
        payload = iteration_payload(parsed["portal"], parsed["action"], iteration, parsed["iterations"])
        trace = urirun_agent.run_plan(
            registry,
            [{"uri": uri, "payload": payload, "why": f"domain loop iteration {iteration}/{parsed['iterations']}"}],
            allow=["portal://**"],
            allow_commands=True,
        )
        step = trace[0] if trace else {"ok": False, "ran": False, "error": "empty trace"}
        steps.append({"iteration": iteration, **step})
        if not step.get("ok"):
            break
    return {
        "ok": len(steps) == parsed["iterations"] and all(step.get("ok") for step in steps),
        "prompt": prompt,
        **parsed,
        "uri": uri,
        "steps": steps,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a bounded autonomous loop from a local-domain prompt.")
    parser.add_argument("prompt", nargs="+")
    parser.add_argument("--registry", default=".state/local-portals.registry.json")
    parser.add_argument("--default-iterations", type=int, default=3)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    registry = v2.load_registry_arg(args.registry)
    try:
        report = run_domain_loop(" ".join(args.prompt), registry,
                                 default_iterations=args.default_iterations, limit=args.limit)
    except ValueError as exc:
        report = {"ok": False, "error": str(exc), "prompt": " ".join(args.prompt)}
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
