#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Computer-use agent loop over the kvm:// connector, following the Gemini Computer Use
# pattern: screenshot -> model returns a UI action with NORMALIZED (0-1000) coords + an
# `intent` -> denormalize to the LIVE screen size -> execute via the connector -> capture
# the new state -> repeat, until done or a safety stop.
#
# Why this design fixes the .201 coordinate mess:
#   * coords are normalized (0-1000); we denormalize to the CURRENT capture's pixel size
#     every turn, so a fluctuating display resolution can't desync us.
#   * clicks go through the uinput ABSOLUTE device (kvm://.../abs/command/click) which is
#     linear + acceleration-free; `calibrate` fits the residual screenshot<->device
#     transform once (the OS-desktop analogue of Playwright's controlled viewport).
#   * human-in-the-loop: irreversible actions (post/send/submit/buy) STOP for confirmation.
#
# Grounding model is pluggable. Best: a real computer-use / GUI-grounding model
# (Gemini 3.5 Flash computer_use, Claude Computer Use, or a dedicated grounding model).
# A generic image model (e.g. gemini-*-image-preview) grounds poorly — don't use it.
#
#   python computer_use.py calibrate                 # fit the screenshot<->abs transform
#   python computer_use.py run "open the LinkedIn composer and draft a post about X"
#
from __future__ import annotations
import argparse, base64, io, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path("/home/tom/github/if-uri")
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))
from urirun.node.mesh import _maybe_load_dotenv  # noqa: E402

URIRUN = str(ROOT / "urirun" / "venv" / "bin" / "urirun")
IDENT = os.path.expanduser("~/.ssh/id_ed25519")
ART = os.path.expanduser("~/.urirun/artifacts/kvm-laptop")
CALIB = os.path.join(ART, "calibration.json")
NODE = "http://192.168.188.201:8765"

IRREVERSIBLE = re.compile(r"\b(post|publish|send|submit|confirm|buy|pay|delete|share|opublikuj|wyślij)\b", re.I)


def _find(o, k):
    if isinstance(o, dict):
        if k in o and o[k] is not None:
            return o[k]
        for v in o.values():
            r = _find(v, k)
            if r is not None:
                return r
    if isinstance(o, list):
        for v in o:
            r = _find(v, k)
            if r is not None:
                return r


def run_uri(uri: str, payload: dict, timeout: float = 40) -> dict:
    p = subprocess.run([URIRUN, "host", "run", NODE, uri, "--payload", json.dumps(payload),
                        "--identity", IDENT, "--timeout", str(timeout)], capture_output=True, text=True)
    m = re.search(r"\{.*\}", p.stdout, re.S)
    return json.loads(m.group(0)) if m else {"ok": False, "raw": (p.stdout + p.stderr)[:300]}


def capture(label: str = "") -> tuple[bytes, int, int]:
    env = run_uri("kvm://laptop/screen/query/capture", {"base64": True})
    png = base64.b64decode(_find(env, "pngBase64"))
    from PIL import Image
    w, h = Image.open(io.BytesIO(png)).size
    if label:
        os.makedirs(ART, exist_ok=True)
        Image.open(io.BytesIO(png)).save(os.path.join(ART, f"{time.strftime('%H%M%S')}-{label}.png"))
    return png, w, h


# --- calibration: fit screenshot-pixel -> uinput-abs (residual transform) -------------- #
def load_calib() -> dict | None:
    try:
        return json.load(open(CALIB))
    except Exception:  # noqa: BLE001
        return None


def abs_click(px: int, py: int, sw: int, sh: int, button: str = "left", do_click: bool = True) -> dict:
    """Click screenshot-pixel (px,py). Applies the stored calibration so the uinput
    absolute device lands on the pixel even when its native mapping is skewed."""
    cal = load_calib()
    if cal:  # map pixel -> calibrated abs fraction (0..1) -> pass as abs raw range
        fx = cal["ax"] * (px / sw) + cal["bx"]
        fy = cal["ay"] * (py / sh) + cal["by"]
        ax = max(0, min(65535, int(fx * 65535)))
        ay = max(0, min(65535, int(fy * 65535)))
        return run_uri("kvm://laptop/abs/command/click", {"x": ax, "y": ay, "button": button, "do_click": do_click})
    return run_uri("kvm://laptop/abs/command/click", {"x": px, "y": py, "sw": sw, "sh": sh, "button": button, "do_click": do_click})


def calibrate() -> int:
    """Open a feedback page that prints the click point, click known abs fractions, read the
    reported page coords back from screenshots, and fit abs<->pixel. Breaks the
    cursor-invisible problem (the PAGE reports where the click landed)."""
    page = ("data:text/html,<body style='margin:0;background:%23000;color:%230f0;"
            "font:90px monospace' onclick=\"c.textContent=Math.round(event.clientX)+','+"
            "Math.round(event.clientY)+'|'+innerWidth+'x'+innerHeight\">"
            "<div id=c style='padding:30px'>CLICK</div></body>")
    # navigate + fullscreen so viewport == screen (page coord == screen pixel)
    run_uri("kvm://laptop/task/command/run", {"steps": [
        {"op": "key", "keys": "ctrl+l", "after": 0.5}, {"op": "key", "keys": "ctrl+a", "after": 0.3},
        {"op": "type", "text": page}, {"op": "key", "keys": "enter", "after": 2.0},
        {"op": "key", "keys": "f11", "after": 1.5}]})
    samples = [(0.25, 0.25), (0.75, 0.25), (0.5, 0.75)]
    print("Calibration: click each abs fraction, then READ the page-reported coords from the\n"
          "saved screenshot and enter them. (3 points fit a linear abs<->pixel map.)")
    pts = []
    for i, (fx, fy) in enumerate(samples):
        ax, ay = int(fx * 65535), int(fy * 65535)
        run_uri("kvm://laptop/abs/command/click", {"x": ax, "y": ay})
        time.sleep(1.2)
        _png, w, h = capture(f"calib-{i}")
        print(f"  point {i}: clicked abs_frac=({fx},{fy}); see {ART}/*-calib-{i}.png")
        raw = input(f"    enter reported 'X,Y' (page px) for point {i}: ").strip()
        cx, cy = (int(v) for v in raw.replace("|", ",").split(",")[:2])
        pts.append((fx, fy, cx / w, cy / h))
    # linear fit per axis: pixel_frac = a*abs_frac + b  ->  invert when clicking
    import statistics
    axs = [(p[0], p[2]) for p in pts]; ays = [(p[1], p[3]) for p in pts]

    def fit(pairs):
        xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]
        mx, my = statistics.mean(xs), statistics.mean(ys)
        a = sum((x - mx) * (y - my) for x, y in pairs) / (sum((x - mx) ** 2 for x in xs) or 1)
        return a, my - a * mx
    # we want abs_frac given pixel_frac: invert pixel_frac=a*abs+b  -> abs=(pf-b)/a
    pa, pb = fit(axs); qa, qb = fit(ays)
    cal = {"ax": 1 / pa, "bx": -pb / pa, "ay": 1 / qa, "by": -qb / qa}
    json.dump(cal, open(CALIB, "w"), indent=1)
    run_uri("kvm://laptop/input/command/key", {"keys": "f11"})  # exit fullscreen
    print("calibration saved:", cal)
    return 0


# --- grounding (pluggable) ------------------------------------------------------------- #
GROUND_SYS = (
    "You are a desktop computer-use agent. Given a screenshot and a goal, return the SINGLE "
    "next UI action as STRICT JSON: {\"name\":\"click|type|key|scroll|done\", \"x\":0-1000, "
    "\"y\":0-1000, \"text\":\"...\", \"keys\":\"ctrl+l\", \"intent\":\"why\"}. x,y are "
    "NORMALIZED 0-1000 of the image. Use 'done' when the goal is reached. Be precise about "
    "which element to click.")


def ground(png: bytes, goal: str, history: list) -> dict:
    import litellm
    model = os.getenv("URIRUN_LLM_MODEL") or os.getenv("LLM_MODEL")
    data_url = "data:image/png;base64," + base64.b64encode(png).decode()
    litellm.suppress_debug_info = True
    import contextlib
    with contextlib.redirect_stdout(sys.stderr):
        resp = litellm.completion(model=model, temperature=0, messages=[
            {"role": "system", "content": GROUND_SYS},
            {"role": "user", "content": [
                {"type": "text", "text": f"GOAL: {goal}\nDONE SO FAR: {history[-4:]}"},
                {"type": "image_url", "image_url": {"url": data_url}}]}])
    t = resp.choices[0].message.content
    return json.loads(t[t.find("{"):t.rfind("}") + 1])


def execute(act: dict, sw: int, sh: int, confirm: bool) -> bool:
    name = act.get("name")
    if name == "done":
        return False
    if confirm and name in ("click", "type") and IRREVERSIBLE.search(act.get("intent", "") + act.get("text", "")):
        ok = input(f"  [SAFETY] irreversible '{act.get('intent')}' — proceed? [y/N] ").strip().lower()
        if ok != "y":
            print("  user declined; stopping."); return False
    if name == "click":
        px = int(act["x"] / 1000 * sw); py = int(act["y"] / 1000 * sh)
        abs_click(px, py, sw, sh)
    elif name == "type":
        if "x" in act:
            abs_click(int(act["x"] / 1000 * sw), int(act["y"] / 1000 * sh), sw, sh); time.sleep(0.4)
        run_uri("kvm://laptop/input/command/type", {"text": act.get("text", "")})
        if act.get("press_enter"):
            run_uri("kvm://laptop/input/command/key", {"keys": "enter"})
    elif name == "key":
        run_uri("kvm://laptop/input/command/key", {"keys": act.get("keys", "")})
    elif name == "scroll":
        run_uri("kvm://laptop/input/command/scroll", {"dy": -5 if act.get("direction") != "up" else 5})
    return True


def agent(goal: str, turns: int, confirm: bool, save: bool) -> int:
    history = []
    for i in range(turns):
        png, w, h = capture(f"turn{i:02d}" if save else "")
        try:
            act = ground(png, goal, history)
        except Exception as exc:  # noqa: BLE001
            print("ground error:", exc); return 1
        print(f"--- turn {i+1}: {act.get('name')} ({act.get('intent','')}) {('@%s,%s' % (act.get('x'),act.get('y'))) if 'x' in act else ''}")
        history.append({"name": act.get("name"), "intent": act.get("intent")})
        if not execute(act, w, h, confirm):
            print("done."); return 0
        time.sleep(1.2)
    print("turn limit reached.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["calibrate", "run"])
    ap.add_argument("goal", nargs="?", default="")
    ap.add_argument("--turns", type=int, default=8)
    ap.add_argument("--no-confirm", action="store_true", help="skip human-in-the-loop on irreversible actions")
    ap.add_argument("--save-shots", action="store_true")
    args = ap.parse_args()
    _maybe_load_dotenv(str(ROOT / "examples" / ".env"))
    if args.cmd == "calibrate":
        return calibrate()
    if not args.goal:
        print("goal required for run"); return 2
    return agent(args.goal, args.turns, not args.no_confirm, args.save_shots)


if __name__ == "__main__":
    raise SystemExit(main())
