# Author: Tom Sapletta · Part of the ifURI solution.
"""Przetwarzanie idempotentne: hash każdej wiadomości + trwały stan klasyfikacji.

Cel: przy cyklicznym uruchamianiu (np. codziennie) NIE przetwarzać drugi raz tego, co już
zostało zrobione — wznawiać od miejsca, w którym skończyliśmy. Każda wiadomość dostaje
stabilny hash (Message-ID, a w razie braku From+Subject+Date). Stan trzymamy per-skrzynka
w ``~/.urirun/host-dashboard/email-state/<konto>.json``:

    { "<hash>": {uid, from, subject, spam, reasons, classified_at, run_id, action} }

Kolejny przebieg czyta ten plik, pomija hashe już obecne i klasyfikuje tylko NOWE.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


def state_path(account: str) -> Path:
    base = Path(os.environ.get("EMAIL_STATE_DIR") or "~/.urirun/host-dashboard/email-state").expanduser()
    base.mkdir(parents=True, exist_ok=True)
    slug = "".join(c if c.isalnum() else "_" for c in (account or "default"))[:60]
    return base / f"{slug}.json"


def msg_hash(m: dict) -> str:
    """Stabilny identyfikator wiadomości — ten sam przy każdym przebiegu."""
    mid = str(m.get("message_id") or "").strip()
    if mid:
        return "mid:" + hashlib.sha1(mid.encode("utf-8", "replace")).hexdigest()[:16]
    raw = "|".join([str(m.get("from", "")), str(m.get("subject", "")), str(m.get("date", ""))])
    return "h:" + hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:16]


def load(account: str) -> dict:
    f = state_path(account)
    if not f.is_file():
        return {}
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def save(account: str, data: dict) -> None:
    state_path(account).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def partition(account: str, messages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Podziel wiadomości na (NOWE, JUŻ-PRZETWORZONE) po hashu w stanie."""
    seen = load(account)
    fresh, done = [], []
    for m in messages:
        (done if msg_hash(m) in seen else fresh).append(m)
    return fresh, done


def record(account: str, classified: list[dict], run_id: str, action: str = "reviewed") -> dict:
    """Zapisz wynik klasyfikacji NOWYCH wiadomości do stanu (merge, nie nadpisuje starych)."""
    data = load(account)
    now = time.time()
    for m in classified:
        data[msg_hash(m)] = {"uid": m.get("uid"), "from": (m.get("from") or "")[:120],
                             "subject": (m.get("subject") or "")[:160], "spam": bool(m.get("spam")),
                             "reasons": m.get("reasons") or [], "classified_at": now,
                             "run_id": run_id, "action": ("moved-to-junk" if m.get("moved") else action)}
    save(account, data)
    return data


def summary(account: str) -> dict:
    data = load(account)
    spam = sum(1 for v in data.values() if v.get("spam"))
    return {"account": account, "total_seen": len(data), "spam": spam, "ham": len(data) - spam,
            "state_file": str(state_path(account))}
