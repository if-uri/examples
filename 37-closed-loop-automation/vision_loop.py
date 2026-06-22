#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# VISION closed loop: the agent decides the next action from the NODE'S SCREEN, not
# from text. Each step: capture a FULL screenshot -> send the image to a vision LLM
# with the goal + available routes -> the model returns the next {uri, payload} or
# {done}. This is the "autonomous decisions from the monitor image" path.
#
# It needs (a) a vision-capable model (LLM_MODEL, e.g. a *-vision / *image* model) and
# (b) a screenshot route that returns the FULL base64 PNG — the stock browser-control
# screenshot routes truncate to base64_head to keep envelopes small, so deploy a
# full-image route (see make_full_shot below / examples deploy).
#
#   NODE_URL=... LLM_MODEL=... python3 vision_loop.py "open the LinkedIn login page"

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from urirun.node.client import NodeClient

NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8765")
NODE_NAME = os.environ.get("NODE", "laptop")
MODEL = os.environ.get("LLM_MODEL") or os.environ.get("URIRUN_LLM_MODEL")


def full_screenshot(client: NodeClient, shot_uri: str) -> str | None:
    """Return a data: URL for the node's screen, or None. Accepts a route that returns
    a full base64 PNG (key `base64`/`data`/`png`) — NOT the truncated `base64_head`."""
    env = client.run(shot_uri)
    res = env.get("result") or {}
    val = res.get("value", res) if isinstance(res, dict) else {}
    for key in ("base64", "data", "png", "screenshot"):
        blob = val.get(key) if isinstance(val, dict) else None
        if isinstance(blob, str) and len(blob) > 200:           # a real image, not a head
            return blob if blob.startswith("data:") else "data:image/png;base64," + blob
    return None


def make_vision_decider(model, client, shot_uri):
    """An agent decider that LOOKS at the node's screen. (goal, routes, transcript) ->
    {uri,payload} | {done}. Feeds the live screenshot to the vision model each step."""
    from urirun_connector_llm.core import complete

    system = ("You drive a computer toward a goal by LOOKING at its screen. Each turn you "
              "get the goal, the available routes (action space) and a SCREENSHOT of the node's "
              "monitor. Decide the single next action from what you SEE. Return strict JSON: "
              "{\"uri\":str,\"payload\":obj} for the next action, or {\"done\":true,\"reason\":str} "
              "when the goal is visibly achieved. Use only the given routes.")

    def decide(goal, routes, transcript):
        shot = full_screenshot(client, shot_uri)
        space = [{"uri": r["uri"], "inputs": list((r.get("inputSchema", {}).get("properties") or {}).keys())} for r in routes]
        prompt = json.dumps({"goal": goal, "routes": space, "transcript": transcript,
                             "screen": "attached" if shot else "unavailable"})
        out = complete(prompt=prompt, model=model, system=system, image=shot or "",
                       response_format={"type": "json_object"})
        text = out.get("response") or out.get("content") or "{}"
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            return {"done": True, "reason": "model did not return JSON", "raw": text[:200]}

    return decide


if __name__ == "__main__":
    import closed_loop
    if not MODEL:
        print("set LLM_MODEL (a vision model) + OPENROUTER_API_KEY"); raise SystemExit(2)
    goal = sys.argv[1] if len(sys.argv) > 1 else "Read what is on the screen and stop."
    client = NodeClient(NODE)
    shot_uri = os.environ.get("SHOT_URI", f"browser://{NODE_NAME}/cdp/page/query/screenshot-full")
    decide = make_vision_decider(MODEL, client, shot_uri)
    out = closed_loop.agent_loop(client, goal, decide, max_steps=4)
    print(json.dumps(out, indent=2)[:1500])
