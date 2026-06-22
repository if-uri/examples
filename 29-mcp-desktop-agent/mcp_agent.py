#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# The noVNC desktop, driven by an LLM through NATIVE TOOL-CALLING — no custom planner.
# urirun projects the connector's routes to MCP tools (name + inputSchema); we hand
# those tools to the model, it decides which to call and with what arguments, we execute
# each via urirun, feed the result back, and loop until the model is done. This is the
# decision-loop shape MCP clients (Claude, etc.) use: next call depends on prior results.

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOVNC = HERE.parent / "28-llm-novnc-desktop"
sys.path.insert(0, str(NOVNC))
sys.path.insert(0, str(HERE.parent.parent / "urirun" / "adapters" / "python"))

from novnc_connector import core as novnc  # noqa: E402
from urirun.runtime import _runtime as runtime, v2_mcp  # noqa: E402

MODEL = os.environ.get("URIRUN_MCP_MODEL", "openrouter/openai/gpt-4o-mini")
GOAL = os.environ.get(
    "GOAL",
    "On the desktop, open a terminal and run a command that prints 'mcp drove this "
    "desktop', then take a screenshot. Stop the session when done.",
)
MAX_TURNS = int(os.environ.get("URIRUN_MCP_MAX_TURNS", "10"))
OUT = HERE / "generated"


def _load_env() -> None:
    p = Path(os.environ.get("URIRUN_ENV", "/home/tom/github/if-uri/urirun/.env"))
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.split(" #", 1)[0].strip().strip('"').strip("'"))


def mcp_tools_as_functions(registry: dict) -> tuple[list[dict], dict]:
    """urirun routes -> MCP tools -> LLM function-calling `tools`. Returns (tools, name->uri)."""
    tools, index = [], {}
    for tool in v2_mcp.to_mcp_tools(registry):
        index[tool["name"]] = tool["_uri"]
        tools.append({"type": "function", "function": {
            "name": tool["name"],
            "description": tool.get("description", "") or tool["_uri"],
            "parameters": tool.get("inputSchema") or {"type": "object", "properties": {}},
        }})
    return tools, index


def run() -> dict:
    _load_env()
    OUT.mkdir(exist_ok=True)
    registry = novnc.registry()
    tools, index = mcp_tools_as_functions(registry)
    policy = runtime.build_policy(None, ["desktop://**"], None)

    import litellm
    litellm.suppress_debug_info = True
    os.environ.setdefault("LITELLM_LOG", "ERROR")

    messages = [
        {"role": "system", "content":
            "You operate a desktop via the provided tools. Call them in a sensible order "
            "(start the session before using it; stop it last). Fill each tool's arguments "
            "from its JSON schema. After you have taken the requested screenshot and stopped "
            "the session, reply with a short final summary and no more tool calls."},
        {"role": "user", "content": GOAL},
    ]

    trace, shots = [], []
    for _turn in range(MAX_TURNS):
        resp = litellm.completion(model=MODEL, messages=messages, tools=tools,
                                  tool_choice="auto", temperature=0, timeout=90, max_tokens=700)
        msg = resp.choices[0].message
        calls = getattr(msg, "tool_calls", None) or []
        messages.append({"role": "assistant", "content": msg.content or "",
                         "tool_calls": [c.model_dump() for c in calls] if calls else None})
        if not calls:
            return _finish(msg.content or "", trace, shots, index)
        for call in calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            env = v2_mcp.call_tool(name, args, registry, mode="execute", policy=policy)
            data = (env.get("result") or {}).get("value") if isinstance(env.get("result"), dict) else None
            # save screenshots; never feed the giant base64 back to the model
            tool_view = dict(data) if isinstance(data, dict) else {"ok": env.get("ok")}
            b64 = tool_view.pop("pngBase64", None)
            if b64:
                fn = f"{Path(tool_view.get('path', 'shot')).stem}.png"
                (OUT / fn).write_bytes(base64.b64decode(b64))
                shots.append(fn)
            trace.append({"tool": name, "uri": index.get(name), "args": args,
                          "ok": bool(env.get("ok")), "result": tool_view})
            messages.append({"role": "tool", "tool_call_id": call.id, "name": name,
                             "content": json.dumps({"ok": env.get("ok"), **tool_view})[:1500]})
    return _finish("(max turns reached)", trace, shots, index)


def _finish(final: str, trace: list, shots: list, index: dict) -> dict:
    typed = next((t["args"].get("text", "") for t in trace if (t["uri"] or "").endswith("/input/command/type")), "")
    shot_ok = any(t["result"].get("bytes", 0) > 0 for t in trace if isinstance(t.get("result"), dict))
    all_ok = all(t["ok"] for t in trace) and bool(trace)
    return {"goal": GOAL, "model": MODEL, "toolCalls": trace, "screenshots": shots,
            "finalMessage": final, "typedText": typed,
            "verdict": {"allToolCallsOk": all_ok, "screenshotCaptured": shot_ok,
                        "intentionRealized": all_ok and shot_ok}}


def _markdown(r: dict) -> str:
    v = r["verdict"]
    out = ["# noVNC desktop via MCP-style native tool-calling (no custom planner)", "",
           f"- **NL goal:** {r['goal']}", f"- **model:** {r['model']}  ·  **tools:** urirun routes as MCP tools", "",
           "## Tool calls the model made (it chose these, filling args from each tool's schema)", "",
           "| # | tool (→ uri) | ok | arguments |", "|---|--------------|----|-----------|"]
    for i, t in enumerate(r["toolCalls"]):
        out.append(f"| {i} | `{t['tool']}` → `{t['uri']}` | {'✓' if t['ok'] else '✗'} | `{json.dumps(t['args'])}` |")
    if r["screenshots"]:
        out += ["", "## Screenshot", "", f"![result](docs/{r['screenshots'][-1]})"]
    out += ["", f"**Final model message:** {r['finalMessage'][:300]}", "",
            "## Verdict", "",
            f"- {'✓' if v['allToolCallsOk'] else '✗'} every tool call succeeded",
            f"- {'✓' if v['screenshotCaptured'] else '✗'} a screenshot was captured",
            "", f"**Intention realized: {'YES' if v['intentionRealized'] else 'NO'}**", ""]
    return "\n".join(out)


def main() -> int:
    report = run()
    (OUT / "mcp-session.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "mcp-session-report.md").write_text(_markdown(report), encoding="utf-8")
    print(_markdown(report))
    return 0 if report["verdict"]["intentionRealized"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    finally:
        novnc.stop()
