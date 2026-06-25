#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# NL -> ui:// plan -> execute. Turns a natural-language desktop task into a sequence
# of kvm://.../ui/* (+ browser/app) URIs and runs them on a urirun node with a
# perceive->act->verify loop. This is the planner that closes the autonomy loop on
# top of the cross-platform kvm connector's semantic UI layer.
#
#   PLAN ONLY:  python run.py "open a terminal and type echo hello"
#   EXECUTE:    python run.py "..." --node http://192.168.188.201:8765 --execute \
#                              --identity ~/.ssh/id_ed25519
#
# LLM via examples/.env (LLM_MODEL / OPENROUTER_API_KEY), in-process (litellm).

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))

from urirun.node.mesh import _maybe_load_dotenv  # noqa: E402

# The action space the planner may emit. Each is a real route on the node; the
# kvm ui/* routes carry the AT-SPI->imgl->vql locate fallback + input.
ACTIONS = """
kvm://{node}/ui/query/find     {"text"?, "role"?, "app"?}        locate an element (no act)
kvm://{node}/ui/command/click  {"text"?, "role"?, "app"?}        find a control and click it
kvm://{node}/ui/command/fill   {"text": field, "value", "verify"?:true}  focus a field and type
kvm://{node}/ui/query/wait     {"text"?, "role"?, "timeout"?}    poll until a target appears
kvm://{node}/ui/query/verify   {"expect"}                        assert text is on screen
kvm://{node}/input/command/type {"text"}                         type into the focused field
kvm://{node}/input/command/key  {"keys": "ctrl+l"|"enter"|...}   a key / hotkey
kvm://{node}/screen/query/capture {}                             screenshot (for observation)
app://{node}/desktop/command/launch {"app": "gnome-terminal"|...} launch a desktop app
browser://{node}/desktop/page/command/open {"url"}               open a URL in the browser
""".strip()

SYSTEM = (
    "You convert a natural-language desktop task into a STRICT JSON plan of URI steps for "
    "the ifURI urirun mesh. Output ONLY valid JSON: {\"steps\":[{\"uri\":..., \"payload\":{...}, "
    "\"why\":\"short\"}]}. Every key and value MUST be a separate double-quoted string. "
    "Use the perceive->act->verify discipline: prefer ui/command/* "
    "(which locate by accessible role/name, not coordinates), insert ui/query/wait before "
    "acting on something that must appear, and ui/query/verify to confirm a result. Target "
    "elements by their visible text or accessibility role (entry/push button/frame/section). "
    "To focus an application WINDOW, use ui/command/click with app=<app name, e.g. 'terminal', "
    "'chrome'> and role='frame' (do NOT match the window title text — it varies). For controls "
    "inside an app, use visible text + role (push button, entry). "
    "Do not invent routes outside the action list. Keep the plan minimal."
)


def plan(task: str, node: str) -> dict:
    import litellm
    import re
    model = os.getenv("URIRUN_LLM_MODEL") or os.getenv("LLM_MODEL")
    if not model:
        raise SystemExit("LLM_MODEL not set (examples/.env)")
    litellm.suppress_debug_info = True
    msgs = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps({
            "task": task,
            "node": node,
            "actions": ACTIONS.replace("{node}", node),
        }, ensure_ascii=False)},
    ]
    import contextlib
    with contextlib.redirect_stdout(sys.stderr):
        resp = litellm.completion(model=model, messages=msgs, temperature=0,
                                  response_format={"type": "json_object"})
    text = resp.choices[0].message.content
    
    # Clean up markdown code blocks
    if "```" in text:
        m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
        if m:
            text = m.group(1)
            
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response: {text!r}")
        
    cleaned = text[start:end + 1]
    # Repair common LLM key-value quoting issues (e.g., "why: message" -> "why": "message")
    cleaned = re.sub(r'"(why|uri|payload):\s*([^"]+)"', r'"\1": "\2"', cleaned)
    # Remove trailing commas before closing braces/brackets
    cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
    
    try:
        return json.loads(cleaned)
    except Exception as exc:
        sys.stderr.write(f"Failed to parse cleaned JSON:\n{cleaned}\nOriginal text was:\n{text}\n")
        raise




def run_uri(node_url: str, uri: str, payload: dict, identity: str, timeout: float = 40) -> dict:
    cmd = [str(ROOT / "urirun" / "venv" / "bin" / "urirun"), "host", "run", node_url, uri,
           "--payload", json.dumps(payload), "--timeout", str(timeout)]
    if identity:
        cmd += ["--identity", os.path.expanduser(identity)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    import re
    m = re.search(r"\{.*\}", p.stdout, re.S)
    return json.loads(m.group(0)) if m else {"ok": False, "raw": (p.stdout + p.stderr)[:300]}


def _ok(env: dict) -> bool:
    if not isinstance(env, dict):
        return False
    if env.get("ok") is False:
        return False
    res = env.get("result")
    return not (isinstance(res, dict) and res.get("ok") is False)


def save_shot(node: str, identity: str, outdir: str, label: str, at=None) -> str | None:
    """Pull a screenshot from the node and save it on the HOST with a timestamp; if
    ``at=(x,y)`` is given, also save a zoomed tile around the action point (small file,
    only where something is happening) so a session is immediately reviewable on the host."""
    try:
        env = run_uri(node, "kvm://{n}/screen/query/capture".replace("{n}", "laptop"),
                      {"base64": True}, identity, timeout=40)
        import base64 as _b64
        import io

        def find(o, k):
            if isinstance(o, dict):
                if k in o and o[k] is not None:
                    return o[k]
                for v in o.values():
                    r = find(v, k)
                    if r is not None:
                        return r
            if isinstance(o, list):
                for v in o:
                    r = find(v, k)
                    if r is not None:
                        return r
        b = find(env, "pngBase64")
        if not b:
            return None
        from PIL import Image
        os.makedirs(outdir, exist_ok=True)
        ts = time.strftime("%H%M%S")
        im = Image.open(io.BytesIO(_b64.b64decode(b))).convert("RGB")
        full = os.path.join(outdir, f"{ts}-{label}.png")
        im.save(full)
        if at:
            x, y = at
            crop = im.crop((max(0, x - 350), max(0, y - 240), min(im.width, x + 350), min(im.height, y + 240)))
            crop.resize((crop.width * 2, crop.height * 2)).save(os.path.join(outdir, f"{ts}-{label}-zoom.png"))
        return full
    except Exception:  # noqa: BLE001 - shot-saving must never break the run
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--node", default="http://192.168.188.201:8765")
    ap.add_argument("--name", default="laptop", help="node self-name used in URIs")
    ap.add_argument("--identity", default="~/.ssh/id_ed25519")
    ap.add_argument("--execute", action="store_true", help="run the plan (else print only)")
    ap.add_argument("--save-shots", dest="save_shots", default="", metavar="DIR",
                    help="save a host-side screenshot (+ zoom around the action point) after each step")
    args = ap.parse_args()

    _maybe_load_dotenv(str(ROOT / "examples" / ".env"))

    flow = plan(args.task, args.name)
    steps = flow.get("steps", [])
    print(json.dumps(flow, indent=2, ensure_ascii=False))
    if not args.execute:
        print(f"\n[plan only] {len(steps)} step(s). Re-run with --execute to run them.")
        return 0

    shots = os.path.expanduser(args.save_shots) if args.save_shots else ""
    if shots:
        save_shot(args.node, args.identity, shots, "step00-before")
    print(f"\n== executing {len(steps)} step(s) on {args.node} ==")
    for i, st in enumerate(steps, 1):
        uri, payload = st.get("uri", ""), st.get("payload", {})
        env = run_uri(args.node, uri, payload, args.identity)
        ok = _ok(env)
        print(f"  [{i}/{len(steps)}] {'OK ' if ok else 'FAIL'} {uri} {json.dumps(payload, ensure_ascii=False)[:80]}")
        if shots:
            at = None
            if isinstance(payload.get("x"), int) and isinstance(payload.get("y"), int):
                at = (payload["x"], payload["y"])
            label = f"step{i:02d}-" + uri.split("/")[-1]
            p = save_shot(args.node, args.identity, shots, label, at)
            if p:
                print(f"        shot: {p}" + ("  (+zoom)" if at else ""))
        if not ok:
            print("    ->", json.dumps(env.get("result", env), ensure_ascii=False)[:200])
            return 1
        time.sleep(0.6)
    print("== done ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
