#!/usr/bin/env python3
# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Assisted KSeF authorization-token capture via the browser, run ON the Lenovo node.
# YOU log in with Profil Zaufany (interactive — cannot and must not be headless); the script
# drives everything else through urirun-connector-browser-control (CDP): open the Aplikacja
# Podatnika KSeF, wait for login, go to the tokens page, read the freshly generated token
# from the DOM and store it in the OS keyring as a `secret://` REFERENCE (never printed).
#
#   python3 run_token_capture.py            # uses the env config below
#
# Confirm the gov-site specifics against the LIVE page (they change): set
#   KSEF_LOGIN_URL, KSEF_TOKENS_URL, KSEF_LOGIN_MARKER (CSS), KSEF_TOKEN_SELECTOR (CSS).

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import ksef_token as kt

ENV = os.getenv("KSEF_ENV", "test")
# TEST environment of the Aplikacja Podatnika KSeF. VERIFY these against the live site.
LOGIN_URL = os.getenv("KSEF_LOGIN_URL", "https://ksef-test.mf.gov.pl/web/login")
TOKENS_URL = os.getenv("KSEF_TOKENS_URL", "https://ksef-test.mf.gov.pl/web/tokens")
LOGIN_MARKER = os.getenv("KSEF_LOGIN_MARKER", "")          # CSS selector present only when logged in
TOKEN_SELECTOR = os.getenv("KSEF_TOKEN_SELECTOR", "")      # CSS selector of the generated token value
BROWSER = os.getenv("KSEF_BROWSER", "chrome")


def _eval_text(result: dict) -> str:
    """Pull the eval payload out of the browser-control envelope (best effort)."""
    if not isinstance(result, dict):
        return ""
    for key in ("value", "result", "output", "text", "eval"):
        v = result.get(key)
        if isinstance(v, str):
            return v.strip()
        if isinstance(v, dict):
            inner = _eval_text(v)
            if inner:
                return inner
    return ""


def main() -> int:
    try:
        import urirun_connector_browser_control.core as bc
    except Exception as exc:  # noqa: BLE001
        print(f"browser-control connector not importable: {exc}\n"
              f"Run this on the Lenovo node where Chrome + the connector live.")
        return 2

    if not TOKEN_SELECTOR:
        print("Set KSEF_TOKEN_SELECTOR (the CSS selector of the token value on the page).\n"
              "Open the tokens page once, inspect the element, and export it. Aborting safely.")
        return 2

    print(f"[1/6] launching {BROWSER} (visible) at the KSeF {ENV} login…")
    bc.cdp_launch(browser=BROWSER, url=LOGIN_URL, headless=False)

    print("[2/6] >>> ZALOGUJ SIĘ teraz w przeglądarce przez Profil Zaufany (login.gov.pl). <<<")
    input("      Po zalogowaniu wróć tu i naciśnij Enter… ")

    # confirm we are really past the login wall before touching the token page
    check = kt.build_login_check_js(LOGIN_MARKER)
    for attempt in range(10):
        if _eval_text(bc.cdp_eval(expr=check)).lower() == "true":
            break
        time.sleep(1)
    else:
        print("[!] Nie wykryto zalogowania (sprawdź KSEF_LOGIN_MARKER). Przerywam, nic nie zapisałem.")
        return 1

    print("[3/6] przechodzę do strony tokenów…")
    bc.cdp_navigate(url=TOKENS_URL)
    print("[4/6] >>> Wygeneruj nowy token w przeglądarce (Generuj token). <<<")
    input("      Gdy token jest widoczny na ekranie, naciśnij Enter… ")

    print("[5/6] odczytuję token z DOM…")
    token = _eval_text(bc.cdp_eval(expr=kt.build_token_read_js(TOKEN_SELECTOR)))
    if not token:
        print("[!] Nie odczytałem tokenu (sprawdź KSEF_TOKEN_SELECTOR). Nic nie zapisałem.")
        return 1

    print("[6/6] zapisuję bezpiecznie (keyring/dotenv)…")
    stored = kt.store_token(token, service="ksef", env=ENV)
    if not stored.get("ok"):
        print(f"[!] zapis nieudany: {stored.get('error')}")
        return 1

    print("\n✓ Token zapisany — wartość NIE jest pokazywana, tylko referencja:")
    print(f"   backend : {stored['backend']}")
    print(f"   ref     : {stored['ref']}")
    print(f"   podgląd : {stored['masked']}")
    if stored.get("warning"):
        print(f"   uwaga   : {stored['warning']}")
    print("\nUżyj w ksef:// (token rozwiązywany dopiero przy --execute, deny-by-default):")
    print(f"   --secret-allow '{stored['ref']}'")
    print("Następnie: handshake ksef-token → accessToken (ksef://%s/auth/...)." % ENV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
