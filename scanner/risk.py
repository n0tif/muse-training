"""Skor risiko dari teks posting dan hasil baca on-chain. Tidak mengirim apa pun."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from scanner.config import ScanConfig
from scanner.extract import parse_time
from scanner.models import ChainFacts, Extraction, Post

_OFFICIAL_HOSTS = {"bscscan.com", "etherscan.io", "x.com", "twitter.com"}
_STEMS = ("bscscan", "etherscan", "opensea", "metamask", "walletconnect")
_FREE_WORDS = ("free mint", "freemint", "gratis", "gas only", "gas-only", "0 bnb", "fcfs")


def host_warning(url: str) -> str | None:
    host = (urlparse(url).hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None
    if host.startswith("xn--"):
        return "domain meniru situs resmi"
    if host in _OFFICIAL_HOSTS:
        return None
    for stem in _STEMS:
        if stem in host:
            return "domain meniru situs resmi"
    return None


def text_flags(text: str) -> list[str]:
    low = text.lower()
    flags: list[str] = []
    compact = low.replace(" ", "")
    if "setapprovalforall" in compact or "approve all" in low or "approval semua" in low:
        flags.append("minta setApprovalForAll")
    if "connect wallet" in low or "hubungkan dompet" in low or "scan qr" in low or "kode qr" in low:
        flags.append("minta QR atau connect wallet")
    if any(phrase in low for phrase in ("send to receive", "kirim supaya", "kirim dulu", "kirim x")):
        flags.append("minta kirim supaya dapat")
    if any(phrase in low for phrase in ("dm me", "kirim dm", "dm untuk", "lewat dm")):
        flags.append("minta DM")
    if any(phrase in low for phrase in ("segera", "menit lagi", "last chance", "jangan tanya", "hurry")):
        flags.append("urgensi")
    return flags


def _says_free(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in _FREE_WORDS)


def _account_flags(post: Post, config: ScanConfig, now: int) -> list[str]:
    flags: list[str] = []
    if post.followers is not None and post.followers < config.min_followers:
        flags.append("pengikut sedikit")
    created = parse_time(post.account_created_at)
    if created is not None:
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (datetime.fromtimestamp(now, timezone.utc) - created).total_seconds() / 86400
        if age_days < config.new_account_days:
            flags.append("akun baru")
    return flags


def assess(post: Post, extraction: Extraction, facts: ChainFacts | None, config: ScanConfig, now: int) -> tuple[list[str], int, int]:
    flags = text_flags(post.text)
    flags.extend(_account_flags(post, config, now))
    for url in extraction.urls:
        warning = host_warning(url)
        if warning and warning not in flags:
            flags.append(warning)
    if facts and facts.has_withdraw_selector:
        flags.append("petunjuk withdraw")
    if facts and _says_free(post.text):
        if facts.price_wei is not None and facts.price_wei > 0:
            flags.append("disebut gratis tetapi harga bukan 0")
        elif facts.price_wei is None:
            flags.append("disebut gratis tetapi harga tidak terbaca")
    if facts and facts.has_code:
        unknown = (
            not facts.mint_selectors
            and facts.name is None
            and facts.total_supply is None
            and facts.price_wei is None
        )
        if unknown:
            flags.append("antarmuka tidak dikenal")
    weights = {
        "disebut gratis tetapi harga bukan 0": 35,
        "minta setApprovalForAll": 40,
        "minta QR atau connect wallet": 40,
        "domain meniru situs resmi": 30,
        "minta kirim supaya dapat": 40,
        "minta DM": 25,
        "petunjuk withdraw": 15,
        "urgensi": 10,
        "pengikut sedikit": 10,
        "akun baru": 10,
        "antarmuka tidak dikenal": 10,
        "disebut gratis tetapi harga tidak terbaca": 10,
    }
    score = min(100, sum(weights.get(flag, 0) for flag in flags))
    sold = bool(facts and facts.progress is not None and facts.progress >= config.sold_out_progress)
    if facts is None or not facts.has_code:
        tier = 3
    elif sold or facts.paused or (facts.price_wei is not None and facts.price_wei > 0):
        tier = 2
    elif facts.price_wei == 0 and not (facts.open_time_unix and facts.open_time_unix > now):
        tier = 0
    else:
        tier = 1
    return flags, score, tier


def is_severe(flags: list[str]) -> bool:
    needles = (
        "disebut gratis tetapi harga bukan 0",
        "minta setApprovalForAll",
        "minta QR atau connect wallet",
        "domain meniru situs resmi",
        "minta kirim supaya dapat",
        "minta DM",
    )
    return any(flag in needles for flag in flags)
