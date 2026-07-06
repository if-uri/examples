# Author: Tom Sapletta · Part of the ifURI solution.
"""IFURI-033 — headless spam review + move-to-Junk on the lenovo mailbox over IMAP.

The human-in-the-loop runner behind the /work "Operacje" panel. It resolves IMAP
credentials from the secret layer (keyring first, then env) — it NEVER takes them on the
command line and NEVER prints the password. Then it runs the email:// flow:

    folders/list  →  inbox/list  →  classify  →  [move spam → Junk]

Usage:
    python run.py review   # read-only: list + classify, print what WOULD move (default)
    python run.py move     # actually move classified spam to the Junk folder (mutation)

Credentials (set once, they stay in your OS keyring — I cannot set these for you):
    keyring set mail imap_host      # e.g. imap.gmail.com  (or export MAIL_IMAP_HOST)
    keyring set mail user           # your address         (or export MAIL_USER)
    keyring set mail main           # an APP-PASSWORD, not your login password
"""
from __future__ import annotations

import os
import sys


def _cred(keyring_account: str, env_var: str) -> str:
    """Resolve one credential: OS keyring (service 'mail') first, then an env var."""
    val = os.environ.get(env_var)
    if val:
        return val
    try:
        import keyring
        return keyring.get_password("mail", keyring_account) or ""
    except Exception:  # noqa: BLE001 - keyring optional; fall through to "missing"
        return ""


def _resolve_creds() -> tuple[str, str, str]:
    return (_cred("imap_host", "MAIL_IMAP_HOST"),
            _cred("user", "MAIL_USER"),
            _cred("main", "MAIL_APP_PASSWORD"))


def _missing_creds_notice() -> None:
    print("BLOCKED: brak poświadczeń IMAP. Ustaw je raz (zostają w keyring — nie widzę ich):")
    print("  keyring set mail imap_host      # np. imap.gmail.com")
    print("  keyring set mail user           # Twój adres")
    print("  keyring set mail main           # APP-PASSWORD (nie hasło logowania)")
    print("Alternatywa: export MAIL_IMAP_HOST=... MAIL_USER=... MAIL_APP_PASSWORD=...")


def _print_spam(spam: list) -> None:
    if not spam:
        print("Brak wiadomości sklasyfikowanych jako spam.")
        return
    print(f"Spam-kandydaci ({len(spam)}):")
    for m in spam:
        print(f"  [{m.get('uid')}] {m.get('from','')[:48]!r}  |  {m.get('subject','')[:60]!r}"
              f"  → {','.join(m.get('reasons') or [])}")


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "review").strip().lower()
    imap_host, user, password = _resolve_creds()
    if not (imap_host and user and password):
        _missing_creds_notice()
        return 2
    try:
        from urirun_connector_email.core import (folders_query_list, inbox_query_list,
                                                 message_query_classify, message_command_move)
    except Exception as exc:  # noqa: BLE001
        print(f"BŁĄD importu connectora email:// — {exc}\nZainstaluj: pip install -e urirun-connector-email")
        return 3

    fr = folders_query_list(imap_host, user, password)
    if not fr.get("ok"):
        print(f"IMAP folders błąd: {fr.get('error')}")
        return 4
    junk = fr.get("junk_folder") or "Junk"
    print(f"Połączono. Folder Junk: {junk!r}. Wszystkie foldery: {fr.get('folders')}")

    il = inbox_query_list(imap_host, user, password, limit=50)
    if not il.get("ok"):
        print(f"INBOX błąd: {il.get('error')}")
        return 5
    cl = message_query_classify(il.get("messages") or [])
    spam = [m for m in (cl.get("classified") or []) if m.get("spam")]
    print(f"INBOX: {il.get('count')} wiadomości · spam: {cl.get('spam_count')}")
    _print_spam(spam)

    uids = cl.get("spam_uids") or []
    if mode != "move":
        print(f"\nDRY-RUN. Aby przenieść {len(uids)} wiad. do {junk!r} — zatwierdź operację "
              "'Przenieś spam do Junk' w panelu /work.")
        return 0
    if not uids:
        print("Nic do przeniesienia.")
        return 0
    mv = message_command_move(imap_host, user, password, dest=junk, uids=uids)
    if not mv.get("ok"):
        print(f"MOVE błąd: {mv.get('error')}")
        return 6
    print(f"✓ Przeniesiono {mv.get('count')} wiadomości do {junk!r}: {mv.get('moved')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
