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

## Ready-to-run YAML flows (`flows/`)

The same flows the LLM generates, as committed files you can run directly — no
model needed. Every step is a real URI; the action space is this example's
`tools.py` (+ the `llm` connector for the vision flow).

| File | What it does | Run |
| --- | --- | --- |
| [`flows/save-note.yaml`](flows/save-note.yaml) | `time://` → `note://` → `log://` | `python3 agent_repair.py --flow flows/save-note.yaml --execute` |
| [`flows/ocr-to-note.yaml`](flows/ocr-to-note.yaml) | OCR an image via `llm://host/vision/command/ocr`, store the text in `note://` (chained with `value_from`) | `python3 agent_repair.py --flow flows/ocr-to-note.yaml` (dry-run; `--execute` needs a vision model) |

```bash
make flow        # runs flows/save-note.yaml --execute
make flow-ocr    # shows the flows/ocr-to-note.yaml plan (dry-run)
```

`save-note.yaml` runs fully offline. `ocr-to-note.yaml` shows the vision URI and
result-chaining (`value_from: "read.result.response"`); dry-run validates the
plan, and `--execute` needs a vision model (a local Ollama `llava` runs as an
isolated step; a hosted model should be called in-process — see the llm
connector README).

Each YAML is also a valid `urirun-flow` document — add a `registry:` field and
you can run it with the canonical `urirun-flow run flows/save-note.yaml --execute`.

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

## Run with a REAL model (`--llm`)

The loop ships a real planner backed by the `llm` connector — pass `--llm`. The
model and key are read from **`examples/.env`** (`LLM_MODEL` + `OPENROUTER_API_KEY`,
gitignored) automatically, so no flags are needed:

```bash
# uses LLM_MODEL from examples/.env (e.g. openrouter/google/gemini-3.1-flash-image-preview)
python3 agent_repair.py --llm --execute "zapisz notatkę raport z wartością ok"

# or override the model explicitly:
python3 agent_repair.py --llm --model gemma4:e4b --execute "..."           # local Ollama
python3 agent_repair.py --llm --model openrouter/anthropic/claude-3.5-sonnet --execute "..."
```

The LLM call goes through the connector's `complete()` **in-process** (it's
infrastructure, not a policy-gated agent action) — which also avoids the
native-lib fragility litellm shows when run out-of-process.

Real run (model from `.env`, via OpenRouter):

```
── attempt 1 ✓ ──
  task:
    title: "Zapisz notatkę"
  steps:
    - id: "save-note"
      uri: "note://host/store/command/put"
      payload: {key: "raport", value: "ok"}
RESULT: ok after 1 attempt(s)        # note {"raport": "ok"} written to notes.json
```

Two things make a small local model reliable here: a **few-shot YAML example** in
the prompt, and a **tolerant normalizer** that coerces the shapes models drift
into (`task` as a bare string → `{title}`, integer `id`s → strings) before strict
validation — so a minor deviation doesn't burn a repair attempt, while real
structural errors still trigger the feedback loop.

## How the real planner is wired

`make_llm_planner()` calls the `llm` connector and returns YAML; the default
`plan_yaml()` stub stays for CI. The call is just:

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
