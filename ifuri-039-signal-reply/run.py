# Author: Tom Sapletta · Part of the ifURI solution.
"""IFURI-039 — odpisz na OSTATNIĄ wiadomość Signal na węźle lenovo.

Headless runner nad connectorem ``signal://``. Realizuje pełny proces URI:

    messages/query/inbox   →  wskaż OSTATNIĄ odebraną wiadomość (adresat = jej nadawca)
    message/command/reply  →  odpowiedz treścią (domyślnie: "OK, potwierdzam.")
    messages/query/list    →  verify: odpowiedź trafiła do wątku (postcondition)

Reply jest zadeklarowany jako REVERSIBLE (inverse = delete-for-everyone), więc
safe:// może orzec safe-auto: odwracalne + weryfikowalne → działaj, nie pytaj.

Transport:
  * Realnie: ``signal-cli`` z kontem operatora (``signal-cli link`` z telefonem).
  * Gdy signal-cli niedostępny albo ``SIGNAL_CLI_MOCK=1`` → tryb MOCK: cały przepływ
    (inbox→reply→verify→inverse) działa na plikach outbox/inbox, bez realnego konta.
    Realne dostarczenie to zależność zewnętrzna, której system NIE utworzy sam
    (fizyczny blocker → actor:human: podlinkuj telefon).

Uruchomienie na węźle, gdzie żyje Signal (np. bliźniak lenovo):
    python run.py                       # odpowiada "OK, potwierdzam."
    python run.py "Inna treść"          # własna treść odpowiedzi
"""
from __future__ import annotations

import json
import os
import sys

DEFAULT_REPLY = "OK, potwierdzam."


def _human_escalation(node: str) -> dict:
    """Koperta actor:human w kształcie ``chat_orchestrator._build_escalation_block``.

    Emitowana, gdy Signal NIE jest podlinkowany na węźle (``signal-cli`` nieobecny/
    niezalinkowany): wtedy ``signal-cli receive`` nie zwróci nic → pusty inbox → nie ma
    „ostatniej wiadomości", na którą można odpisać. To fizyczny blocker, którego system nie
    usunie sam — musi go zdjąć człowiek (podlinkować telefon). Standardowy kształt koperty
    pozwala pętli/dashboardowi potraktować to jako human-task (eskalacja), a NIE jako
    przejściową awarię do ponawiania — co powodowało zapętlenie reapera na tym tickecie.
    """
    dash = (os.environ.get("URIRUN_DASHBOARD_BASE") or "http://192.168.188.212:8797").strip().rstrip("/")
    dashboard_url = f"{dash}/?node={node}&fix=signal-not-linked" if node else ""
    action = (f"Podlinkuj Signal na węźle {node!r}: `signal-cli link -n urirun` "
              "(zeskanuj QR telefonem operatora), potem `signal-cli receive`. Dopiero wtedy "
              "istnieje 'ostatnia wiadomość', na którą IFURI-039 może odpisać.")
    return {
        "ok": False, "humanEscalation": True, "kind": "human-task",
        "remediationClass": "signal-not-linked", "node": node,
        "humanAction": action, "command": "signal-cli link -n urirun",
        "dashboardUrl": dashboard_url, "message": action,
        "notify": {"sound": "beep", "reason": "human-task"},
        "next": {"kind": "human-task", "instruction": action,
                 "command": "signal-cli link -n urirun", "dashboardUrl": dashboard_url},
    }


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    message = (args[0] if args else DEFAULT_REPLY).strip()
    try:
        from urirun_connector_signal import core
    except Exception as exc:  # noqa: BLE001
        print(f"BŁĄD importu connectora signal:// — {exc}\n"
              "Zainstaluj: pip install -e urirun-connector-signal")
        return 3

    # 1) Wskaż ostatnią odebraną wiadomość (cel odpowiedzi).
    inbox = core.messages_query_inbox()
    if not inbox.get("ok"):
        print(f"INBOX błąd: {inbox.get('error')}")
        return 4
    last = inbox.get("last")
    if not last:
        if core._mock():  # signal-cli nieobecny/niezalinkowany → fizyczny blocker, actor:human
            esc = _human_escalation(node=(os.environ.get("URIRUN_NODE") or "lenovo"))
            print("ESCALATE actor:human — Signal nie jest podlinkowany na tym węźle; nie ma na co odpisać.")
            print(json.dumps(esc, ensure_ascii=False, indent=1))
            return 2
        print("BLOCKED: brak odebranych wiadomości Signal na tym węźle (pusty inbox).")
        print("  Realny odbiór: `signal-cli -a <konto> receive` (wymaga podlinkowanego telefonu).")
        return 2
    print(f"Ostatnia wiadomość od {last['from']!r}: {last['message']!r}")

    # 2) Odpowiedz (adresat = nadawca ostatniej wiadomości). REVERSIBLE.
    reply = core.message_command_reply(message=message)
    if not reply.get("ok"):
        print(f"REPLY błąd: {reply.get('error')}")
        return 5
    mode = reply.get("mode")
    print(f"✓ Odpowiedziano {reply['to']!r}: {message!r}  (id={reply['id']}, tryb={mode})")
    if mode == "mock":
        print("  Uwaga: tryb MOCK — realne dostarczenie wymaga `signal-cli link` (actor:human).")

    # 3) Verify: odpowiedź jest w wątku (postcondition procesu URI).
    lst = core.messages_query_list(to=reply["to"])
    ok = lst.get("count", 0) >= 1 and any(m.get("message") == message for m in lst.get("messages", []))
    print(f"verify → w wątku {reply['to']!r}: {lst.get('count')} wiad. · potwierdzenie treści: {ok}")
    return 0 if ok else 6


if __name__ == "__main__":
    raise SystemExit(main())
