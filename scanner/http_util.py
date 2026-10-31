"""HTTP kecil di atas urllib. Transport bisa diganti di tes, tanpa jaringan."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> object:
        return json.loads(self.body.decode("utf-8"))


@dataclass
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, str] | None = None
    body: bytes | None = None


class Transport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class UrllibTransport:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def send(self, request: HttpRequest) -> HttpResponse:
        url = request.url
        if request.params:
            url = url + "?" + urlencode(request.params)
        req = Request(url, data=request.body, method=request.method.upper())
        for key, value in request.headers.items():
            req.add_header(key, value)
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw_headers = {key.lower(): value for key, value in response.headers.items()}
                return HttpResponse(response.status, raw_headers, response.read())
        except HTTPError as exc:
            raw_headers = {key.lower(): value for key, value in exc.headers.items()}
            return HttpResponse(exc.code, raw_headers, exc.read())
