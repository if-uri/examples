# 15 — Self-correcting YAML flow (NL → LLM → execute → repair)

An LLM turns a natural-language goal into a **urirun flow as YAML**, the loop
runs it under policy, and **if a step fails the structured error is fed back to
the LLM to get a corrected flow** — then it re-runs. This is example 14's
action-space idea plus a YAML flow and a self-repair loop.

```
action space (allowed URIs + JSON Schema)
     │
     ▼
[plan_yaml]  LLM emits a urirun flow as YAML
     ▼
Flow.from_yaml  →  validate every step.uri ∈ action space   (hard safety boundary)
     ▼
run each step (urirun.run; query free / command gated)   ── dry-run | --execute
     ▼
ok? ── yes ─► done
 │ no
 ▼
feedback {step, uri, error}  ──►  plan_yaml(goal, space, feedback)  ──►  retry
```

## Run

```bash
python3 agent_repair.py "zapisz notatke o uruchomieniu"             # dry-run (plan only)
python3 agent_repair.py --execute "zapisz notatke o uruchomieniu"   # actually run + repair
python3 agent_repair.py --execute --json "..."                      # machine-readable transcript
```

The bundled stub planner deliberately makes a plausible mistake on the first pass
(forgets the required `key` on the `note://` step), so you can watch the loop
recover:

```
── attempt 1 ✗ ──
  ... note://host/store/command/put  payload: {key: '', value: ...}
  → FAILED: {"step":"save","uri":"note://...","error":"key is required and must be non-empty"}
── attempt 2 ✓ ──
  ... note://host/store/command/put  payload: {key: note-..., value: ...}
RESULT: ok after 2 attempt(s)
```

## Plug in a real LLM

`plan_yaml()` is a deterministic stand-in so the example runs in CI. Replace it
with a call to the **`llm` connector** — pass the goal, the allowed URIs and the
last error, and ask for YAML only:

```python
import urirun, json
def plan_yaml(goal, allowed_uris, feedback=None):
    prompt = (
        "Return ONLY a urirun flow as YAML (keys: task, allow, steps[].{id,uri,payload,depends_on}). "
        f"Use ONLY these URIs: {allowed_uris}.\nGOAL: {goal}"
        + (f"\nThe previous flow FAILED, fix it. Error:\n{json.dumps(feedback)}" if feedback else "")
    )
    env = urirun.run("llm://host/chat/command/complete",
                     registry, {"prompt": prompt,
                                "model": "openrouter/anthropic/claude-3.5-sonnet"},
                     mode="execute", policy=urirun.policy(allow=["llm://*"]))
    text = urirun.result_data(env)["response"]
    return text.strip().removeprefix("```yaml").removeprefix("```").removesuffix("```")
```

Model/provider follow the `llm` connector rules: a provider-prefixed `model`
(`openrouter/...`, `openai/...`) goes through litellm with the matching
`*_API_KEY`; a bare model (`llama3`) hits a local Ollama. Everything else in the
loop — validate, execute, feed the error back — is unchanged.

## Why it's safe

- **Action-space validation:** any step whose URI is not in the registry is
  rejected before execution (the model cannot invent a route).
- **Policy gate:** `command` routes only run with permission; `query` routes are
  read-only. The same boundary a node's `--allow` enforces.
- **Dry-run first:** without `--execute` you see the planned YAML and nothing
  runs.

## Test

```bash
python3 -m pytest test_repair.py -q
```
