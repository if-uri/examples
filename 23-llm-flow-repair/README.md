# 23 — self-repairing LLM flow over `llm://`

Talk to an LLM through the `llm://` connector (you pick the **model** and the
**provider**), have it emit a **YAML flow**, run that flow through urirun, and — if
a step fails — feed the step + error back to the model so it returns a **corrected
flow**. Repeat until it runs or the attempt budget is spent.

```
action space (URIs + schemas)
        │
        ▼
llm://host/chat/command/complete   ──▶  YAML flow
        ▲                                   │
        │ failing step + error              ▼
        └────────── urirun runs each step under policy ──▶ ok → done
```

## Model + provider selection (on the `llm://` payload)

`llm://host/chat/command/complete` takes `{prompt, model, base_url}`:

- **`model`** — the model name (`llama3`, `mistral`, `claude-3.5-sonnet`, …).
- **`base_url`** — the **provider** endpoint. Default is a local Ollama
  (`http://localhost:11434`, which serves `/api/generate`). Point it at a
  **litellm / OpenAI-compatible proxy** to use hosted models (Claude, GPT, …):
  the proxy is the provider, `model` selects which model behind it.

```bash
# local Ollama
python3 repair_flow.py "stamp the current time" --model llama3 --base-url http://localhost:11434

# hosted model via a litellm proxy (the proxy is the provider)
python3 repair_flow.py "stamp the current time" \
    --model claude-3.5-sonnet --base-url http://localhost:4000
```

The flow's **action space** here is the `time-tools` connector; swap
`tt.conn.registry()` in `repair_flow.py:main` for your own set (or
`urirun.entry_point_registry()` for every installed connector).

## The loop (`generate_run_repair`)

1. `urirun.action_space(registry)` → the routes + input schemas the model may use.
2. `ask_llm()` calls `llm://` → raw reply → `_extract_yaml()` strips ``` fences.
3. `run_flow()` runs each step with `urirun.run(..., mode="execute", policy=urirun.policy(allow=...))`,
   unwraps the result via `urirun.result_data(env)`, stops on the first failure.
4. On failure the next prompt includes the failing step + error + the previous
   YAML, so the model returns a fix. Loops up to `--max-attempts`.

Safety is urirun's: `query` routes run freely, `command` routes only under the
`--allow` policy; secrets stay deny-by-default.

## Test (offline, no model needed)

A fake LLM returns a broken flow first (unknown route), then — once the error is
fed back — a valid one, proving the repair loop end-to-end:

```bash
pytest test_repair.py -q
```
