#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# NL -> LLM -> YAML flow -> execute -> on failure feed the structured error back
# to the LLM -> corrected YAML -> re-run. A self-correcting URI-flow loop.
#
#   action space (allowed URIs + JSON Schema)
#        │
#        ▼
#   [plan_yaml]  LLM emits a urirun flow as YAML  (here: a deterministic stub)
#        ▼
#   Flow.from_yaml  →  validate every step.uri ∈ action space
#        ▼
#   run each step (urirun.run, query free / command gated)  ── dry-run | execute
#        ▼
#   ok? ── yes ─► done
#    │ no
#    ▼
#   build feedback {step, uri, error}  ──► plan_yaml(goal, space, feedback) ──► retry
#
# The planner here is a deterministic stand-in so the example runs in CI. To use a
# real model, replace `plan_yaml()` with a call to the `llm` connector
# (`llm://host/chat/command/complete`, model="openrouter/anthropic/claude-3.5-sonnet")
# and ask it to "return ONLY a urirun flow as YAML using these URIs"; the rest of
# the loop — validate, execute, feed the error back — is model-agnostic.

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _ensure_imports() -> None:
    """Make `import urirun`, `urirun_flow` and `urirun_connector_llm` work from
    sibling checkouts, so the example runs without installing anything."""
    for rel in (("..", "..", "urirun", "adapters", "python"),
                ("..", "..", "urirun-flow", "src"),
                ("..", "..", "urirun-connector-llm")):
        cand = os.path.normpath(os.path.join(HERE, *rel))
        if os.path.isdir(cand) and cand not in sys.path:
            sys.path.insert(0, cand)
            os.environ["PYTHONPATH"] = os.pathsep.join(
                p for p in (cand, os.environ.get("PYTHONPATH", "")) if p)


def _load_dotenv() -> None:
    """Load examples/.env (KEY=VALUE) into the environment without overriding
    anything already set — so `LLM_MODEL` / `OPENROUTER_API_KEY` come from there.
    The file is gitignored; never print or commit its contents."""
    path = os.path.normpath(os.path.join(HERE, "..", ".env"))
    if not os.path.isfile(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.split(" #", 1)[0].strip().strip('"').strip("'")  # drop inline comments/quotes
        if key and key not in os.environ:
            os.environ[key] = val


_ensure_imports()
_load_dotenv()

import urirun
from urirun_flow import Flow, FlowError

DEFAULT_LLM_MODEL = os.environ.get("LLM_MODEL") or os.environ.get("URIRUN_LLM_MODEL") or "llama3"

TOOLS = [sys.executable, os.path.join(HERE, "tools.py")]


def load_registry() -> dict:
    import subprocess
    raw = subprocess.run(TOOLS + ["bindings"], capture_output=True, text=True, check=True).stdout
    return urirun.compile_registry(json.loads(raw))


# --- the LLM (deterministic stub) ------------------------------------------

def plan_yaml(goal: str, allowed_uris: list[str], feedback: dict | None = None) -> str:
    """Stand-in for an LLM: returns a urirun flow as YAML, correcting itself when
    given feedback about a failed step.

    A real planner would send (goal, allowed_uris, feedback) to a model and get
    back this same YAML string. The behaviour we emulate:
      • first pass — a plausible mistake: it forgets the required `key` on the
        note step (empty), so the step fails at runtime;
      • after feedback that mentions `key` — it fills the key in and succeeds.
    """
    detail = goal.strip() or "agent run"
    # Derive a key from the goal only once the failure told us the key was missing.
    needs_key_fix = bool(feedback) and "key" in json.dumps(feedback, ensure_ascii=False).lower()
    key = "note-" + "".join(c for c in detail.lower() if c.isalnum())[:16] if needs_key_fix else ""

    steps = []
    if "time://host/clock/query/now" in allowed_uris:
        steps.append({"id": "stamp", "uri": "time://host/clock/query/now"})
    if "note://host/store/command/put" in allowed_uris:
        steps.append({"id": "save", "uri": "note://host/store/command/put",
                      "payload": {"key": key, "value": detail}})
    if "log://host/run/command/write" in allowed_uris:
        steps.append({"id": "record", "uri": "log://host/run/command/write",
                      "payload": {"event": "repair-demo", "detail": detail}})

    flow = {"task": {"title": detail}, "allow": ["time://*", "note://*", "log://*"], "steps": steps}
    import yaml
    return yaml.safe_dump(flow, sort_keys=False, allow_unicode=True)


# --- the real LLM planner (calls the llm:// connector) ---------------------

_LLM_REGISTRY = None


def _llm_registry() -> dict:
    """A tiny registry containing only the llm:// routes, used to drive the model.
    Kept separate from the agent's action space (the model plans *over* the agent
    routes, it doesn't get to call llm:// as one of them)."""
    global _LLM_REGISTRY
    if _LLM_REGISTRY is None:
        import urirun_connector_llm
        _LLM_REGISTRY = urirun.compile_registry(urirun_connector_llm.urirun_bindings())
    return _LLM_REGISTRY


def _strip_fences(text: str) -> str:
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.removeprefix("yaml\n").strip()


def make_llm_planner(space: list[dict], model: str, base_url: str = "http://localhost:11434",
                     provider: str = ""):
    """Return a planner backed by a real model via `llm://host/chat/command/complete`.

    The model receives the goal, the allowed URIs *with their required fields*, and
    (on a retry) the structured failure — and must return a urirun flow as YAML.
    """
    routes = [{"uri": r["uri"], "required": r.get("required", []),
               "inputs": r.get("inputs", [])} for r in space]

    def plan(goal: str, allowed: list[str], feedback: dict | None = None) -> str:
        prompt = (
            "You translate a goal into a urirun flow. Return ONLY a YAML document — "
            "no prose, no code fences.\n"
            "Exact shape (copy it): `task` is a MAPPING, each `id` is a STRING in quotes:\n"
            "task:\n  title: \"<short title>\"\n"
            "steps:\n"
            "  - id: \"save\"\n"
            "    uri: \"note://host/store/command/put\"\n"
            "    payload:\n      key: \"my-key\"\n      value: \"my-value\"\n"
            "Use ONLY these routes, and fill every `required` field in payload:\n"
            + json.dumps(routes, ensure_ascii=False) + "\n"
            "GOAL: " + goal
        )
        if feedback:
            prompt += ("\nThe previous flow FAILED. Fix it and return corrected YAML.\n"
                       "Error:\n" + json.dumps(feedback, ensure_ascii=False))
        env = urirun.run("llm://host/chat/command/complete", _llm_registry(),
                         {"prompt": prompt, "model": model, "base_url": base_url, "provider": provider},
                         mode="execute", policy=urirun.policy(allow=["llm://*"]))
        data = urirun.result_data(env)
        if not (isinstance(data, dict) and data.get("ok")):
            raise RuntimeError(f"llm call failed: {(data or {}).get('error') or env.get('error')}")
        return _strip_fences(data.get("response", ""))

    return plan


# --- tolerate common LLM deviations before strict validation ---------------

def _normalize_flow_dict(raw: object) -> dict:
    """Coerce the loose shapes models tend to emit into the strict Flow schema:
    `task` as a bare string → {title: ...}; integer step `id`s → strings; a single
    step mapping → a one-item list. Real structural errors still surface."""
    d = dict(raw) if isinstance(raw, dict) else {}
    task = d.get("task")
    if isinstance(task, str):
        d["task"] = {"title": task}
    elif task is None:
        d["task"] = {}
    steps = d.get("steps")
    if isinstance(steps, dict):
        steps = [steps]
    norm = []
    for i, s in enumerate(steps or []):
        if not isinstance(s, dict):
            continue
        s = dict(s)
        s["id"] = str(s.get("id", f"s{i + 1}"))
        if "payload" in s and not isinstance(s["payload"], dict):
            s.pop("payload")
        norm.append(s)
    d["steps"] = norm
    return d


# --- the loop --------------------------------------------------------------

def run_step(registry: dict, uri: str, payload: dict, *, execute: bool) -> tuple[bool, dict]:
    scheme = uri.split("://", 1)[0]
    env = urirun.run(uri, registry, payload, mode="execute" if execute else "dry-run",
                     policy=urirun.policy(allow=[f"{scheme}://*"]))
    data = urirun.result_data(env)
    ok = bool(env.get("ok")) and (data.get("ok", True) if isinstance(data, dict) else True)
    return ok, (data if isinstance(data, dict) else {"value": data})


def repair_run(goal: str, registry: dict, *, tries: int = 3, execute: bool = False,
               planner=plan_yaml) -> dict:
    """Plan → validate → execute, repairing from the structured error up to `tries`."""
    space = urirun.action_space(registry)
    allowed = sorted({r["uri"] for r in space})
    feedback: dict | None = None
    transcript: list[dict] = []

    for attempt in range(1, tries + 1):
        yaml_text = planner(goal, allowed, feedback)
        record: dict = {"attempt": attempt, "yaml": yaml_text}

        # 1) parse YAML, tolerate common LLM shape deviations, then schema-validate
        try:
            import yaml
            flow = Flow(**_normalize_flow_dict(yaml.safe_load(yaml_text)))
        except (FlowError, ValueError, yaml.YAMLError) as exc:
            feedback = {"stage": "parse", "error": str(exc)}
            record.update(ok=False, feedback=feedback); transcript.append(record); continue

        # 2) every step URI must be in the action space (hard safety boundary)
        unknown = [s.uri for s in flow.steps if s.uri not in set(allowed)]
        if unknown:
            feedback = {"stage": "validate", "unknownUris": unknown, "allowed": allowed}
            record.update(ok=False, feedback=feedback); transcript.append(record); continue

        # 3) execute step by step; stop and capture the first failure
        results: dict[str, dict] = {}
        failed: dict | None = None
        for step in flow.order():
            ok, data = run_step(registry, step.uri, step.payload, execute=execute)
            results[step.id] = data
            if not ok:
                failed = {"stage": "execute", "step": step.id, "uri": step.uri,
                          "error": data.get("error", "step returned ok=false"), "data": data}
                break

        record.update(ok=failed is None, results=results, failed=failed)
        transcript.append(record)
        if failed is None:
            return {"ok": True, "attempts": attempt, "flow": flow.to_dict(),
                    "transcript": transcript, "results": results}
        feedback = failed  # ← this is what the LLM sees on the next attempt

    return {"ok": False, "attempts": tries, "transcript": transcript, "lastError": feedback}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent_repair", description="NL→YAML flow→execute→repair loop")
    parser.add_argument("goal", nargs="?", default="zapisz notatkę o uruchomieniu")
    parser.add_argument("--execute", action="store_true", help="actually run steps (default: dry-run)")
    parser.add_argument("--tries", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--llm", action="store_true", help="use a real model via llm:// (default: deterministic stub)")
    parser.add_argument("--model", default=DEFAULT_LLM_MODEL,
                        help="LLM model id (default from examples/.env LLM_MODEL: %(default)s)")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama backend (ignored for litellm models)")
    parser.add_argument("--provider", default="", help="force litellm/ollama")
    args = parser.parse_args(argv)

    registry = load_registry()
    if args.llm:
        space = urirun.action_space(registry)
        planner = make_llm_planner(space, args.model, args.base_url, args.provider)
    else:
        planner = plan_yaml
    report = repair_run(args.goal, registry, tries=args.tries, execute=args.execute, planner=planner)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"goal: {args.goal}   ({'EXECUTE' if args.execute else 'dry-run'})")
        for r in report["transcript"]:
            mark = "✓" if r["ok"] else "✗"
            print(f"\n── attempt {r['attempt']} {mark} ──")
            print("\n".join("  " + ln for ln in r["yaml"].strip().splitlines()))
            if not r["ok"]:
                why = r.get("failed") or r.get("feedback")
                print(f"  → FAILED: {json.dumps(why, ensure_ascii=False)}")
        print(f"\nRESULT: {'ok' if report['ok'] else 'failed'} after {report['attempts']} attempt(s)")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
