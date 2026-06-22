"""Flow stand-in for urillm: deterministically 'summarize' a prompt."""

from __future__ import annotations

import re
from typing import Any


def complete(prompt: str = "", model: str = "mock-llm", host: str = "host") -> dict[str, Any]:
    # A real LLM would summarize; we extract the salient fields deterministically so
    # the flow is testable. The point is that `prompt` carries the OCR step's text.
    total = re.search(r"TOTAL DUE:\s*([\d.]+\s*\w+)", prompt)
    due = re.search(r"due\s*([\d-]+)", prompt)
    if total:
        summary = f"Invoice for {total.group(1)}" + (f", due {due.group(1)}" if due else "") + "."
    elif due:
        summary = f"Action due {due.group(1)}."
    else:
        summary = "No invoice/date found in the captured text."
    return {"model": model, "summary": summary, "prompt_chars": len(prompt)}
