"""Ekstrak alamat, URL, waktu sebutan, dan kata kunci dari posting. Tidak memanggil jaringan."""

from __future__ import annotations

import re
from datetime import datetime

from scanner.models import Extraction, Post

_ADDRESS = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
_URL = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)
_TIME = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?Z?\b"
    r"|\b\d{1,2}:\d{2}\b"
    r"|\b\d{1,2}\s*(?:menit|jam)\b"
    r"|\b(?:hari ini|besok|today|tomorrow)\b",
    re.IGNORECASE,
)
_TRAIL = ".,);]>"

_KEYWORDS = {
    "free": ("free mint", "freemint", "gratis", "gas only", "gas-only", "0 bnb", "fcfs"),
    "price": ("price", "harga", "mint price"),
    "whitelist": ("whitelist", "allowlist"),
    "phase": ("phase", "fase", "public sale", "presale"),
}


def _clean_url(url: str) -> str:
    return url.rstrip(_TRAIL)


def extract_post(post: Post, expand=None) -> Extraction:
    addresses: list[str] = []
    seen_addr: set[str] = set()
    for match in _ADDRESS.finditer(post.text):
        addr = match.group(0)
        if set(addr[2:].lower()) == {"0"}:
            continue
        key = addr.lower()
        if key not in seen_addr:
            seen_addr.add(key)
            addresses.append(addr)
    urls: list[str] = []
    seen_url: set[str] = set()
    raw_urls = list(post.extra_urls) + _URL.findall(post.text)
    for raw in raw_urls:
        url = _clean_url(raw)
        if expand is not None and _is_tco(url):
            expanded = expand(url)
            if expanded:
                url = expanded
        if url not in seen_url:
            seen_url.add(url)
            urls.append(url)
    times = []
    for match in _TIME.finditer(post.text):
        found = match.group(0)
        if found not in times:
            times.append(found)
    low = post.text.lower()
    keywords = [name for name, phrases in _KEYWORDS.items() if any(phrase in low for phrase in phrases)]
    return Extraction(addresses=addresses, urls=urls, times_mentioned=times, keywords=keywords)


def _is_tco(url: str) -> bool:
    from urllib.parse import urlparse

    host = (urlparse(url).hostname or "").lower()
    return host == "t.co"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
