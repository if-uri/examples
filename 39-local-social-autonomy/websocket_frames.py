"""Minimal WebSocket text-frame codec shared by the local CDP clients."""

from __future__ import annotations

import json
import os
import socket
import struct
from typing import Any


def send_text(sock: socket.socket, text: str) -> None:
    payload = text.encode("utf-8")
    mask = os.urandom(4)
    header = bytearray([0x81])
    length = len(payload)
    if length < 126:
        header.append(0x80 | length)
    elif length < 65536:
        header.append(0x80 | 126)
        header += struct.pack(">H", length)
    else:
        header.append(0x80 | 127)
        header += struct.pack(">Q", length)
    header += mask
    sock.sendall(
        bytes(header)
        + bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    )


def recv_exact(sock: socket.socket, length: int) -> bytes:
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk:
            raise RuntimeError("websocket closed")
        data += chunk
    return data


def recv_json(sock: socket.socket) -> dict[str, Any]:
    head = recv_exact(sock, 2)
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack(">H", recv_exact(sock, 2))[0]
    elif length == 127:
        length = struct.unpack(">Q", recv_exact(sock, 8))[0]
    if head[1] & 0x80:
        mask = recv_exact(sock, 4)
        payload = bytes(
            byte ^ mask[index % 4]
            for index, byte in enumerate(recv_exact(sock, length))
        )
    else:
        payload = recv_exact(sock, length)
    return json.loads(payload.decode("utf-8", "replace"))
