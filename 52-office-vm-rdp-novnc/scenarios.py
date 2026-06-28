# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.
#
# Office tasks a user asks for in natural language, each driving a virtual machine
# over RDP through a noVNC (HTML5) view. Each scenario carries:
#   - `nl`: the request a user types,
#   - `steps`: the multi-step URI flow that satisfies it — the plan an LLM produces
#     over the VM-office MCP tool surface (vm_office_system.bindings); the
#     deterministic copy here lets the example run in CI,
#   - `verify(state)`: checks the simulator's END state to confirm the task is
#     actually done — INCLUDING teardown correctness (no dangling RDP sessions /
#     noVNC views) so we observe whether the flow behaves correctly, not just runs.
#
# Session/view ids are deterministic because each scenario runs on a fresh state:
# the first RDP connect is always "s1" (then "s2"), the first noVNC view "v1".

from __future__ import annotations


def _step(uri, **payload):
    return {"uri": uri, "payload": payload}


def _ocr_has(state, needle, vm=None):
    return any(needle in e["text"] and (vm is None or e["vm"] == vm) for e in state["ocr_log"])


# --- 1. finance workstation: open Excel on a Win11 VM, enter + save a figure -
FINANCE = {
    "id": "finance",
    "title": "Connect to the Win11 finance VM over RDP/noVNC, enter Q3 revenue in Excel, save & verify",
    "nl": "Połącz się z maszyną finansową przez RDP w noVNC, otwórz Excela, wpisz przychód Q3, zapisz i potwierdź zrzutem.",
    "steps": [
        _step("vm://fleet/catalog/query/list"),
        _step("vm://fleet/instance/command/start", vm="win11-finance"),
        _step("rdp://gateway/session/command/connect", vm="win11-finance", user="anna.k"),
        _step("novnc://gateway/view/command/open", session="s1"),
        _step("novnc://gateway/view/query/status", view="v1"),
        _step("desktop://vm/app/command/launch", session="s1", app="excel"),
        _step("desktop://vm/input/command/type", session="s1", text="Przychód Q3: 1 480 000 PLN"),
        _step("desktop://vm/input/command/hotkey", session="s1", keys="ctrl+s"),
        _step("fs://vm/file/command/save", session="s1", path="Finanse/Q3.xlsx", content="Przychód Q3: 1 480 000 PLN"),
        _step("desktop://vm/screen/query/screenshot", session="s1"),
        _step("desktop://vm/screen/query/ocr", session="s1"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("notify://gateway/desktop/command/send", message="Raport Q3 zapisany na VM finansowej"),
    ],
    "verify": lambda s: (
        _ocr_has(s, "1 480 000", vm="win11-finance")
        and "Finanse/Q3.xlsx" in s["vms"]["win11-finance"]["files"]
        and len(s["screenshots"]) >= 1
        and len(s["sessions"]) == 0 and len(s["views"]) == 0,           # clean teardown
        f"ocr={_ocr_has(s, '1 480 000')} saved={'Finanse/Q3.xlsx' in s['vms']['win11-finance']['files']} "
        f"sessions={len(s['sessions'])} views={len(s['views'])}"),
}

# --- 2. move a value between two VMs via RDP clipboard redirection -----------
MULTI_VM = {
    "id": "multi-vm",
    "title": "Copy a figure from the finance VM to the sales VM using RDP clipboard redirection",
    "nl": "Otwórz dwie maszyny (finanse i sprzedaż), skopiuj przychód z finansów przez schowek RDP i wklej go w arkuszu sprzedaży.",
    "steps": [
        _step("vm://fleet/instance/command/start", vm="win11-finance"),
        _step("vm://fleet/instance/command/start", vm="win-sales"),
        _step("rdp://gateway/session/command/connect", vm="win11-finance", user="anna.k"),
        _step("rdp://gateway/session/command/connect", vm="win-sales", user="bartek.s"),
        _step("desktop://vm/app/command/launch", session="s1", app="excel"),
        _step("desktop://vm/input/command/type", session="s1", text="Przychód: 1 480 000"),
        _step("clipboard://gateway/buffer/command/set", text="1 480 000"),
        _step("clipboard://gateway/buffer/query/get"),
        _step("desktop://vm/app/command/launch", session="s2", app="excel"),
        _step("desktop://vm/input/command/type", session="s2", text="Z finansów: 1 480 000"),
        _step("desktop://vm/screen/query/ocr", session="s2"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("rdp://gateway/session/command/disconnect", session="s2"),
        _step("notify://gateway/desktop/command/send", message="Przychód przeniesiony finanse → sprzedaż"),
    ],
    "verify": lambda s: (
        s["clipboard"] == "1 480 000"
        and _ocr_has(s, "1 480 000", vm="win-sales")
        and len(s["sessions"]) == 0,
        f"clipboard={s['clipboard']!r} sales_ocr={_ocr_has(s, '1 480 000', vm='win-sales')} sessions={len(s['sessions'])}"),
}

# --- 3. on-demand VM: spin up, work, tear down (full lifecycle) --------------
ONBOARD = {
    "id": "onboard",
    "title": "Spin up a fresh dev VM on demand, do a quick task over noVNC, then power it down",
    "nl": "Uruchom maszynę deweloperską na żądanie, połącz przez RDP/noVNC, otwórz przeglądarkę, zrób zrzut, rozłącz i wyłącz maszynę.",
    "steps": [
        _step("vm://fleet/catalog/query/list"),
        _step("vm://fleet/instance/command/start", vm="ubuntu-dev"),
        _step("rdp://gateway/session/command/connect", vm="ubuntu-dev", user="ci"),
        _step("novnc://gateway/view/command/open", session="s1"),
        _step("novnc://gateway/view/query/status", view="v1"),
        _step("desktop://vm/app/command/launch", session="s1", app="firefox"),
        _step("desktop://vm/input/command/type", session="s1", text="https://status.corp/health"),
        _step("desktop://vm/screen/query/screenshot", session="s1"),
        _step("novnc://gateway/view/command/close", view="v1"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("vm://fleet/instance/command/stop", vm="ubuntu-dev"),
        _step("notify://gateway/desktop/command/send", message="Maszyna deweloperska zwolniona"),
    ],
    "verify": lambda s: (
        s["vms"]["ubuntu-dev"]["power"] == "off"
        and len(s["sessions"]) == 0 and len(s["views"]) == 0
        and len(s["screenshots"]) >= 1,
        f"power={s['vms']['ubuntu-dev']['power']} sessions={len(s['sessions'])} views={len(s['views'])}"),
}

# --- 4. invoice processing: OCR an image inside the VM, key it into a form ---
INVOICE = {
    "id": "invoice",
    "title": "OCR an invoice dropped into the VM, key the values into the billing app, save the record",
    "nl": "Na maszynie finansowej odczytaj fakturę z obrazka (OCR), przepisz dane do aplikacji księgowej, zapisz potwierdzenie.",
    "steps": [
        _step("vm://fleet/instance/command/start", vm="win11-finance"),
        _step("rdp://gateway/session/command/connect", vm="win11-finance", user="anna.k"),
        _step("novnc://gateway/view/command/open", session="s1"),
        _step("screen://vm/ocr/query/image", session="s1", image="invoice.png"),
        _step("desktop://vm/app/command/launch", session="s1", app="ksiegowosc"),
        _step("desktop://vm/input/command/type", session="s1", text="Faktura 11/2026"),
        _step("desktop://vm/input/command/type", session="s1", text="Kwota: 2 460,00 PLN"),
        _step("desktop://vm/input/command/hotkey", session="s1", keys="ctrl+s"),
        _step("fs://vm/file/command/save", session="s1", path="Ksiegowosc/FV-11-2026.txt", content="Faktura 11/2026 — 2 460,00 PLN — zaksięgowana."),
        _step("desktop://vm/screen/query/ocr", session="s1"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("notify://gateway/desktop/command/send", message="Faktura 11/2026 zaksięgowana"),
    ],
    "verify": lambda s: (
        _ocr_has(s, "2 460", vm="win11-finance")
        and "Ksiegowosc/FV-11-2026.txt" in s["vms"]["win11-finance"]["files"]
        and len(s["sessions"]) == 0,
        f"ocr={_ocr_has(s, '2 460')} record={'Ksiegowosc/FV-11-2026.txt' in s['vms']['win11-finance']['files']}"),
}

# --- 5. secure teardown: explicit close ordering, no dangling artefacts ------
SECURE = {
    "id": "secure",
    "title": "End-of-day: close the noVNC view, disconnect RDP, confirm nothing is left dangling",
    "nl": "Po pracy zamknij widok noVNC, rozłącz sesję RDP i upewnij się, że nie zostały żadne otwarte sesje ani widoki.",
    "steps": [
        _step("vm://fleet/instance/command/start", vm="win-sales"),
        _step("rdp://gateway/session/command/connect", vm="win-sales", user="bartek.s"),
        _step("novnc://gateway/view/command/open", session="s1"),
        _step("desktop://vm/app/command/launch", session="s1", app="outlook"),
        _step("desktop://vm/input/command/type", session="s1", text="Raport dzienny wysłany"),
        _step("desktop://vm/screen/query/screenshot", session="s1"),
        _step("rdp://gateway/session/query/list"),
        _step("novnc://gateway/view/command/close", view="v1"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("rdp://gateway/session/query/list"),
        _step("notify://gateway/desktop/command/send", message="Sesje zamknięte, brak wiszących połączeń"),
    ],
    "verify": lambda s: (
        len(s["sessions"]) == 0 and len(s["views"]) == 0,
        f"sessions={len(s['sessions'])} views={len(s['views'])}"),
}

# --- 6. resilient connect: VM is off -> plan checks, starts it, then connects -
RESILIENT = {
    "id": "resilient",
    "title": "Reach a VM that may be powered off — check the fleet, power it on, then connect & work",
    "nl": "Wejdź na maszynę sprzedażową; jeśli jest wyłączona, najpierw ją uruchom, dopiero potem połącz i zapisz notatkę.",
    "steps": [
        _step("vm://fleet/catalog/query/list"),
        _step("vm://fleet/instance/command/start", vm="win-sales"),     # precondition: ensure powered on
        _step("rdp://gateway/session/command/connect", vm="win-sales", user="bartek.s"),
        _step("novnc://gateway/view/command/open", session="s1"),
        _step("desktop://vm/app/command/launch", session="s1", app="notepad"),
        _step("desktop://vm/input/command/type", session="s1", text="Notatka: leady z targów"),
        _step("fs://vm/file/command/save", session="s1", path="Notatki/leady.txt", content="Leady z targów — do obdzwonienia."),
        _step("fs://vm/file/query/read", session="s1", path="Notatki/leady.txt"),
        _step("desktop://vm/screen/query/ocr", session="s1"),
        _step("rdp://gateway/session/command/disconnect", session="s1"),
        _step("notify://gateway/desktop/command/send", message="Notatka zapisana na VM sprzedaży"),
    ],
    "verify": lambda s: (
        "Notatki/leady.txt" in s["vms"]["win-sales"]["files"]
        and _ocr_has(s, "leady", vm="win-sales")
        and len(s["sessions"]) == 0,
        f"saved={'Notatki/leady.txt' in s['vms']['win-sales']['files']} ocr={_ocr_has(s, 'leady')}"),
}

SCENARIOS = [FINANCE, MULTI_VM, ONBOARD, INVOICE, SECURE, RESILIENT]
