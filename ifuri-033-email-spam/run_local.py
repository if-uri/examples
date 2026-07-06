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
    """PIERWSZE ``limit`` wiadomości z mboxa (z Message-ID do stabilnego hashu)."""
    box = mailbox.mbox(str(path))
    try:
        keys = list(box.keys())[:limit]
        rows = []
        for k in keys:
            m = box[k]
            rows.append({"uid": f"{path.parent.name}/{k}", "from": _decode(str(m.get("From", ""))),
                         "subject": _decode(str(m.get("Subject", ""))), "date": str(m.get("Date", "")),
                         "message_id": str(m.get("Message-ID", "")).strip()})
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
    import checkpoint  # trwały stan: hash wiadomości → nie duplikuj, wznawiaj
    limit = int(os.environ.get("EMAIL_FIRST_N") or 10)         # "pierwsze 10 z pierwszej skrzynki"
    reclassify = "--reclassify" in sys.argv or "--all" in sys.argv
    prof = profiles[0]                                          # PIERWSZA skrzynka
    inboxes = _inbox_mboxes(prof)
    if not inboxes:
        print(f"Profil {prof} nie ma INBOX-a.")
        return 0
    ib = inboxes[0]
    account = os.environ.get("EMAIL_ACCOUNT") or f"{prof.name}/{ib.parent.name}"
    msgs = _read_messages(ib, limit)
    print(f"Skrzynka: {account}  ·  pierwsze {len(msgs)} wiad. (z {ib})")
    if not msgs:
        print("Brak wiadomości (Thunderbird niezsynchronizowany?).")
        return 0

    fresh, done = (msgs, []) if reclassify else checkpoint.partition(account, msgs)
    print(f"Nowe do klasyfikacji: {len(fresh)}  ·  już przetworzone (pomijam): {len(done)}"
          + (" [--reclassify: przetwarzam wszystko]" if reclassify else ""))
    for m in done:
        print(f"  ⏭  {m.get('uid')}  {m.get('subject','')[:50]!r} (w stanie)")
    if not fresh:
        print("Nic nowego — wszystko już przetworzone w poprzednich przebiegach.")
        print("Stan:", checkpoint.summary(account))
        return 0

    cl = _classify(fresh)
    if not cl.get("ok"):
        print(f"Klasyfikacja błąd: {cl.get('error')}")
        return 3
    classified = cl.get("classified") or []
    run_id = os.environ.get("EMAIL_RUN_ID") or "local-" + str(int(msgs[0].get("uid", "0").split("/")[-1] or 0))
    checkpoint.record(account, classified, run_id)
    spam = [m for m in classified if m.get("spam")]
    print(f"\nLLM: {cl.get('llm')}  ·  sklasyfikowano NOWYCH: {len(classified)}  ·  spam: {len(spam)}")
    for m in classified:
        tag = "SPAM" if m.get("spam") else "ham "
        print(f"  {tag} [{m.get('uid')}] {m.get('from','')[:40]!r} | {m.get('subject','')[:50]!r}"
              + (f" → {','.join(m.get('reasons') or [])}" if m.get("spam") else ""))
    print("Zapisano stan:", checkpoint.summary(account))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
