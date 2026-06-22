# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# A self-contained, multi-scheme node surface pushed to a remote urirun node via
# POST /deploy. One file, only stdlib + a local Chrome (already on the node) —
# so it deploys cleanly where pip-installing the real connector packages is not
# possible. It re-implements the pure capabilities of several connectors
# (browser-control / base64 / hash / uuid / http-check / mcp-filesystem) plus a
# small office/sys surface, giving the node REAL browser control and tools.
#
# Connectors that need external services or native packages (mqtt broker, ksef /
# namecheap APIs, email creds, kvm device, llm key) or the tellmesh desktop packs
# are NOT reimplemented here — those need their package installed on the node
# (the bridge pattern, see examples/31-llm-remote-office).

from __future__ import annotations

import base64
import hashlib
import os
import platform
import re
import shutil
import socket
import subprocess
import time
import urllib.request
import uuid as _uuid
from pathlib import Path

import urirun

WS = Path.home() / ".urirun-node" / "ws"          # sandbox for files/screenshots/notes
NOTES = Path.home() / ".urirun-node" / "office-notes.txt"


def _chrome() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _safe(path: str) -> Path:
    p = (WS / path).resolve()
    WS.mkdir(parents=True, exist_ok=True)
    if not str(p).startswith(str(WS.resolve())):
        raise ValueError("path escapes the workspace")
    return p


# --- browser:// (real, via headless Chrome) --------------------------------
browser = urirun.connector("lenovo-browser", scheme="browser", target="laptop")


@browser.handler("page/query/text", isolated=False, meta={"label": "Read page text via headless Chrome"})
def page_text(url: str = "", max: int = 600) -> dict:
    chrome = _chrome()
    if not chrome:
        return urirun.fail("no Chrome/Chromium on the node")
    try:
        out = subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--dump-dom", url],
                             capture_output=True, text=True, timeout=45)
    except (OSError, subprocess.SubprocessError) as exc:
        return urirun.fail(str(exc))
    html = out.stdout or ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return urirun.ok(url=url, bytes=len(html), text=" ".join(text.split())[:int(max)])


@browser.handler("page/query/screenshot", isolated=False, meta={"label": "Screenshot a page (headless Chrome)"})
def page_screenshot(url: str = "", width: int = 1280) -> dict:
    chrome = _chrome()
    if not chrome:
        return urirun.fail("no Chrome/Chromium on the node")
    shot = _safe(f"shot-{int(time.time())}.png")
    try:
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                        f"--window-size={int(width)},900", f"--screenshot={shot}", url],
                       capture_output=True, timeout=45)
    except (OSError, subprocess.SubprocessError) as exc:
        return urirun.fail(str(exc))
    if not shot.exists():
        return urirun.fail("no screenshot produced")
    return urirun.ok(url=url, screenshot=str(shot), bytes=shot.stat().st_size)


@browser.handler("desktop/page/command/open", isolated=False, meta={"label": "Open a URL in a real browser window"})
def desktop_open(url: str = "") -> dict:
    chrome = _chrome()
    if not chrome:
        return urirun.fail("no Chrome/Chromium on the node")
    subprocess.Popen([chrome, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return urirun.ok(opened=url, browser=os.path.basename(chrome))


# --- sys:// ----------------------------------------------------------------
sysc = urirun.connector("lenovo-sys", scheme="sys", target="laptop")


@sysc.handler("host/query/info", isolated=False, meta={"label": "Host info"})
def host_info() -> dict:
    return urirun.ok(hostname=socket.gethostname(), platform=platform.platform(),
                     python=platform.python_version(), cpus=os.cpu_count())


@sysc.handler("disk/query/usage", isolated=False, meta={"label": "Disk usage"})
def disk_usage() -> dict:
    u = shutil.disk_usage("/")
    return urirun.ok(total_gb=round(u.total / 1e9, 1), free_gb=round(u.free / 1e9, 1),
                     used_pct=round(100 * u.used / u.total, 1))


# --- fs:// (sandboxed under ~/.urirun-node/ws) -----------------------------
fsc = urirun.connector("lenovo-fs", scheme="fs", target="laptop")


@fsc.handler("file/command/write", isolated=False, meta={"label": "Write a file (sandboxed)"})
def fs_write(path: str = "", content: str = "") -> dict:
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return urirun.ok(wrote=str(p), bytes=len(content))


@fsc.handler("file/query/read", isolated=False, meta={"label": "Read a file (sandboxed)"})
def fs_read(path: str = "") -> dict:
    p = _safe(path)
    return urirun.ok(path=str(p), content=p.read_text(encoding="utf-8")) if p.exists() else urirun.fail("no such file")


@fsc.handler("dir/query/list", isolated=False, meta={"label": "List the workspace"})
def fs_list() -> dict:
    WS.mkdir(parents=True, exist_ok=True)
    return urirun.ok(dir=str(WS), files=sorted(os.listdir(WS)))


# --- codec:// / hash:// / uuid:// (stdlib re-implementations) ---------------
codec = urirun.connector("lenovo-codec", scheme="codec", target="laptop")


@codec.handler("text/query/base64", isolated=False, meta={"label": "base64 encode/decode"})
def b64(text: str = "", mode: str = "encode") -> dict:
    if mode == "decode":
        return urirun.ok(mode=mode, result=base64.b64decode(text.encode()).decode("utf-8", "replace"))
    return urirun.ok(mode=mode, result=base64.b64encode(text.encode()).decode())


hashc = urirun.connector("lenovo-hash", scheme="hash", target="laptop")


@hashc.handler("text/query/sha256", isolated=False, meta={"label": "sha256 of text"})
def sha256(text: str = "") -> dict:
    return urirun.ok(sha256=hashlib.sha256(text.encode()).hexdigest())


uuidc = urirun.connector("lenovo-uuid", scheme="uuid", target="laptop")


@uuidc.handler("id/query/v4", isolated=False, meta={"label": "Generate UUIDv4"})
def uuid_v4(count: int = 1) -> dict:
    return urirun.ok(ids=[str(_uuid.uuid4()) for _ in range(max(1, min(int(count), 50)))])


# --- httpcheck:// ----------------------------------------------------------
httpc = urirun.connector("lenovo-httpcheck", scheme="httpcheck", target="laptop")


@httpc.handler("url/query/status", isolated=False, meta={"label": "HTTP status of a URL"})
def http_status(url: str = "") -> dict:
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ifuri-lenovo/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return urirun.ok(url=url, status=int(resp.status), final=resp.geturl())
    except urllib.error.HTTPError as exc:
        return urirun.ok(url=url, status=int(exc.code))
    except Exception as exc:  # noqa: BLE001
        return urirun.fail(str(exc), url=url)


# --- office:// notes -------------------------------------------------------
office = urirun.connector("lenovo-office", scheme="office", target="laptop")


@office.handler("note/command/write", isolated=False, meta={"label": "Append a note on the node"})
def note_write(text: str = "") -> dict:
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTES, "a", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {text}".rstrip() + "\n")
    return urirun.ok(wrote=text)


@office.handler("note/query/read", isolated=False, meta={"label": "Read the notes back"})
def note_read() -> dict:
    txt = NOTES.read_text(encoding="utf-8") if NOTES.exists() else ""
    return urirun.ok(notes=txt.strip(), lines=txt.count("\n"))


# --- the deployable binding document ---------------------------------------
_CONNECTORS = (browser, sysc, fsc, codec, hashc, uuidc, httpc, office)


def urirun_bindings() -> dict:
    b: dict = {}
    for c in _CONNECTORS:
        b.update(c.bindings()["bindings"])
    return {"version": "urirun.bindings.v2", "bindings": b}


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "bindings":
        print(json.dumps(urirun_bindings()))
