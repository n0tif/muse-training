"""Bentuk data bersama. Tidak ada bidang kunci atau tanda tangan."""

from __future__ import annotations

from dataclasses import dataclass, field


NEXT_STEP = "Pratinjau lalu tunggu konfirmasi user. Jangan auto-mint."


@dataclass
class Post:
    id: str
    text: str
    source: str
    url: str | None = None
    author: str | None = None
    followers: int | None = None
    account_created_at: str | None = None
    created_at: str | None = None
    extra_urls: list[str] = field(default_factory=list)


@dataclass
class Extraction:
    addresses: list[str]
    urls: list[str]
    times_mentioned: list[str]
    keywords: list[str]


@dataclass
class ChainFacts:
    address: str
    has_code: bool
    is_proxy: bool = False
    implementation: str | None = None
    name: str | None = None
    symbol: str | None = None
    total_supply: int | None = None
    max_supply: int | None = None
    price_wei: int | None = None
    open_time_unix: int | None = None
    paused: bool | None = None
    max_per_wallet: int | None = None
    mint_selectors: list[str] = field(default_factory=list)
    has_withdraw_selector: bool = False
    progress: float | None = None
    read_error: str | None = None


@dataclass
class Lead:
    post: Post
    extraction: Extraction
    chain: ChainFacts | None
    statuses: list[str]
    red_flags: list[str]
    risk_score: int
    open_time_wib: str | None
    tier: int

    @property
    def next_step(self) -> str:
        return NEXT_STEP
