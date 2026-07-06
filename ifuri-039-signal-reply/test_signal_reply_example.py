# Author: Tom Sapletta · Part of the ifURI solution.
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402


def _seed(tmp_path, monkeypatch, msgs):
    monkeypatch.setenv("SIGNAL_CLI_MOCK", "1")
    monkeypatch.setenv("SIGNAL_OUTBOX", str(tmp_path / "out.json"))
    inbox = tmp_path / "in.json"
    inbox.write_text(json.dumps(msgs), encoding="utf-8")
    monkeypatch.setenv("SIGNAL_INBOX", str(inbox))


def test_ifuri039_replies_to_last_and_verifies(tmp_path, monkeypatch, capsys):
    _seed(tmp_path, monkeypatch, [
        {"from": "+48-a", "message": "Cześć", "at": 1},
        {"from": "+48-kontakt-lenovo", "message": "Możesz potwierdzić?", "at": 2},
    ])
    rc = run.main([])
    out = capsys.readouterr().out
    assert rc == 0                                      # verify postcondition held
    assert "OK, potwierdzam." in out                   # default reply body used
    assert "+48-kontakt-lenovo" in out                 # replied to LAST sender

    # verify independently: reply landed in that thread's outbox
    from urirun_connector_signal import core
    lst = core.messages_query_list(to="+48-kontakt-lenovo")
    assert lst["count"] == 1 and lst["messages"][0]["message"] == "OK, potwierdzam."


def test_ifuri039_empty_inbox_is_blocked_not_faked(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, [])
    assert run.main([]) == 2                            # honest BLOCKED, no fabricated send


def test_ifuri039_unlinked_escalates_to_human(tmp_path, monkeypatch, capsys):
    # signal-cli nieobecny (_mock) + pusty inbox = fizyczny blocker → koperta actor:human,
    # nie cicha awaria: pętla/reaper ma traktować to jako human-task, nie retry.
    _seed(tmp_path, monkeypatch, [])                    # _seed ustawia SIGNAL_CLI_MOCK=1
    monkeypatch.setenv("URIRUN_NODE", "lenovo")
    rc = run.main([])
    out = capsys.readouterr().out
    assert rc == 2
    assert "ESCALATE actor:human" in out
    esc = json.loads(out[out.index("{"):])              # koperta jest parsowalna maszynowo
    assert esc["humanEscalation"] is True and esc["kind"] == "human-task"
    assert esc["node"] == "lenovo" and "signal-cli link" in esc["command"]
