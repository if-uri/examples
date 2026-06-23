# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Last link of the chain: take the KSeF authorization token captured into the keyring and run
# the ksef-token handshake (token -> accessToken), then store the accessToken back into the
# keyring as a reference. Plan/dry-run by default (needs no secrets); a real run needs the MF
# public key + execute=True. Neither the token nor the accessToken is ever returned in clear.

from __future__ import annotations

import os
from typing import Any

import ksef_token as kt


def resolve_token(service: str = "ksef", account: str = "", env: str = "test",
                  dotenv_path: str = "") -> str:
    """Read the stored KSeF token VALUE (keyring first, then the 0600 dotenv fallback). Used
    only to feed the handshake — callers must never print the return value."""
    account = account or f"{env}-token"
    try:
        import keyring  # type: ignore
        val = keyring.get_password(service, account)
        if val:
            return val.strip()
    except Exception:  # noqa: BLE001
        pass
    path = os.path.expanduser(dotenv_path or f"~/.urirun/ksef/{env}.env")
    name = f"KSEF_TOKEN_{env.upper()}"
    try:
        for line in open(path, encoding="utf-8"):
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def authenticate_and_store(env: str, nip: str, *, public_key: str = "", execute: bool = False,
                           service: str = "ksef", method: str = "token") -> dict[str, Any]:
    """Run (or plan) the KSeF auth handshake using the keyring-stored token. On a real execute
    that returns an accessToken, store it under `secret://keyring/<service>/<env>-access` and
    return only the reference + masked preview. Plan mode returns the step list, no secrets."""
    try:
        import urirun_connector_ksef.core as ksef
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"ksef connector not importable: {exc}"}

    token = resolve_token(service=service, env=env) if execute else ""
    if execute and not token:
        return {"ok": False, "error": f"no stored token (run run_token_capture.py first); "
                                      f"expected secret://keyring/{service}/{env}-token"}
    if execute and not public_key:
        return {"ok": False, "error": "real authentication needs the MF public_key (env public-key endpoint)"}

    result = ksef.authenticate(env, nip, token=token, public_key=public_key,
                               execute=execute, method=method)
    if not execute:
        # plan/dry-run: surface the steps, nothing secret involved
        return {"ok": bool(result.get("ok")), "dryRun": True, "env": env,
                "steps": result.get("steps", []), "note": result.get("note", "")}

    if not result.get("ok"):
        return {"ok": False, "env": env, "error": result.get("error", "authentication failed")}
    access = (result.get("accessToken") or result.get("access_token") or "")
    if not access:
        return {"ok": False, "env": env, "error": "no accessToken in KSeF response"}
    stored = kt.store_token(access, service=service, account=f"{env}-access", env=env)
    return {"ok": True, "env": env, "authenticated": True,
            "accessRef": stored.get("ref"), "accessMasked": stored.get("masked"),
            "backend": stored.get("backend"),
            "note": f"use --secret-allow '{stored.get('ref')}' for ksef:// API calls"}
