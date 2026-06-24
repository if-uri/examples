# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Self-contained, NARROW CDP surface pushed to a urirun node via POST /deploy.
# stdlib + a local google-chrome only. Unlike a generic eval endpoint, every
# handler is a fixed, purpose-built action — the only caller inputs are a post's
# text and a dry_run flag, never arbitrary JavaScript. Drives a real, logged-in
# Chrome profile over a debug port so a flow can compose a LinkedIn post inside an
# already-authenticated session. Deployed under browser://laptop/cdp/**.

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import time
import urllib.parse
import urllib.request

import urirun

cdp = urirun.connector("lenovo-cdp", scheme="browser", target="laptop")

_PORT = int(os.environ.get("CDP_PORT", "9222"))
_PROFILE = os.environ.get("CDP_PROFILE") or os.path.join(os.path.expanduser("~"), ".config", "google-chrome")
_FEED = "https://www.linkedin.com/feed/"


def _chrome() -> str | None:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        path = shutil.which(name)
        if path:
            return path
    return None


def _http(path: str, timeout: float = 5.0):
    req = urllib.request.Request(f"http://127.0.0.1:{_PORT}{path}")
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read() or "{}")


def _pages() -> list[dict]:
    try:
        return [t for t in _http("/json") if t.get("type") == "page"]
    except Exception:
        return []


def _ws(ws_url: str, messages: list[dict]) -> list[dict]:
    u = urllib.parse.urlparse(ws_url)
    s = socket.create_connection((u.hostname, u.port), timeout=8)
    s.sendall((f"GET {u.path} HTTP/1.1\r\nHost: {u.hostname}:{u.port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {base64.b64encode(os.urandom(16)).decode()}\r\n"
               f"Sec-WebSocket-Version: 13\r\n\r\n").encode())
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += s.recv(4096)

    def send(text: str) -> None:
        p = text.encode()
        mask, h, n = os.urandom(4), bytearray([0x81]), len(p)
        if n < 126:
            h.append(0x80 | n)
        elif n < 65536:
            h.append(0x80 | 126); h += struct.pack(">H", n)
        else:
            h.append(0x80 | 127); h += struct.pack(">Q", n)
        h += mask
        s.sendall(bytes(h) + bytes(b ^ mask[i % 4] for i, b in enumerate(p)))

    def rd(n: int):
        b = b""
        while len(b) < n:
            c = s.recv(n - len(b))
            if not c:
                return None
            b += c
        return b

    def recv():
        h = rd(2)
        if not h:
            return None
        ln = h[1] & 0x7f
        if ln == 126:
            ln = struct.unpack(">H", rd(2))[0]
        elif ln == 127:
            ln = struct.unpack(">Q", rd(8))[0]
        return (rd(ln) or b"").decode("utf-8", "replace")

    out = []
    for msg in messages:
        send(json.dumps(msg))
        while True:
            data = recv()
            if data is None:
                break
            obj = json.loads(data)
            if obj.get("id") == msg["id"]:
                out.append(obj)
                break
    s.close()
    return out


def _eval(expr: str, *, await_promise: bool = True):
    """INTERNAL ONLY — runs a FIXED, module-defined expression. Never exposed as a
    route and never takes a caller-supplied script (no arbitrary RCE surface)."""
    pages = _pages()
    if not pages:
        return {"_error": "no running debug session"}
    res = _ws(pages[0]["webSocketDebuggerUrl"],
              [{"id": 1, "method": "Runtime.evaluate",
                "params": {"expression": expr, "returnByValue": True, "awaitPromise": await_promise}}])
    r = (res[0].get("result") if res else None) or {}
    if r.get("exceptionDetails"):
        return {"_error": str(r.get("exceptionDetails"))[:300]}
    return r.get("result", {}).get("value")


# JS that drives LinkedIn's composer. text is injected as a JSON string literal
# (json.dumps), so the caller input is data, not executable script.
_POST_JS = """(async (text, submit) => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const vis = el => el && el.offsetParent !== null;
  const findBtn = res => [...document.querySelectorAll('button,[role=button]')]
      .find(b => vis(b) && res.test((b.getAttribute('aria-label')||'') + ' ' + (b.innerText||'')));
  let trigger = document.querySelector('.share-box-feed-entry__trigger') || findBtn(/start a post|utw[oó]rz post|napisz post/i);
  if (!trigger) return {step:'trigger', ok:false, reason:'no start-a-post button (logged in?)'};
  trigger.click(); await sleep(2500);
  const ed = document.querySelector('div.ql-editor[contenteditable="true"], div[role="textbox"][contenteditable="true"]');
  if (!ed) return {step:'editor', ok:false, reason:'composer editor not found'};
  ed.focus();
  document.execCommand && document.execCommand('insertText', false, text);
  if (!ed.innerText.trim()) { ed.textContent = text; ed.dispatchEvent(new InputEvent('input', {bubbles:true})); }
  await sleep(800);
  const typed = ed.innerText.trim();
  const postBtn = findBtn(/^post$|^opublikuj$/i) ||
      document.querySelector('.share-actions__primary-action, button.share-box_actions__primary-action');
  const ready = !!(postBtn && !postBtn.disabled);
  if (!submit) return {step:'composed', ok:true, typed, postButton:ready, submitted:false};
  if (!ready) return {step:'submit', ok:false, typed, reason:'post button missing/disabled'};
  postBtn.click(); await sleep(2500);
  return {step:'submit', ok:true, typed, submitted:true};
})""".strip()


@cdp.handler("cdp/session/command/launch", isolated=True, meta={"label": "Launch Chrome with a debug port on the real profile"})
def cdp_launch(headless: bool = True, profile: str = "") -> dict:
    chrome = _chrome()
    if not chrome:
        return urirun.fail("no Chrome on the node")
    if _pages():
        return urirun.ok(reused=True, debugPort=_PORT, pages=len(_pages()))
    args = [chrome, f"--remote-debugging-port={_PORT}", "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={profile or _PROFILE}", "--no-first-run", "--no-default-browser-check"]
    if headless:
        args += ["--headless=new", "--disable-gpu"]
    proc = subprocess.Popen([*args, "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(48):
        try:
            ver = _http("/json/version")
            return urirun.ok(pid=proc.pid, debugPort=_PORT, browser=ver.get("Browser"),
                             profile=profile or _PROFILE, headless=headless)
        except Exception:
            time.sleep(0.25)
    return urirun.fail("debugger did not come up", pid=proc.pid)


@cdp.handler("cdp/session/query/find", isolated=True, meta={"label": "Report whether the running session is logged into a domain (read-only)"})
def cdp_find(domain: str = "linkedin.com", cookie_names: str = "li_at") -> dict:
    pages = _pages()
    if not pages:
        return urirun.fail("no running debug session (launch first)")
    url = f"https://www.{domain.strip().lstrip('www.').rstrip('/')}/"
    wanted = [c.strip() for c in cookie_names.split(",") if c.strip()] or ["li_at"]
    res = _ws(pages[0]["webSocketDebuggerUrl"],
              [{"id": 1, "method": "Network.getCookies", "params": {"urls": [url]}}])
    cookies = ((res[0].get("result") if res else None) or {}).get("cookies") or []
    present = sorted({c.get("name") for c in cookies if c.get("name") in wanted})
    return urirun.ok(domain=domain, loggedIn=bool(present), sessionCookies=present, cookieCount=len(cookies))


@cdp.handler("cdp/page/query/state", isolated=True, meta={"label": "Current tab url + title (read-only)"})
def cdp_state() -> dict:
    val = _eval("({u:location.href,t:document.title})")
    if isinstance(val, dict) and val.get("_error"):
        return urirun.fail(val["_error"])
    return urirun.ok(url=(val or {}).get("u"), title=(val or {}).get("t"))


@cdp.handler("cdp/linkedin/command/post", isolated=True, meta={"label": "Compose (and optionally submit) a LinkedIn post — fixed automation"})
def cdp_linkedin_post(text: str = "", dry_run: bool = True) -> dict:
    if not text.strip():
        return urirun.fail("empty post text")
    pages = _pages()
    if not pages:
        return urirun.fail("no running debug session (launch first)")
    ws = pages[0]["webSocketDebuggerUrl"]
    _ws(ws, [{"id": 1, "method": "Page.enable"},
             {"id": 2, "method": "Page.navigate", "params": {"url": _FEED}}])
    time.sleep(5.0)
    expr = f"{_POST_JS}({json.dumps(text)}, {str(not dry_run).lower()})"
    val = _eval(expr)
    if isinstance(val, dict) and val.get("_error"):
        return urirun.fail("composer automation error", detail=val["_error"])
    result = val if isinstance(val, dict) else {"raw": val}
    return urirun.ok(dryRun=dry_run, **result)


def urirun_bindings() -> dict:
    return cdp.bindings()


if __name__ == "__main__":
    print(json.dumps(urirun_bindings()))
