"""Klien JSON-RPC baca-saja. Metode yang mengirim transaksi ditolak."""

from __future__ import annotations

import json

from scanner.http_util import HttpRequest, Transport

READONLY_METHODS = frozenset(
    {
        "eth_call",
        "eth_getCode",
        "eth_getStorageAt",
        "eth_getLogs",
        "eth_blockNumber",
        "eth_getTransactionByHash",
    }
)


class ReadOnlyError(RuntimeError):
    pass


class RpcError(RuntimeError):
    pass


def ensure_readonly(method: str) -> None:
    if method not in READONLY_METHODS:
        raise ReadOnlyError(f"metode tidak diizinkan: {method}")


class JsonRpcClient:
    def __init__(self, urls: list[str], transport: Transport) -> None:
        if not urls:
            raise RpcError("tidak ada URL RPC")
        self.urls = list(urls)
        self.transport = transport

    def call(self, method: str, params: list) -> object:
        ensure_readonly(method)
        last: Exception | None = None
        for url in self.urls:
            try:
                return self._once(url, method, params)
            except RpcError as exc:
                last = exc
                continue
        raise RpcError("semua RPC gagal") from last

    def _once(self, url: str, method: str, params: list) -> object:
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        request = HttpRequest(
            method="POST",
            url=url,
            headers={"content-type": "application/json", "accept": "application/json"},
            body=json.dumps(payload).encode("utf-8"),
        )
        try:
            response = self.transport.send(request)
        except OSError as exc:
            raise RpcError("gagal menghubungi RPC") from exc
        if response.status == 429 or response.status >= 500 or response.status == 0:
            raise RpcError(f"RPC HTTP {response.status}")
        if response.status >= 400:
            raise RpcError(f"RPC HTTP {response.status}")
        try:
            body = response.json()
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise RpcError("RPC bukan JSON") from exc
        if not isinstance(body, dict):
            raise RpcError("RPC bukan objek")
        if body.get("error"):
            if method == "eth_call":
                return None
            raise RpcError("RPC menolak pembacaan")
        return body.get("result")
