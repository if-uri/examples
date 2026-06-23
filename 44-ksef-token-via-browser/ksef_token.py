# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Helper for capturing a KSeF authorization token from the browser (Aplikacja Podatnika
# KSeF) and storing it SECURELY — never echoed, never written into a flow/binding. The
# browser parts run via urirun-connector-browser-control (CDP); these functions are the
# testable, security-critical glue: the JS snippets to read state, token masking, and the
# keyring store that yields a `secret://` REFERENCE (the value stays in the OS store).

from __future__ import annotations

import os
from typing import Any


def mask(token: str) -> str:
    """A safe-to-log preview: first 3 + last 2 chars, the middle hidden."""
    t = (token or "").strip()
    if len(t) <= 6:
        return "*" * len(t)
    return f"{t[:3]}{'*' * (len(t) - 5)}{t[-2:]}"


def build_login_check_js(marker: str = "") -> str:
    """JS (for browser://cdp/page/query/eval) that returns 'true' once the user has logged
    in. `marker` is a CSS selector that only exists on the authenticated KSeF page (e.g. a
    logout button / NIP context badge). Defaults to 'not on the login page'."""
    if marker:
        sel = marker.replace("'", "\\'")
        return f"(!!document.querySelector('{sel}')).toString()"
    return "(!location.href.toLowerCase().includes('login')).toString()"


def build_token_read_js(selector: str) -> str:
    """JS that reads the freshly generated token text from the DOM (it is shown once).
    `selector` targets the element holding the token value."""
    sel = (selector or "").replace("'", "\\'")
    return ("(function(){var e=document.querySelector('" + sel + "');"
            "return e?(e.value||e.innerText||e.textContent||'').trim():'';})()")


def store_token(token: str, *, service: str = "ksef", account: str = "", env: str = "test",
                dotenv_path: str = "") -> dict[str, Any]:
    """Store the captured token by VALUE in the OS keyring and return only a REFERENCE
    (`secret://keyring/<service>/<account>`) plus a masked preview — the raw token is never
    in the result. Falls back to a chmod-600 dotenv (`secret://dotenv/<path>#NAME`) when the
    `keyring` library is unavailable. The connectors then resolve the value only at execute
    time, behind the deny-by-default secret policy."""
    token = (token or "").strip()
    if not token:
        return {"ok": False, "error": "empty token"}
    account = account or f"{env}-token"
    try:
        import keyring  # type: ignore
        keyring.set_password(service, account, token)
        return {"ok": True, "backend": "keyring", "ref": f"secret://keyring/{service}/{account}",
                "masked": mask(token), "secretAllow": f"secret://keyring/{service}/{account}"}
    except Exception:  # noqa: BLE001 - keyring missing/locked → dotenv fallback
        pass
    path = os.path.expanduser(dotenv_path or f"~/.urirun/ksef/{env}.env")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    name = f"KSEF_TOKEN_{env.upper()}"
    # write the single line atomically with 0600 perms so the value isn't world-readable
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"{name}={token}\n")
    return {"ok": True, "backend": "dotenv", "ref": f"secret://dotenv/{path}#{name}",
            "masked": mask(token), "path": path,
            "warning": "keyring unavailable — stored in a 0600 dotenv; prefer `pip install keyring`"}
