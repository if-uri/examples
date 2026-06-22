#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Self-repairing LLM-over-URI flow:
#
#   action space (URIs+schemas) ─▶ llm://host/chat/command/complete ─▶ YAML flow
#       ─▶ urirun runs each step under policy ─▶ ok? done
#                                            └▶ failed? feed the step+error back
#                                               to the LLM ─▶ corrected YAML ─▶ retry
#
# The model and provider are chosen on the `llm://` payload: `model` picks the
# model, `base_url` picks the provider endpoint (a local Ollama by default, or a
# litellm/OpenAI-compatible proxy URL for hosted models like Claude/GPT).

from __future__ import annotations

import argparse
import json
import re
import sys

import yaml

import urirun

LLM_ROUTE = "llm://host/chat/command/complete"


# --- talk to the model over llm:// (model + provider chosen here) ----------

def ask_llm(llm_registry: dict, prompt: str, *, model: str, base_url: str) -> str:
    """One completion through the llm:// connector; returns the raw text."""
    env = urirun.run(
        LLM_ROUTE, llm_registry, {"prompt": prompt, "model": model, "base_url": base_url},
        mode="execute", policy=urirun.policy(allow=["llm://*"]),
    )
    data = urirun.result_data(env)
    if not isinstance(data, dict) or not data.get("ok"):
        raise RuntimeError(f"llm:// call failed: {data}")
    return data.get("response", "")


def _extract_yaml(text: str) -> str:
    """Pull the YAML body out of a model reply (strip ``` fences / prose)."""
    fence = re.search(r"```(?:ya?ml)?\s*(.*?)```", text, re.S)
    return (fence.group(1) if fence else text).strip()


# --- prompt: goal + the typed action space (+ the failure on a retry) ------

def build_prompt(goal: str, space: list[dict], *, prior_yaml: str | None = None,
                 failure: dict | None = None) -> str:
    routes = "\n".join(
        f"  - {r['uri']}  (kind={r['kind']}, inputs={r['inputs']}, required={r['required']})"
        for r in space
    )
    prompt = (
        "You translate a goal into a urirun flow. Output ONLY YAML, no prose, no code fences.\n"
        "Schema:\n"
        "  steps:\n"
        "    - id: <unique>\n"
        "      uri: <one of the available routes>\n"
        "      payload: { <fields from that route's inputs> }\n"
        "      depends_on: [ <ids> ]   # optional\n\n"
        f"Available routes:\n{routes}\n\n"
        f"Goal: {goal}\n"
    )
    if failure:
        prompt += (
            "\nYour previous flow FAILED — fix it and return a corrected YAML flow.\n"
            f"Failing step id: {failure['id']}\n"
            f"Failing uri: {failure['uri']}\n"
            f"Error: {failure['detail']}\n\n"
            f"Previous flow:\n{prior_yaml}\n"
        )
    return prompt


# --- execute the flow under policy, stop + report on the first failure ------

def _local_runner(uri: str, registry: dict, payload: dict, allow: list[str]) -> dict:
    """Run a step in-process under an allow policy (single-registry case)."""
    return urirun.run(uri, registry, payload, mode="execute", policy=urirun.policy(allow=allow))


def run_flow(flow: dict, registry: dict, *, allow: list[str], runner=None) -> tuple[bool, dict | None, dict]:
    """Execute each step via ``runner`` (default: in-process). A mesh driver passes
    a runner that forwards each step to the remote node over HTTP."""
    runner = runner or _local_runner
    results: dict = {}
    for step in flow.get("steps") or []:
        env = runner(step["uri"], registry, step.get("payload") or {}, allow)
        data = urirun.result_data(env)
        ok = bool(env.get("ok")) and (data.get("ok", True) if isinstance(data, dict) else True)
        results[step.get("id", step["uri"])] = data
        mark = "✓" if ok else "✗"
        print(f"    {mark} {step.get('id','?'):<14} {step['uri']}")
        if not ok:
            reason = (env.get("decision") or {}).get("reason") or env.get("error") or data
            return False, {"id": step.get("id", "?"), "uri": step["uri"],
                           "detail": json.dumps(reason)[:400]}, results
    return True, None, results


# --- the generate → run → repair loop --------------------------------------

def generate_run_repair(goal: str, registry: dict, llm_registry: dict, *, model: str,
                        base_url: str, allow: list[str], max_attempts: int = 3, ask=ask_llm,
                        runner=None) -> dict:
    space = urirun.action_space(registry)
    prior_yaml: str | None = None
    failure: dict | None = None
    for attempt in range(1, max_attempts + 1):
        prompt = build_prompt(goal, space, prior_yaml=prior_yaml, failure=failure)
        raw = ask(llm_registry, prompt, model=model, base_url=base_url)
        yaml_text = _extract_yaml(raw)
        try:
            flow = yaml.safe_load(yaml_text) or {}
        except yaml.YAMLError as exc:
            print(f"  attempt {attempt}: invalid YAML ({exc}); asking for a fix")
            prior_yaml = yaml_text
            failure = {"id": "(parse)", "uri": "-", "detail": f"invalid YAML: {exc}"}
            continue
        print(f"  attempt {attempt}: running {len(flow.get('steps') or [])} step(s)")
        ok, failure, results = run_flow(flow, registry, allow=allow, runner=runner)
        if ok:
            return {"ok": True, "attempts": attempt, "flow": flow, "results": results}
        print(f"    -> failed at '{failure['id']}'; feeding the error back to the model")
        prior_yaml = yaml_text
    return {"ok": False, "attempts": max_attempts, "lastError": failure}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LLM-generated, self-repairing urirun flow")
    ap.add_argument("goal", nargs="?", default="get the current UTC time")
    ap.add_argument("--model", default="llama3", help="model name (e.g. llama3, claude-3.5-sonnet)")
    ap.add_argument("--base-url", default="http://localhost:11434",
                    help="provider endpoint: local Ollama, or a litellm/OpenAI-compatible proxy")
    ap.add_argument("--allow", action="append", default=["time://*"], metavar="GLOB")
    ap.add_argument("--max-attempts", type=int, default=3)
    args = ap.parse_args(argv)

    # The flow's action space: here, the time-tools connector (swap for your set).
    import urirun_connector_time_tools.core as tt
    registry = tt.conn.registry()

    # The llm:// connector that generates the flow.
    import urirun_connector_llm.core as llm
    llm_registry = llm.conn.registry()

    report = generate_run_repair(args.goal, registry, llm_registry, model=args.model,
                                 base_url=args.base_url, allow=args.allow,
                                 max_attempts=args.max_attempts)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
