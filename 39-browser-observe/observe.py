#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# READ-ONLY autonomous browser observation. Captures the node's real screen (gillm
# portal capture as a URI), analyses it with a vision LLM, and reports what's on it
# (e.g. "LinkedIn is open and logged in; the feed shows …"). It NEVER publishes, sends
# a message, comments, likes, follows, logs in, or pays — a hard gate refuses any write
# URI, so the loop stays observation-only no matter what a plan asks for.
#
#   NODE_URL=http://192.168.188.201:8766 LLM_MODEL=...(vision) python3 observe.py
#   urirun host ask laptop "what is on the screen" --env-file ../.env   # the LLM path

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "urirun" / "adapters" / "python"))

from urirun.node import mesh
from urirun.node.client import NodeClient


def _load_env(path: Path) -> None:
    """Tiny KEY=VALUE loader for example .env files; existing env wins."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_env(HERE.parent / ".env")
_load_env(HERE / ".env")

NODE = os.environ.get("NODE_URL", "http://192.168.188.201:8766")
NODE_NAME = os.environ.get("NODE", "laptop")
MODEL = os.environ.get("LLM_MODEL") or os.environ.get("URIRUN_LLM_MODEL")
IDENTITY = os.path.expanduser(os.environ.get("IDENTITY", "~/.ssh/id_ed25519"))

# Hard read-only gate: any URI matching these is refused, so observation can never turn
# into a social write / login / payment — regardless of what a goal or a plan requests.
REFUSED = ("/command/", "publish", "post/command", "form/command/submit", "message", "/send",
           "dm", "comment", "like", "follow", "connect/command", "login", "signin", "password",
           "input/command", "click", "type", "pay", "buy", "checkout")


def assert_read_only(uri: str) -> None:
    low = uri.lower()
    if any(p in low for p in REFUSED):
        raise PermissionError(f"refused: '{uri}' is a write/social/login action — observe.py is read-only")


def run_ro(client: NodeClient, uri: str, payload: dict | None = None) -> dict:
    assert_read_only(uri)                       # the gate, on every call
    return client.run(uri, payload, timeout=60)


def ensure_capture(client: NodeClient) -> str:
    """Self-manage the capture capability: if no screen:// route is served, deploy the
    gillm portal-capture handler (signed)."""
    routes = [r.get("uri", "") for r in client.routes()]
    for uri in routes:
        if uri.endswith("/screen/query/capture") and uri.startswith("kvm://"):
            return uri
    for uri in routes:
        if uri.endswith("/portal/query/capture") and uri.startswith("screen://"):
            return uri
    sys.path.insert(0, str(HERE))
    import gillm_capture
    res = mesh.deploy_to_node(client.base, bindings=gillm_capture.urirun_bindings(),
                              code={"gillm_capture.py": (HERE / "gillm_capture.py").read_text()},
                              allow=["screen://**"], merge=True, identity=IDENTITY)
    if not res.get("ok"):
        raise RuntimeError(f"could not provision capture: {res}")
    return f"screen://{NODE_NAME}/portal/query/capture"


def observe(client: NodeClient) -> dict:
    capture_uri = ensure_capture(client)
    env = run_ro(client, capture_uri, {"base64": True})
    data = (env.get("result") or {}).get("value") or {}
    if not data.get("ok"):
        return {"ok": False, "error": data.get("error", "capture failed")}
    encoded = data.get("base64") or data.get("pngBase64")
    if not encoded:
        return {"ok": False, "error": "capture returned no base64 image payload"}
    shot = "data:image/png;base64," + encoded
    if not MODEL:
        return {"ok": True, "captured_bytes": data["bytes"], "note": "set LLM_MODEL (vision) to analyse the image"}
    from urirun_connector_llm.core import complete
    out = complete(model=MODEL, image=shot,
                   prompt=("You are a READ-ONLY screen observer. Describe what application is open and, if it is a "
                           "website, which one and whether it looks logged in. Summarise the visible content in 2-3 "
                           "sentences. Do NOT propose posting, messaging, clicking, or any action. What is on this screen?"))
    return {"ok": True, "captured_bytes": data["bytes"], "observation": out.get("response") or out.get("content")}


if __name__ == "__main__":
    result = observe(NodeClient(NODE))
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
