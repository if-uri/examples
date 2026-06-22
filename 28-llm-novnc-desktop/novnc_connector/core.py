# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A SEPARATE connector that drives a noVNC desktop running in Docker. Each route is a
# typed @handler, so its input JSON Schema is derived from the function signature and
# shows up in the agent action space — which is exactly what lets an LLM pick the right
# command AND fill its parameters from a natural-language intent.
#
# This is the "connector" half of the answer: desktop/Docker control lives in a
# connector, never in urirun core. Core only learned to put each route's schema in the
# action space (see urirun.runtime.agent.action_space).

from __future__ import annotations

import base64
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import urirun

CONNECTOR_ID = "novnc"
conn = urirun.connector(CONNECTOR_ID, scheme="desktop", target="novnc")

IMAGE = os.environ.get("URIRUN_NOVNC_IMAGE", "dorowu/ubuntu-desktop-lxde-vnc:latest")
DISPLAY = ":1"
STATE = Path(os.environ.get("URIRUN_NOVNC_STATE", str(Path.home() / ".urirun-novnc" / "session.json")))
SHOT_DIR = Path(os.environ.get("URIRUN_NOVNC_SHOTS", str(Path.home() / ".urirun-novnc" / "shots")))


def _run(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def _state() -> dict:
    if not STATE.exists():
        raise RuntimeError("no desktop session — call desktop://novnc/session/command/start first")
    return json.loads(STATE.read_text())


def _exec(cid: str, *cmd: str, display: bool = True, timeout: int = 60) -> subprocess.CompletedProcess:
    env = ["-e", f"DISPLAY={DISPLAY}"] if display else []
    return _run(["docker", "exec", *env, cid, *cmd], timeout=timeout)


@conn.handler("session/command/start", external=True, meta={"label": "Start a noVNC desktop in Docker"})
def start(image: str = IMAGE, port: int = 6080) -> dict[str, Any]:
    """Start a noVNC desktop container and wait until its X display is ready."""
    STATE.parent.mkdir(parents=True, exist_ok=True)
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    run = _run(["docker", "run", "-d", "--rm", "-p", f"{port}:80", "--shm-size=512m", image])
    if run.returncode != 0:
        return urirun.fail(f"docker run failed: {run.stderr.strip()[:200]}")
    cid = run.stdout.strip()
    # wait for the X display, then make sure the control tools exist
    ready = False
    for _ in range(40):
        if _exec(cid, "bash", "-lc", "DISPLAY=:1 xdpyinfo >/dev/null 2>&1").returncode == 0:
            ready = True
            break
        time.sleep(1)
    tools_ok = _exec(cid, "bash", "-lc", "command -v xdotool && command -v scrot", display=False).returncode == 0
    if not tools_ok:
        _exec(cid, "bash", "-lc", "apt-get update -qq && apt-get install -y -qq xdotool scrot xdpyinfo",
              display=False, timeout=180)
        tools_ok = _exec(cid, "bash", "-lc", "command -v xdotool && command -v scrot", display=False).returncode == 0
    STATE.write_text(json.dumps({"cid": cid, "port": port, "image": image}))
    return urirun.ok(containerId=cid[:12], novncUrl=f"http://localhost:{port}/", displayReady=ready, toolsReady=tools_ok)


@conn.handler("app/command/launch", external=True, meta={"label": "Launch an app on the desktop"})
def launch(command: str, settle: float = 2.0) -> dict[str, Any]:
    """Launch a GUI command on the desktop (e.g. ``lxterminal``)."""
    cid = _state()["cid"]
    _exec(cid, "bash", "-lc", f"DISPLAY=:1 nohup {command} >/tmp/launch.log 2>&1 &")
    time.sleep(settle)
    return urirun.ok(launched=command)


@conn.handler("input/command/type", external=True, meta={"label": "Type text into the focused window"})
def type_text(text: str, enter: bool = False) -> dict[str, Any]:
    """Type a string into whatever window has focus; optionally press Enter."""
    cid = _state()["cid"]
    res = _exec(cid, "xdotool", "type", "--delay", "60", text)
    if res.returncode != 0:
        return urirun.fail(f"xdotool type failed: {res.stderr.strip()[:160]}")
    if enter:
        _exec(cid, "xdotool", "key", "Return")
    return urirun.ok(typed=text, enter=enter)


@conn.handler("input/command/key", external=True, meta={"label": "Press a key or chord"})
def key(keys: str) -> dict[str, Any]:
    """Press an xdotool key/chord, e.g. ``Return``, ``ctrl+l``, ``alt+F2``."""
    cid = _state()["cid"]
    res = _exec(cid, "xdotool", "key", keys)
    return urirun.ok(key=keys) if res.returncode == 0 else urirun.fail(res.stderr.strip()[:160])


@conn.handler("screen/query/screenshot", meta={"label": "Capture the desktop screenshot"})
def screenshot(name: str = "shot") -> dict[str, Any]:
    """Grab the current desktop as a PNG; returns the saved path and a base64 thumbnail."""
    cid = _state()["cid"]
    cap = _exec(cid, "bash", "-lc", "DISPLAY=:1 scrot -o /tmp/_shot.png")
    if cap.returncode != 0:
        return urirun.fail(f"scrot failed: {cap.stderr.strip()[:160]}")
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    local = SHOT_DIR / f"{name}.png"
    cp = _run(["docker", "cp", f"{cid}:/tmp/_shot.png", str(local)])
    if cp.returncode != 0 or not local.exists():
        return urirun.fail(f"docker cp failed: {cp.stderr.strip()[:160]}")
    data = local.read_bytes()
    return urirun.ok(path=str(local), bytes=len(data),
                     pngBase64=base64.b64encode(data).decode("ascii"))


@conn.handler("session/command/stop", external=True, meta={"label": "Stop the noVNC desktop"})
def stop() -> dict[str, Any]:
    """Stop and remove the desktop container."""
    try:
        cid = _state()["cid"]
    except RuntimeError:
        return urirun.ok(stopped=False, note="no session")
    _run(["docker", "rm", "-f", cid])
    STATE.unlink(missing_ok=True)
    return urirun.ok(stopped=True, containerId=cid[:12])


def registry():
    """In-process runnable registry for this connector (live handler refs)."""
    return conn.registry()
