#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# LinkedIn Compose → Fill → Verify → Publish via CDP DOM (focus-independent).
#
# Proves the step that the nav+verify green run (example 36) did NOT cover:
#   1. cdp/page/command/fill into the contenteditable composer (no focus/Wayland)
#   2. Hard verification via cdp/page/query/eval BEFORE clicking Publish
#   3. Conditional cdp/page/command/click "Opublikuj"/"Post" only when text is confirmed
#
# Precondition: Chrome with --remote-debugging-port=9222 is running, linkedin.com is open.
# If not, the first step (ensure) launches a dedicated session.
#
#   DRY RUN (plan only, no publish):
#       python run.py "napisz post na LinkedIn: Testujemy CDP" --node-url http://127.0.0.1:8766 --name laptop
#
#   EXECUTE:
#       python run.py "napisz post na LinkedIn: Testujemy CDP" \
#           --node-url http://127.0.0.1:8766 --name laptop --execute
#
#   PUBLISH (add --publish flag — clicks "Opublikuj"/"Post"):
#       python run.py "..." --node-url http://127.0.0.1:8766 --name laptop --execute --publish
#
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Environment: examples/.env (LLM_MODEL + OPENROUTER_API_KEY) — used only for NL->text.
# The flow itself does NOT need the LLM — it drives pure CDP DOM.

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "urirun" / "adapters" / "python"))

SCHEME = os.environ.get("LINKEDIN_CDP_SCHEME", "browser")

from urirun.node.mesh import _maybe_load_dotenv  # noqa: E402


# ─── LinkedIn DOM selectors (role-based — OCR-immune, language-agnostic) ─────
#
# The composer opens as a modal with a contenteditable div[role=textbox].
# We target by role+aria-label because the visible text "What's on your mind?"
# is locale-specific; role=textbox is stable.
COMPOSER_OPENER_TEXT = "Start a post"   # aria-label on the teaser button (EN)
COMPOSER_OPENER_ROLE = "button"
COMPOSER_FIELD_ROLE  = "textbox"
PUBLISH_BUTTON_TEXT  = "Post"           # EN; try "Opublikuj" fallback on PL locale
PUBLISH_BUTTON_ROLE  = "button"
LINKEDIN_URL         = "https://www.linkedin.com/feed/"

# JS snippet that reads the current text content of the first visible textbox.
# Used for the hard verification gate — returns the actual text as a string.
VERIFY_JS = (
    "(function(){"
    "  const el=document.querySelector('[role=textbox][contenteditable]')"
    "         || document.querySelector('textarea[aria-label]');"
    "  return el ? (el.innerText||el.value||'').trim() : null;"
    "})()"
)


_URIRUN = str(ROOT / "urirun" / "venv" / "bin" / "urirun")


def _step(node_url: str, node_name: str, uri_path: str, payload: dict[str, Any], timeout: float = 30) -> dict[str, Any]:
    """Call a single URI step on the node via `urirun host run`."""
    uri = f"{SCHEME}://{node_name}/{uri_path}"
    cmd = [_URIRUN, "host", "run", node_url, uri,
           "--payload", json.dumps(payload), "--timeout", str(int(timeout))]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"\{.*\}", proc.stdout, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return {"ok": False, "raw": (proc.stdout + proc.stderr)[:300]}


def _ok(result: dict) -> bool:
    return bool(result.get("ok"))


def run_flow(node_url: str, node_name: str, text: str, *, execute: bool, publish: bool, verbose: bool) -> None:
    steps = []

    def do(label: str, uri_path: str, payload: dict, *, skip_on_dry: bool = True) -> dict:
        entry = {"label": label, "uri": f"{SCHEME}://{node_name}/{uri_path}", "payload": payload}
        if not execute:
            if verbose:
                print(f"  [DRY] {label}  →  {SCHEME}://{node_name}/{uri_path}  {json.dumps(payload)}")
            steps.append({**entry, "ok": None, "dry": True})
            return {"ok": True, "dry": True}
        t0 = time.monotonic()
        result = _step(node_url, node_name, uri_path, payload)
        elapsed = time.monotonic() - t0
        ok = _ok(result)
        steps.append({**entry, "ok": ok, "result": result, "elapsed_ms": int(elapsed * 1000)})
        marker = "✓" if ok else "✗"
        print(f"  {marker} [{int(elapsed*1000):4d}ms] {label}")
        if verbose or not ok:
            print(f"           {json.dumps(result)}")
        return result

    print(f"\n{'[DRY RUN] ' if not execute else ''}LinkedIn Compose via CDP DOM")
    print(f"  node  : {node_url}")
    print(f"  name  : {node_name}")
    print(f"  text  : {text!r}")
    print(f"  publish: {publish}")
    print()

    # 1. Launch a CDP browser session directly on the target page.
    # The live browser-control registry exposes launch/find, not ensure/ready.
    r = do("launch CDP browser on LinkedIn", "cdp/session/command/launch",
           {"browser": "chrome", "url": LINKEDIN_URL, "headless": False})
    if execute and not _ok(r):
        _fail("CDP browser could not be launched", r, steps)
        return

    # 2. Open LinkedIn before any compose actions.
    # The CDP session may start on about:blank or a non-LinkedIn tab, so we
    # explicitly navigate to the target page instead of depending on ambient state.
    r = do("navigate to LinkedIn", "cdp/page/command/navigate", {"url": LINKEDIN_URL})
    if execute and not _ok(r):
        _fail("Could not navigate to LinkedIn", r, steps)
        return

    # 3. Verify we are on LinkedIn (safety check — do NOT publish to wrong page)
    r = do("verify LinkedIn is open", "cdp/page/query/eval",
           {"expr": "document.location.hostname.includes('linkedin.com')"})
    if execute:
        if not _ok(r):
            _fail("page/query/eval failed", r, steps)
            return
        if r.get("value") is not True:
            _fail("Not on linkedin.com after navigation", r, steps)
            return

    # 4. Click the "Start a post" / "Opublikuj" teaser (opens composer modal)
    r = do("click composer opener",
           "cdp/page/command/click",
           {"text": COMPOSER_OPENER_TEXT, "role": COMPOSER_OPENER_ROLE})
    if execute and not _ok(r):
        # Try PL locale fallback
        r2 = do("click composer opener (PL: Napisz post)",
                "cdp/page/command/click",
                {"text": "Napisz post", "role": "button"})
        if not _ok(r2):
            _fail("Could not open composer (tried EN + PL locale)", r2, steps)
            return

    # 5. Wait for composer modal to appear (the textbox enters DOM after the modal opens)
    r = do("wait for composer textbox", "cdp/page/query/eval",
           {"expr": "!!document.querySelector('[role=textbox][contenteditable]')"})
    if execute:
        # Poll up to 4s in 0.5s ticks
        for _ in range(8):
            if r.get("value") is True:
                break
            time.sleep(0.5)
            r = _step(node_url, node_name, "cdp/page/query/eval",
                      {"expr": "!!document.querySelector('[role=textbox][contenteditable]')"})
        if r.get("value") is not True:
            _fail("Composer textbox did not appear in DOM after 4s", r, steps)
            return

    # 6. Fill the composer with the text (contenteditable path: execCommand+InputEvent)
    r = do("fill composer",
           "cdp/page/command/fill",
           {"role": COMPOSER_FIELD_ROLE, "value": text})
    if execute and not _ok(r):
        _fail("fill failed — element not found or CDP error", r, steps)
        return

    # 7. HARD VERIFICATION GATE: read back the actual text from the DOM
    #    This is the gate that prevents a misfire: we only proceed to Publish if
    #    the text we see in the DOM contains what we intended to write.
    r = do("verify text landed in composer", "cdp/page/query/eval", {"expr": VERIFY_JS})
    if execute:
        if not _ok(r):
            _fail("verify eval failed", r, steps)
            return
        actual = str(r.get("value") or "").strip()
        if text.strip() not in actual:
            _fail(
                f"Text did NOT land in composer — expected {text!r}, got {actual!r}. "
                "Aborting before publish.",
                r, steps,
            )
            return
        print(f"           verified: {actual!r}")

    # 8. Conditional publish — only if --publish flag was given
    if publish:
        r = do("click Publish (Post)",
               "cdp/page/command/click",
               {"text": PUBLISH_BUTTON_TEXT, "role": PUBLISH_BUTTON_ROLE})
        if execute and not _ok(r):
            # PL locale fallback
            r2 = do("click Publish (PL: Opublikuj)",
                    "cdp/page/command/click",
                    {"text": "Opublikuj", "role": "button"})
            if not _ok(r2):
                _fail("Publish button not found (tried EN + PL locale)", r2, steps)
                return

        # 9. Post-publish verify: wait for the composer modal to close
        #    (LinkedIn removes the modal from DOM after successful publish)
        r = do("verify composer closed (post published)",
               "cdp/page/query/eval",
               {"expr": "!document.querySelector('[role=dialog][aria-label*=post]')"
                " && !document.querySelector('[role=dialog][aria-label*=Post]')"})
        if execute:
            for _ in range(10):
                if r.get("value") is True:
                    break
                time.sleep(0.5)
                r = _step(node_url, node_name, "cdp/page/query/eval",
                          {"expr": "!document.querySelector('[role=dialog]')"})
            if r.get("value") is not True:
                print("  ⚠  Composer still open — post may have failed or requires confirmation")
            else:
                print("  ✓  Composer closed — post published")
    else:
        print("\n  ↳ Skipping publish (no --publish flag). Text is in composer, ready to review.")

    _summary(steps, execute)


def _fail(reason: str, result: dict, steps: list) -> None:
    print(f"\n  ✗ ABORTED: {reason}")
    if result:
        print(f"    {json.dumps(result)}")
    _summary(steps, execute=True)
    sys.exit(1)


def _summary(steps: list, execute: bool) -> None:
    print()
    if not execute:
        print(f"  [DRY RUN] {len(steps)} steps planned — add --execute to run")
        return
    ok_n = sum(1 for s in steps if s.get("ok") is True)
    fail_n = sum(1 for s in steps if s.get("ok") is False)
    total = len(steps)
    print(f"  {'ok' if fail_n == 0 else 'FAILED'}: {ok_n}/{total} steps OK, {fail_n} failed")


def main() -> None:
    _maybe_load_dotenv(str(ROOT / "examples" / ".env"))
    p = argparse.ArgumentParser(description="LinkedIn Compose via CDP DOM")
    p.add_argument("text", help="Text to write in the LinkedIn composer")
    p.add_argument("--node-url", default="http://127.0.0.1:8766", help="urirun node base URL")
    p.add_argument("--name", default="laptop", help="service name used in browser:// URIs")
    p.add_argument("--execute", action="store_true", help="Actually execute (default: dry run)")
    p.add_argument("--publish", action="store_true", help="Click Publish after fill+verify")
    p.add_argument("--verbose", "-v", action="store_true", help="Print full result dicts")
    args = p.parse_args()
    run_flow(args.node_url, args.name, args.text, execute=args.execute, publish=args.publish, verbose=args.verbose)


if __name__ == "__main__":
    main()
