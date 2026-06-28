# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Pluggable planners/deciders for the closed loops. All consume the node's LIVE
# routes (the action space) so plans are constrained to what the node can run.

from __future__ import annotations

import json
import re

from urirun.node import mesh


def _loads_llm_json(resp: dict) -> dict:
    """Parse the model's JSON reply ROBUSTLY — not every model/proxy honours
    ``response_format=json_object``. Tolerates ```json fences, leading prose, and
    trailing text by extracting the outermost balanced ``{...}`` object."""
    content = ((resp.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    content = content.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", content, re.DOTALL)
    if fence:
        content = fence.group(1).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        if start != -1:  # find the matching close brace
            depth = 0
            for i in range(start, len(content)):
                depth += {"{": 1, "}": -1}.get(content[i], 0)
                if depth == 0:
                    return json.loads(content[start:i + 1])
        raise ValueError(f"model did not return JSON: {content[:200]!r}")


# --- offline / no-LLM (keyword heuristic, deterministic) -------------------

def heuristic_planner(goal, routes, prev_error=None, observation=None):
    """No-LLM planner: urirun's keyword heuristic over the node's routes. Good enough
    for simple audit-style goals (date/uname/processes/health) and fully offline, so
    the loops run in CI without a model."""
    targets = sorted({r["uri"].split("://", 1)[1].split("/", 1)[0] for r in routes})
    nodes = [{"name": t} for t in targets] or [{"name": "local"}]
    flow = mesh.heuristic_flow(goal, routes, nodes)
    return {"steps": flow.get("steps", [])}


# --- live / LLM (litellm) --------------------------------------------------

_SYSTEM = (
    "Build a urirun flow as strict JSON {\"steps\":[{\"id\":str,\"uri\":str,\"payload\":obj}]}. "
    "Use ONLY the given routes and their EXACT input field names; never invent fields. "
    "To feed one step's output into a later step, add a payload key '<field>_from' with "
    "the dotted path '<earlier_step_id>.result.stdout' (do NOT use ${...} templates). "
    "Keep it minimal."
)


def make_llm_planner(model):
    """Live planner backed by litellm. Reads/repairs against the node's error and any
    verification observation fed back by the loop."""
    from urirun.host.task_planner import quiet_completion

    def planner(goal, routes, prev_error=None, observation=None):
        space = [{"uri": r["uri"],
                  "inputs": list((r.get("inputSchema", {}).get("properties") or {}).keys()),
                  "required": r.get("inputSchema", {}).get("required", [])} for r in routes]
        user = {"goal": goal, "routes": space}
        if prev_error:
            user["previous_attempt_failed"] = prev_error
            user["instruction"] = "Fix the failed step's payload to match the route's required fields."
        if observation:
            user["observation"] = observation
            user["instruction"] = "The goal is not yet met; adjust the flow given the observed state."
        resp = quiet_completion(model=model, temperature=0, response_format={"type": "json_object"},
                                messages=[{"role": "system", "content": _SYSTEM},
                                          {"role": "user", "content": json.dumps(user)}])
        return _loads_llm_json(resp)

    return planner


def make_llm_decider(model):
    """Live agent decider: given the goal + routes + transcript so far, return ONE next
    action {"uri","payload"} or {"done": true, "reason": ...}."""
    from urirun.host.task_planner import quiet_completion

    system = (
        "You drive a node one step at a time toward a goal. Given the goal, the available "
        "routes, and the transcript so far, return strict JSON: either {\"uri\":str,\"payload\":obj} "
        "for the single next action, or {\"done\":true,\"reason\":str} when the goal is achieved. "
        "Use only the given routes and their exact field names."
    )

    def decide(goal, routes, transcript):
        space = [{"uri": r["uri"], "inputs": list((r.get("inputSchema", {}).get("properties") or {}).keys())}
                 for r in routes]
        resp = quiet_completion(model=model, temperature=0, response_format={"type": "json_object"},
                                messages=[{"role": "system", "content": system},
                                          {"role": "user", "content": json.dumps(
                                              {"goal": goal, "routes": space, "transcript": transcript})}])
        return _loads_llm_json(resp)

    return decide
