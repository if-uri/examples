# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Closed-loop task automation against a urirun node. Three loop patterns, all over
# the URI contract, all with a PLUGGABLE planner (real LLM / heuristic / a test
# stub) so the same loops run live or offline:
#
#   A. self-repair   — NL -> plan a YAML flow -> execute -> on failure feed the
#                      node's own error back to the planner -> corrected flow -> retry.
#   B. goal-verify   — plan -> execute -> probe the node to check the goal is met ->
#                      if not, re-plan WITH the observed state -> repeat.
#   C. agent         — observe -> planner picks ONE next action toward the goal ->
#                      act -> repeat until the planner says done (or a step budget).
#
# Cross-step data flow uses urirun's `<field>_from` convention (resolve_step_payload):
# `{text_from: "find_py.result.stdout"}` feeds an earlier step's output into a later
# step — no ${...} string templating.

from __future__ import annotations

import urirun
from urirun.node.client import NodeClient
from urirun.node.mesh import resolve_step_payload

# A planner is: (goal, routes, prev_error, observation) -> {"steps": [...]}
# A decider is: (goal, routes, transcript) -> {"uri", "payload"} | {"done": True}


def execute_flow(client: NodeClient, flow: dict) -> dict:
    """Run a flow's steps on the node, chaining `<field>_from` outputs. Stops at the
    first failed step and returns its node-reported error so a loop can react."""
    results: dict = {}
    trace = []
    for step in flow.get("steps", []):
        payload = resolve_step_payload(step.get("payload") or {}, results)
        env = client.run(step["uri"], payload)
        results[step["id"]] = env
        ok = bool(env.get("ok"))
        data = urirun.result_data(env)
        trace.append({"id": step["id"], "uri": step["uri"], "ok": ok,
                      "degraded": urirun.result_degraded(env), "data": data})
        if not ok:
            err = env.get("error") or {}
            return {"ok": False, "trace": trace,
                    "error": err.get("message") if isinstance(err, dict) else err, "failed_step": step}
    return {"ok": True, "trace": trace, "results": results}


def self_repair_loop(client: NodeClient, goal: str, planner, max_iter: int = 3) -> dict:
    """Pattern A. The planner builds a flow; on a node error the error is fed back and
    the planner corrects it — the loop closes through the node's own validation."""
    error = None
    history = []
    for iteration in range(1, max_iter + 1):
        flow = planner(goal, client.routes(), error, None)
        out = execute_flow(client, flow)
        history.append({"iteration": iteration, "flow": flow, "ok": out["ok"], "trace": out["trace"]})
        if out["ok"]:
            return {"ok": True, "iterations": iteration, "history": history, "trace": out["trace"]}
        error = {"failed_step": out["failed_step"], "error": out["error"]}
    return {"ok": False, "iterations": max_iter, "history": history, "error": error}


def goal_verify_loop(client: NodeClient, goal: str, planner, verify, max_iter: int = 4) -> dict:
    """Pattern B. After each execution a `verify(client) -> (met: bool, state)` probe
    checks the world; if the goal isn't met the observed state is fed back to re-plan."""
    observation = None
    history = []
    for iteration in range(1, max_iter + 1):
        flow = planner(goal, client.routes(), None, observation)
        out = execute_flow(client, flow)
        met, state = verify(client)
        history.append({"iteration": iteration, "ok": out["ok"], "met": met, "state": state})
        observation = {"goal_met": met, "observed": state, "last_flow_ok": out["ok"]}
        if met:
            return {"ok": True, "iterations": iteration, "history": history}
    return {"ok": False, "iterations": max_iter, "history": history}


def agent_loop(client: NodeClient, goal: str, decide, max_steps: int = 6) -> dict:
    """Pattern C. observe -> decide ONE action -> act -> repeat. `decide` sees the goal,
    the routes and the running transcript and returns a single step or {"done": true}."""
    transcript = []
    for step in range(1, max_steps + 1):
        action = decide(goal, client.routes(), transcript)
        if action.get("done"):
            return {"ok": True, "steps": step - 1, "transcript": transcript, "reason": action.get("reason")}
        env = client.run(action["uri"], action.get("payload"))
        transcript.append({"uri": action["uri"], "payload": action.get("payload") or {},
                           "ok": bool(env.get("ok")), "data": urirun.result_data(env)})
    return {"ok": False, "steps": max_steps, "transcript": transcript}
