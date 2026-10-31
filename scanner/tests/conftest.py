"""Pembantu tes. Alamat dirakit saat jalan, bukan ditulis utuh di berkas."""

from __future__ import annotations

import json

from scanner.http_util import HttpResponse
from scanner.rpc import ReadOnlyError, ensure_readonly


def fake_addr(pair: str = "ab") -> str:
    return "0x" + (pair * 20)


def word(value: int) -> str:
    return "0x" + value.to_bytes(32, "big").hex()


def abi_string(text: str) -> str:
    raw = text.encode()
    padded = raw + b"\x00" * ((32 - len(raw) % 32) % 32)
    blob = (32).to_bytes(32, "big") + len(raw).to_bytes(32, "big") + padded
    return "0x" + blob.hex()


class FakeRpc:
    def __init__(self, handler) -> None:
        self.handler = handler
        self.calls: list[tuple[str, list]] = []

    def call(self, method: str, params: list):
        ensure_readonly(method)
        self.calls.append((method, params))
        return self.handler(method, params)


class FakeTransport:
    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)
        self.sent = []

    def send(self, request):
        self.sent.append(request)
        if not self.responses:
            raise AssertionError("tidak ada balasan palsu tersisa")
        return self.responses.pop(0)


def response(status: int, payload: dict | None = None, headers: dict | None = None, body: bytes | None = None) -> HttpResponse:
    raw = body if body is not None else json.dumps(payload or {}).encode()
    return HttpResponse(status, headers or {}, raw)


def assert_readonly(method: str) -> None:
    try:
        ensure_readonly(method)
    except ReadOnlyError:
        return
    raise AssertionError("metode terlarang lolos")
