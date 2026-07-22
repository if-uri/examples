import json
import struct

import websocket_frames


class FakeSocket:
    def __init__(self, incoming=b""):
        self.incoming = bytearray(incoming)
        self.sent = b""

    def sendall(self, data):
        self.sent += data

    def recv(self, length):
        chunk = self.incoming[:length]
        del self.incoming[:length]
        return bytes(chunk)


def test_send_text_masks_payload(monkeypatch):
    sock = FakeSocket()
    monkeypatch.setattr(websocket_frames.os, "urandom", lambda _length: b"\x01\x02\x03\x04")

    websocket_frames.send_text(sock, "hello")

    assert sock.sent[:2] == b"\x81\x85"
    assert sock.sent[2:6] == b"\x01\x02\x03\x04"
    decoded = bytes(byte ^ sock.sent[2 + index % 4] for index, byte in enumerate(sock.sent[6:]))
    assert decoded == b"hello"


def test_recv_json_supports_extended_unmasked_payload():
    payload = json.dumps({"result": "x" * 130}).encode()
    frame = b"\x81\x7e" + struct.pack(">H", len(payload)) + payload

    assert websocket_frames.recv_json(FakeSocket(frame)) == {"result": "x" * 130}


def test_recv_exact_reports_closed_socket():
    try:
        websocket_frames.recv_exact(FakeSocket(), 1)
    except RuntimeError as exc:
        assert str(exc) == "websocket closed"
    else:
        raise AssertionError("expected websocket closure")
