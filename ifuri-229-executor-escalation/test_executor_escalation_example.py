# Author: Tom Sapletta · Part of the ifURI solution.
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run  # noqa: E402
from urirun_connector_work.signal_kvm import KVM_URI_HOST  # noqa: E402


def test_ifuri229_escalation_chain_reaches_teacher(capsys):
    rc = run.main([])
    out = capsys.readouterr().out

    assert rc == 0
    assert "failover_triggered = True" in out
    assert "teacher_escalated  = True" in out
    assert f"kvm://{KVM_URI_HOST}/ui/query/locate" in out
    assert "inquiry:// dostał propozycję teachera jako artefakt: True" in out
    assert "Łańcuch eskalacji" in out and "zadziałał poprawnie" in out
