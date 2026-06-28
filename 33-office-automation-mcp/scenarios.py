# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Six office tasks a user asks for in natural language. Each carries:
#   - `nl`: the request a user types,
#   - `steps`: the multi-step URI flow that satisfies it (≥10 steps) — the plan an
#     LLM produces over the office MCP tool surface (office_system.bindings); the
#     deterministic copy here lets the example run in CI,
#   - `verify(state)`: checks the simulator's END state to confirm the task is
#     actually done (returns (ok, message)).

from __future__ import annotations


def _step(uri, **payload):
    return {"uri": uri, "payload": payload}


# --- 1. send a report by email ---------------------------------------------
REPORT = {
    "id": "report",
    "title": "Prepare a Q2 report and email it to the boss with attachments",
    "nl": "Przygotuj raport sprzedaży za Q2, zapisz go, dołącz podsumowanie i wyślij mailem do szefa.",
    "steps": [
        _step("app://office/launch/command/open", app="files"),
        _step("fs://office/file/command/write", path="reports/q2.txt", content="Q2 sprzedaż: 1 240 000 PLN (+12% r/r)."),
        _step("fs://office/file/query/read", path="reports/q2.txt"),
        _step("fs://office/file/command/write", path="reports/q2-summary.txt", content="Podsumowanie: cel przekroczony o 12%."),
        _step("app://office/launch/command/open", app="email"),
        _step("email://office/inbox/query/search", q="report"),
        _step("email://office/message/command/compose", to="boss@corp", subject="Raport Q2", body="W załączeniu raport i podsumowanie."),
        _step("email://office/message/command/attach", path="reports/q2.txt"),
        _step("email://office/message/command/attach", path="reports/q2-summary.txt"),
        _step("email://office/message/command/send"),
        _step("notify://office/desktop/command/send", message="Raport Q2 wysłany do szefa"),
    ],
    "verify": lambda s: (
        len(s["email"]["sent"]) == 1 and s["email"]["sent"][0]["to"] == "boss@corp"
        and len(s["email"]["sent"][0]["attachments"]) == 2,
        f"sent={len(s['email']['sent'])} attachments={len(s['email']['sent'][0]['attachments']) if s['email']['sent'] else 0}"),
}

# --- 2. web research -> notes -----------------------------------------------
RESEARCH = {
    "id": "research",
    "title": "Research a web page, screenshot it, and save notes to the editor",
    "nl": "Wejdź na example.com, odczytaj stronę, zrób zrzut, skopiuj kluczowe info i zapisz notatki w edytorze.",
    "steps": [
        _step("app://office/launch/command/open", app="browser"),
        _step("browser://office/tab/command/open", url="https://example.com/pricing"),
        _step("browser://office/page/query/read"),
        _step("browser://office/page/query/screenshot"),
        _step("clipboard://office/buffer/command/copy", text="Invoice total: 199.00 PLN; contact sales@example.com"),
        _step("app://office/launch/command/open", app="editor"),
        _step("fs://office/file/command/write", path="notes/research.txt", content="Badanie example.com — cennik."),
        _step("clipboard://office/buffer/query/paste"),
        _step("fs://office/file/command/write", path="notes/research-key.txt", content="Invoice total: 199.00 PLN; contact sales@example.com"),
        _step("fs://office/file/query/read", path="notes/research.txt"),
        _step("notify://office/desktop/command/send", message="Notatki z badania zapisane"),
    ],
    "verify": lambda s: (
        "notes/research.txt" in s["files"] and "notes/research-key.txt" in s["files"]
        and len(s["screenshots"]) >= 1 and bool(s["clipboard"]),
        f"notes={'notes/research.txt' in s['files']} screenshots={len(s['screenshots'])}"),
}

# --- 3. tidy the desktop ----------------------------------------------------
TIDY = {
    "id": "tidy",
    "title": "Open several apps, then tidy the desktop down to the essentials",
    "nl": "Pootwieraj przeglądarkę, mail, edytor i kalkulator, potem uporządkuj pulpit: zamknij zbędne okna i kalkulator.",
    "steps": [
        _step("app://office/launch/command/open", app="browser"),
        _step("app://office/launch/command/open", app="email"),
        _step("app://office/launch/command/open", app="editor"),
        _step("app://office/launch/command/open", app="calculator"),
        _step("window://office/manager/query/list"),
        _step("window://office/manager/command/focus", id="w3"),
        _step("window://office/manager/command/close", id="w1"),
        _step("window://office/manager/command/close", id="w2"),
        _step("app://office/launch/command/quit", app="calculator"),
        _step("window://office/manager/query/list"),
        _step("notify://office/desktop/command/send", message="Pulpit uporządkowany"),
    ],
    "verify": lambda s: (
        len(s["windows"]) <= 2 and "calculator" not in s["apps"],
        f"windows={len(s['windows'])} apps={s['apps']}"),
}

# --- 4. process an invoice (OCR -> form -> submit) ---------------------------
INVOICE = {
    "id": "invoice",
    "title": "OCR an invoice image, fill a web form and submit it, save the record",
    "nl": "Przetwórz fakturę: odczytaj dane z obrazka (OCR), wypełnij formularz w portalu i wyślij, zapisz potwierdzenie.",
    "steps": [
        _step("fs://office/file/command/write", path="incoming/invoice.png", content="<image bytes>"),
        _step("screen://office/ocr/query/text", image="invoice.png"),
        _step("app://office/launch/command/open", app="browser"),
        _step("browser://office/tab/command/open", url="https://billing.corp/invoices/new"),
        _step("browser://office/page/command/type", selector="invoice_no", text="7/2026"),
        _step("browser://office/page/command/type", selector="amount", text="199.00"),
        _step("browser://office/page/command/type", selector="nip", text="123-456-78-90"),
        _step("browser://office/page/command/click", selector="submit"),
        _step("browser://office/page/query/read"),
        _step("fs://office/file/command/write", path="records/invoice-7-2026.txt", content="Faktura 7/2026 — 199,00 PLN — wysłana."),
        _step("notify://office/desktop/command/send", message="Faktura 7/2026 przetworzona"),
    ],
    "verify": lambda s: (
        "records/invoice-7-2026.txt" in s["files"]
        and any(t.get("submitted") for t in s["browser"]["tabs"]),
        f"record={'records/invoice-7-2026.txt' in s['files']} submitted={any(t.get('submitted') for t in s['browser']['tabs'])}"),
}

# --- 5. schedule a meeting + invites ---------------------------------------
MEETING = {
    "id": "meeting",
    "title": "Schedule a team meeting and email the invitations",
    "nl": "Zaplanuj spotkanie zespołu na czwartek 10:00 i wyślij zaproszenia mailem do zespołu oraz do szefa.",
    "steps": [
        _step("app://office/launch/command/open", app="calendar"),
        _step("calendar://office/event/command/create", title="Sync zespołu", when="2026-06-25 10:00", invitees="team@corp"),
        _step("calendar://office/event/query/list"),
        _step("app://office/launch/command/open", app="email"),
        _step("email://office/message/command/compose", to="team@corp", subject="Zaproszenie: Sync zespołu", body="Czwartek 10:00. Do zobaczenia."),
        _step("email://office/message/command/send"),
        _step("email://office/message/command/compose", to="boss@corp", subject="FYI: Sync zespołu", body="Zaplanowane na czwartek 10:00."),
        _step("email://office/message/command/send"),
        _step("email://office/inbox/query/list"),
        _step("calendar://office/event/query/list"),
        _step("notify://office/desktop/command/send", message="Spotkanie zaplanowane, zaproszenia wysłane"),
    ],
    "verify": lambda s: (
        len(s["calendar"]) == 1 and len(s["email"]["sent"]) == 2,
        f"events={len(s['calendar'])} sent={len(s['email']['sent'])}"),
}

# --- 6. daily backup --------------------------------------------------------
BACKUP = {
    "id": "backup",
    "title": "Back up today's documents into a backup folder and verify the count",
    "nl": "Zrób codzienny backup dokumentów: skopiuj wszystkie pliki z docs do folderu backup i potwierdź liczbę.",
    "steps": [
        _step("fs://office/file/command/write", path="docs/a.txt", content="Dokument A"),
        _step("fs://office/file/command/write", path="docs/b.txt", content="Dokument B"),
        _step("fs://office/file/command/write", path="docs/c.txt", content="Dokument C"),
        _step("fs://office/dir/query/list", dir="docs"),
        _step("fs://office/file/command/copy", src="docs/a.txt", dst="backup/a.txt"),
        _step("fs://office/file/command/copy", src="docs/b.txt", dst="backup/b.txt"),
        _step("fs://office/file/command/copy", src="docs/c.txt", dst="backup/c.txt"),
        _step("fs://office/dir/query/list", dir="backup"),
        _step("fs://office/file/query/read", path="backup/a.txt"),
        _step("notify://office/desktop/command/send", message="Backup ukończony: 3 pliki"),
    ],
    "verify": lambda s: (
        sum(1 for p in s["files"] if p.startswith("backup/")) == 3
        and s["files"].get("backup/a.txt") == s["files"].get("docs/a.txt"),
        f"backup_files={sum(1 for p in s['files'] if p.startswith('backup/'))}"),
}

# --- 7. reconcile expenses from receipts (OCR -> summary -> email finance) ---
EXPENSES = {
    "id": "expenses",
    "title": "OCR two receipts, write an expense reconciliation and email it to finance",
    "nl": "Rozlicz wydatki: odczytaj dwa paragony/faktury (OCR), policz sumę, zapisz zestawienie i wyślij je do księgowości.",
    "steps": [
        _step("fs://office/file/command/write", path="incoming/receipt.png", content="<image bytes>"),
        _step("screen://office/ocr/query/text", image="receipt.png"),
        _step("fs://office/file/command/write", path="incoming/invoice.png", content="<image bytes>"),
        _step("screen://office/ocr/query/text", image="invoice.png"),
        _step("app://office/launch/command/open", app="editor"),
        _step("fs://office/file/command/write", path="reports/expenses.txt", content="Wydatki: paragon 42,00 PLN + faktura 199,00 PLN = 241,00 PLN."),
        _step("fs://office/file/query/read", path="reports/expenses.txt"),
        _step("app://office/launch/command/open", app="email"),
        _step("email://office/message/command/compose", to="finance@corp", subject="Rozliczenie wydatków", body="W załączeniu zestawienie wydatków."),
        _step("email://office/message/command/attach", path="reports/expenses.txt"),
        _step("email://office/message/command/send"),
        _step("notify://office/desktop/command/send", message="Zestawienie wydatków wysłane do księgowości"),
    ],
    "verify": lambda s: (
        "reports/expenses.txt" in s["files"]
        and len(s["email"]["sent"]) == 1 and s["email"]["sent"][0]["to"] == "finance@corp"
        and len(s["email"]["sent"][0]["attachments"]) == 1,
        f"summary={'reports/expenses.txt' in s['files']} sent={len(s['email']['sent'])}"),
}

# --- 8. approval workflow: read a request, decide, reply, schedule follow-up -
APPROVAL = {
    "id": "approval",
    "title": "Read the boss's request, record a decision, reply, and schedule a follow-up",
    "nl": "Znajdź w skrzynce prośbę o raport, zapisz decyzję o akceptacji, odpisz szefowi i zaplanuj spotkanie kontrolne.",
    "steps": [
        _step("app://office/launch/command/open", app="email"),
        _step("email://office/inbox/query/list"),
        _step("email://office/inbox/query/search", q="report"),
        _step("fs://office/file/command/write", path="decisions/q2-approve.txt", content="Decyzja: raport Q2 zatwierdzony do wysyłki."),
        _step("email://office/message/command/compose", to="boss@corp", subject="Re: Q2 report?", body="Zatwierdzone — raport wychodzi dziś."),
        _step("email://office/message/command/attach", path="decisions/q2-approve.txt"),
        _step("email://office/message/command/send"),
        _step("app://office/launch/command/open", app="calendar"),
        _step("calendar://office/event/command/create", title="Kontrola raportu Q2", when="2026-07-01 09:00", invitees="boss@corp"),
        _step("calendar://office/event/query/list"),
        _step("notify://office/desktop/command/send", message="Decyzja zapisana, odpowiedź wysłana, kontrola zaplanowana"),
    ],
    "verify": lambda s: (
        "decisions/q2-approve.txt" in s["files"]
        and len(s["email"]["sent"]) == 1 and s["email"]["sent"][0]["to"] == "boss@corp"
        and len(s["calendar"]) == 1,
        f"decision={'decisions/q2-approve.txt' in s['files']} sent={len(s['email']['sent'])} events={len(s['calendar'])}"),
}

SCENARIOS = [REPORT, RESEARCH, TIDY, INVOICE, MEETING, BACKUP, EXPENSES, APPROVAL]
