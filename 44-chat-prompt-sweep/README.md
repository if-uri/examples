# Chat Prompt Sweep

Runs a corpus of 100 natural-language prompts through the dashboard chat API.

The browser URL is only UI state. The actual command is:

```text
POST http://127.0.0.1:8194/api/chat/ask
```

## Quick Start

Smoke test 5 prompts without executing actions:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --limit 5
```

Run all 100 prompts as dry-run planning/routing tests:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py
```

LLM runs send an explicit model in the chat request. The runner resolves it in
this order: `--model`, `URIRUN_LLM_MODEL`, `LLM_MODEL`, then the dashboard's
non-secret `/api/chat/config`. Provider quota/rate-limit failures are reported
separately as `environmentBlocked`, without counting as a successful prompt.

Use the current dashboard URL as defaults for host/targets:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py \
  --from-url 'http://127.0.0.1:8194/?view=chat&tab=chat&execute=1&targets=host&action=chat%3Arun&discovery=node%3Alenovo&prompt=zrob+zrzut+jednego+ekranu++monitora%2C+na+kt%C3%B3rym+jest++przegl%C4%85darka+chrome&prompt_len=37&chat=panel'
```

Execute accepted flows on the host:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --execute --targets host
```

Cases marked `executeAllowed: false` are skipped during `--execute`, unless you
also pass `--include-side-effects`. That protects prompts such as "opublikuj
post na LinkedIn" from being executed during a broad sweep.

## Useful Slices

Only screen/capture prompts:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --category screen --execute
```

Only routing and node-selection prompts:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --category routing
```

Only Digital Twin prompts:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --category twin
```

Force no-LLM mode:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py --no-llm
```

## Outputs

Each run creates:

- `generated/<timestamp>/chat-prompt-results.jsonl` — full response per prompt.
- `generated/<timestamp>/summary.json` — aggregate counts by category.
- `generated/<timestamp>/REPORT.md` — human-readable table.
- `generated/<timestamp>/artifacts/` — materialized inline artifacts, if any.

The console line per prompt includes:

```text
[003/100] ok   screen-003 ok=1 steps=1 target=host 812ms
```

For deeper diagnosis inspect the JSONL fields:

- `model`, `environmentBlocked`, `generator`
- `selectedTargets`, `selectedNodes`
- `routingAccepted`, `routingViolations`, `runsOnByStep`
- `flowUris`, `timeline`
- `attachmentCount`, `artifactCount`
- `humanSignal`, `degraded`, `degradedReason`

## Recommended Gate

For local regression work, use a high but not absolute threshold:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py \
  --min-ok-rate 0.80
```

For live host execution, start with a narrow category:

```bash
python3 examples/44-chat-prompt-sweep/run_chat_prompts.py \
  --category screen --execute --min-ok-rate 0.70
```
