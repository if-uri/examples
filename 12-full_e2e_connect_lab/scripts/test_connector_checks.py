from subprocess import CompletedProcess

import connector_checks


def test_emit_connector_bindings_uses_requested_module_and_output(monkeypatch, tmp_path):
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return CompletedProcess(args, 0, stdout='{"routes": []}\n', stderr="")

    monkeypatch.setattr(connector_checks, "BASE", tmp_path)
    monkeypatch.setattr(connector_checks, "run", fake_run)

    connector_checks.emit_connector_bindings("time-tools", "urirun_connector_time_tools")

    assert calls[0][:2] == ["python3", "-c"]
    assert "from urirun_connector_time_tools import urirun_bindings" in calls[0][2]
    assert (tmp_path / "time-tools-bindings.json").read_text() == '{"routes": []}\n'
