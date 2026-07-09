# Author: Tom Sapletta · Part of the ifURI solution.
"""IFURI-229 — 3-poziomowy łańcuch eskalacji executora w send_via_kvm.

Headless runner nad ``urirun_connector_work.goal.send_via_kvm``. Demonstruje pełny
łańcuch bez dotykania realnego KVM/Signal/sieci:

    EXECUTOR (LLM_MODEL_EXECUTOR) próbuje zadanie
      → VALIDATOR (LLM_MODEL_VALIDATOR) ocenia semantycznie (nie tylko verify=true)
      → jeśli FAIL: EXECUTOR_TWIN (LLM_MODEL_EXECUTOR_TWIN) przejmuje, ta sama linia czasu
        → VALIDATOR ocenia ponownie
        → jeśli znów FAIL: TEACHER (LLM_MODEL_TEACHER) diagnozuje i proponuje KONKRETNĄ
          poprawę (inny URI/prompt/dekompozycję), nie kolejną ślepą powtórkę

Ten przykład celowo NIE łączy się z żadnym prawdziwym węzłem/LLM/Signal — to czysta
demonstracja mechanizmu (grounding: "czy okablowanie działa", nie "czy wysyłka działa").
Real send do prawdziwej osoby wymaga zawsze osobnej, jawnej zgody na treść/odbiorcę
(patrz report/nxdo/IFURI-229-operator-handoff.md) — to poza zakresem tego przykładu.

Scenariusz zaszyty w mocku: executor i twin oboje nie trafiają w pole (verify zawsze
False), więc łańcuch eskaluje aż do teachera — to ścieżka najbardziej wymagająca
i najrzadziej ćwiczona, dlatego wybrana jako domyślna demonstracja.

Uruchomienie:
    python run.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Namespace-shadow guard: uruchomione z korzenia repo (cwd=if-uri/), bare `import urirun`
# łapie /if-uri/urirun/ (parasolowy katalog bez __init__.py, PEP 420 namespace package)
# zamiast realnie zainstalowanego pakietu w urirun/adapters/python/urirun/. Wymuszamy
# właściwą ścieżkę na start sys.path, żeby run.py działało niezależnie od cwd.
_REAL_URIRUN_PKG = Path(__file__).resolve().parents[2] / "urirun" / "adapters" / "python"
if _REAL_URIRUN_PKG.is_dir():
    sys.path.insert(0, str(_REAL_URIRUN_PKG))


def _install_mock(goal) -> list[str]:
    """Podmienia zależności sieciowe/LLM na deterministyczny scenariusz: executor i twin
    nie trafiają w pole (verify zawsze False) -> wymusza pełną eskalację do teachera.
    Zwraca listę wywołanych URI (do weryfikacji na końcu, że inquiry:// dostał artefakt).
    """
    node_calls: list[str] = []

    def fake_node_run(node, uri, payload=None, timeout=15.0):
        node_calls.append(uri)
        if "ui/query/verify" in uri:
            return {"present": False}
        if "ui/query/locate" in uri:
            return {"count": 0}
        return {"ok": True}

    micro_calls = {"n": 0}

    def fake_decide_next(state, know, node, max_tokens=200, model=None):
        micro_calls["n"] += 1
        if micro_calls["n"] > 2:
            return {"uri": "done"}
        return {"uri": f"kvm://{node}/input/command/type", "payload": {"text": "TST"}, "reason": "probe"}

    from urirun_connector_work.signal_kvm import KVM_URI_HOST

    def fake_llm_completion(model, prompt, **kw):
        if model == goal._llm_teacher_model():
            return {"ok": True, "model": model, "content": (
                '{"diagnosis": "pole wpisywania nie zostalo poprawnie zlokalizowane (probe '
                'wyladowal poza composerem)", "suggested_uri": "kvm://' + KVM_URI_HOST + '/ui/query/locate", '
                '"suggested_payload": {"text": "Message", "role": "textbox"}, '
                '"prompt_improvement": "uzyj atspi role=textbox zamiast samego OCR do lokalizacji '
                'pola wiadomosci", "needs_new_capability": null}')}
        return {"ok": True, "model": model, "content": '{"pass": false, "reason": "tekst nie widoczny w czacie po probie"}'}

    goal.prepare_and_validate_for_signal_kvm = lambda **k: {
        "ok": True, "plan": [{"id": "focus", "uri": f"kvm://{KVM_URI_HOST}/window/command/focus", "payload": {}}],
        "executor_model": goal._llm_model(), "executor_twin_model": goal._llm_executor_twin_model()}
    goal._ensure_gui_ready_for_signal = lambda *a, **k: {"ok": True}
    goal._speak_on_node = lambda *a, **k: None
    goal._capture_lowres = lambda *a, **k: ("/tmp/ifuri229-lowres.png", None)
    goal._capture_quad = lambda *a, **k: ("/tmp/ifuri229-quad.png", None)
    goal._node_run = fake_node_run
    goal._llm_decide_next = fake_decide_next
    goal._llm_completion = fake_llm_completion
    return node_calls


def main(argv: list[str] | None = None) -> int:
    try:
        from urirun_connector_work import goal
    except Exception as exc:  # noqa: BLE001
        print(f"BŁĄD importu connectora work:// (goal.py) — {exc}\n"
              "Uruchom z katalogu examples/ (nie z korzenia repo — namespace shadow urirun/).")
        return 3

    node_calls = _install_mock(goal)
    # send_via_kvm domyślnie bierze szybką ścieżkę scripted (bez LLM); ten przykład
    # celowo ćwiczy triple-LLM tor z eskalacją, więc włączamy go jawnie.
    os.environ["SIGNAL_KVM_PREP"] = "1"

    print("== IFURI-229: executor -> validator -> twin -> validator -> teacher ==")
    print(f"executor={goal._llm_model()}  twin={goal._llm_executor_twin_model()}  "
          f"validator={goal._llm_validator_model()}  teacher={goal._llm_teacher_model()}\n")

    result = goal.send_via_kvm(recipient="TestOnlyLabel", text="tresc testowa (mock)",
                               ticket=None, node="lenovo")

    print(f"1) executor  ({result['executor_model']}) próbował, verify nie przeszedł")
    print(f"2) failover_triggered = {result['failover_triggered']}  "
          f"(twin {result['executor_twin_model']} przejął)")
    print(f"3) teacher_escalated  = {result['teacher_escalated']}")
    if result.get("teacher_improvement"):
        ti = result["teacher_improvement"]
        print(f"   teacher diagnoza: {ti.get('diagnosis')}")
        print(f"   teacher proponuje: {ti.get('suggested_uri')} payload={ti.get('suggested_payload')}")
        print(f"   prompt_improvement: {ti.get('prompt_improvement')}")
    print(f"4) inquiry:// dostał propozycję teachera jako artefakt: "
          f"{'inquiry://host/case/command/create' in node_calls}")
    print(f"\nresult.ok = {result['ok']}  (False = poprawnie zgłoszone jako niewykonane, "
          f"verify nigdy present=True w tym scenariuszu)")

    chain_worked = (
        result["failover_triggered"] is True
        and result["teacher_escalated"] is True
        and bool(result.get("teacher_improvement", {}).get("suggested_uri"))
        and "inquiry://host/case/command/create" in node_calls
    )
    if not chain_worked:
        print("\nBŁĄD: łańcuch eskalacji nie zadziałał zgodnie z oczekiwaniami.")
        return 1
    print("\n✓ Łańcuch eskalacji (executor→validator→twin→validator→teacher) zadziałał poprawnie.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
