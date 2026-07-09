from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("observe", HERE / "observe.py")
observe = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(observe)


class FakeClient:
    base = "http://node.example"

    def routes(self):
        return [{"uri": "screen://laptop/portal/query/capture"}]

    def run(self, uri, payload, timeout=60):
        assert uri == "screen://laptop/portal/query/capture"
        assert payload == {"base64": True}
        assert timeout == 60
        return {
            "ok": True,
            "result": {
                "value": {
                    "ok": True,
                    "bytes": 3,
                    "base64": base64.b64encode(b"png").decode(),
                }
            },
        }


def test_read_only_gate_allows_queries():
    observe.assert_read_only("screen://laptop/portal/query/capture")
    observe.assert_read_only("browser://laptop/cdp/page/query/screenshot")


def test_read_only_gate_refuses_social_writes():
    blocked = [
        "linkedin://post/command/publish",
        "browser://laptop/kvm/input/command/type",
        "social://linkedin.com/message/command/send",
        "browser://laptop/page/form/command/submit",
    ]
    for uri in blocked:
        try:
            observe.assert_read_only(uri)
        except PermissionError:
            pass
        else:
            raise AssertionError(f"expected read-only gate to refuse {uri}")


def test_observe_capture_without_model(monkeypatch):
    monkeypatch.setattr(observe, "MODEL", None)

    out = observe.observe(FakeClient())

    assert out == {
        "ok": True,
        "captured_bytes": 3,
        "note": "set LLM_MODEL (vision) to analyse the image",
    }
