# Author: Tom Sapletta · Part of the ifURI solution.
"""IFURI-033 · WARIANT B — przegląd spamu z LOKALNEGO Thunderbirda, BEZ hasła.

Thunderbird już się uwierzytelnił i ściągnął pocztę do lokalnego profilu (pliki mbox).
Ten runner czyta INBOX prosto z dysku — nie loguje się nigdzie, nie potrzebuje żadnych
poświadczeń — i podaje wiadomości do czystego (bez-credsowego) klasyfikatora spamu
connectora email://. Read-only: pokazuje spam-kandydatów, niczego nie przenosi.

Uruchomienie tam, gdzie żyje Thunderbird (np. bliźniak na lenovo):
    python run_local.py                    # auto-wykrycie profilu
    TB_PROFILE_DIR=/ścieżka/do/profilu python run_local.py

Przeniesienie do Junk lokalnie = edycja plików mbox (ryzykowne) — zostaje po stronie
serwera (IMAP: run.py move) albo sterowania GUI Thunderbirda przez kvm://.
"""
from __future__ import annotations

import mailbox
import os
import sys
from email.header import decode_header, make_header
from pathlib import Path

_ROOTS = (
    "~/.var/app/net.thunderbird.Thunderbird/.thunderbird",
    "~/.var/app/org.mozilla.Thunderbird/.thunderbird",
    "~/.thunderbird",
    "~/.icedove",
)


def _profiles() -> list[Path]:
    override = os.environ.get("TB_PROFILE_DIR")
    if override:
        p = Path(override).expanduser()
        return [p] if p.is_dir() else []
    found = []
    for root in _ROOTS:
        r = Path(root).expanduser()
        if not r.is_dir():
            continue
        for child in r.iterdir():
            if child.is_dir() and ((child / "Mail").is_dir() or (child / "ImapMail").is_dir()):
                found.append(child)
    return found


def _inbox_mboxes(profile: Path) -> list[Path]:
    """INBOX mbox files under a profile (Mail/ + ImapMail/), excluding .msf indexes."""
    out = []
    for sub in ("ImapMail", "Mail"):
        base = profile / sub
        if base.is_dir():
            out += [p for p in base.rglob("INBOX") if p.is_file()]
    return out


def _decode(value: str) -> str:
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:  # noqa: BLE001
        return value or ""


def _read_messages(path: Path, limit: int) -> list[dict]:
    box = mailbox.mbox(str(path))
    try:
        keys = list(box.keys())[-limit:]
        rows = []
        for k in keys:
            m = box[k]
            rows.append({"uid": f"{path.parent.name}/{k}", "from": _decode(str(m.get("From", ""))),
                         "subject": _decode(str(m.get("Subject", ""))), "date": str(m.get("Date", ""))})
        return rows
    finally:
        box.close()


def _ollama_spam(messages: list[dict], model: str) -> dict | None:
    """Klasyfikacja spamu przez LOKALNY ollama (HTTP :11434). None → ollama niedostępny."""
    import json
    import urllib.request
    base = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    name = model.split("/", 1)[1] if "/" in model else model
    out = []
    for m in messages:
        prompt = ("Czy ten e-mail to spam? Odpowiedz JEDNYM słowem: SPAM albo HAM.\n"
                  f"Od: {m.get('from','')}\nTemat: {m.get('subject','')}\n")
        body = json.dumps({"model": name, "prompt": prompt, "stream": False,
                           "options": {"temperature": 0}}).encode()
        try:
            req = urllib.request.Request(base + "/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())  # noqa: S310
        except Exception:  # noqa: BLE001 - ollama off/unreachable → caller falls back to rules
            return None
        verdict = "spam" in str(resp.get("response", "")).lower()
        out.append({**m, "spam": verdict, "score": 1 if verdict else 0,
                    "reasons": ["ollama:" + name] if verdict else []})
    spam = [m for m in out if m["spam"]]
    return {"ok": True, "classified": out, "spam_count": len(spam),
            "spam_uids": [m["uid"] for m in spam]}


def _classify(messages: list[dict]) -> dict:
    """Klasyfikuj spam. Jawnie zwraca który LLM uczestniczył (pole 'llm').

    EMAIL_LLM_MODEL (np. 'ollama/llama3.1') → lokalny ollama; inaczej reguły connectora
    (bez LLM). Każde zadanie deklaruje SWÓJ model — nic nie działa 'nie wiadomo czym'."""
    model = os.environ.get("EMAIL_LLM_MODEL", "").strip()
    if model:
        r = _ollama_spam(messages, model)
        if r is not None:
            return {**r, "llm": model}
        print(f"(LLM {model} niedostępny — fallback na reguły)")
    from urirun_connector_email.core import message_query_classify
    return {**message_query_classify(messages), "llm": "reguły (bez LLM)"}


def main() -> int:
    profiles = _profiles()
    if not profiles:
        print("Nie znaleziono profilu Thunderbirda na TYM hoście (" + os.uname().nodename + ").")
        print("Thunderbird bliźniaka żyje na lenovo — uruchom tam, albo wskaż profil:")
        print("  TB_PROFILE_DIR=/ścieżka/do/xxxx.default python run_local.py")
        print("Szukane lokalizacje:", ", ".join(_ROOTS))
        return 2
    limit = int(os.environ.get("TB_LIMIT") or 50)
    all_msgs: list[dict] = []
    for prof in profiles:
        inboxes = _inbox_mboxes(prof)
        print(f"Profil: {prof}  ·  INBOX-ów: {len(inboxes)}")
        for ib in inboxes:
            try:
                msgs = _read_messages(ib, limit)
            except Exception as exc:  # noqa: BLE001
                print(f"  (pomiń {ib}: {exc})")
                continue
            print(f"  {ib.parent.name}: {len(msgs)} wiad.")
            all_msgs += msgs
    if not all_msgs:
        print("Brak wiadomości w lokalnym INBOX (Thunderbird niezsynchronizowany?).")
        return 0
    cl = _classify(all_msgs)
    if not cl.get("ok"):
        print(f"Klasyfikacja błąd: {cl.get('error')}")
        return 3
    spam = [m for m in (cl.get("classified") or []) if m.get("spam")]
    print(f"\nRazem: {len(all_msgs)} wiad. · spam: {cl.get('spam_count')} (bez logowania, z lokalnego mbox)")
    for m in spam:
        print(f"  [{m.get('uid')}] {m.get('from','')[:46]!r} | {m.get('subject','')[:56]!r}"
              f" → {','.join(m.get('reasons') or [])}")
    if not spam:
        print("Brak spamu w lokalnej skrzynce.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
