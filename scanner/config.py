"""Muat YAML konfigurasi. Token tidak pernah dibaca dari berkas ini."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

_FORBIDDEN_KEYS = {
    "bearer",
    "bearer_token",
    "x_bearer_token",
    "private_key",
    "mnemonic",
    "seed_phrase",
}


@dataclass
class ScanConfig:
    queries: list[str]
    accounts: list[str]
    exclude_retweets: bool
    max_results: int
    max_pages: int
    max_posts: int
    rpc_url: str
    fallback_rpc_urls: list[str] = field(default_factory=list)
    sold_out_progress: float = 0.999
    min_followers: int = 100
    new_account_days: int = 30
    cadence_minutes: int = 30
    active_window: str = "07:00-23:00"
    timezone: str = "Asia/Jakarta"
    opening_soon_minutes: int = 20
    per_run_cap: int = 5
    daily_cap: int | None = None
    standing_permission: bool = False
    wave_lookback_blocks: int = 300
    wave_min_mints: int = 3


def _reject_secret_keys(node: object) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key).lower() in _FORBIDDEN_KEYS:
                raise ValueError("config tidak boleh memuat rahasia; pakai environment")
            _reject_secret_keys(value)
    elif isinstance(node, list):
        for item in node:
            _reject_secret_keys(item)


def _http_url(value: object) -> str | None:
    text = str(value or "").strip()
    if text.startswith("https://") or text.startswith("http://"):
        return text
    return None


def load_config(path: Path) -> ScanConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("config harus berupa peta")
    _reject_secret_keys(raw)
    queries = raw.get("queries") or []
    if not isinstance(queries, list) or not all(isinstance(item, str) for item in queries):
        raise ValueError("queries harus daftar teks")
    accounts_raw = raw.get("accounts") or []
    if not isinstance(accounts_raw, list):
        raise ValueError("accounts harus daftar")
    accounts: list[str] = []
    for account in accounts_raw:
        name = str(account).strip().lstrip("@")
        if not name:
            continue
        if not name.replace("_", "").isalnum() or len(name) > 15:
            raise ValueError("nama akun tidak valid")
        accounts.append(name)
    chain = raw.get("chain") or {}
    thresholds = raw.get("thresholds") or {}
    monitoring = raw.get("monitoring") or {}
    farming = raw.get("farming") or {}
    rpc = _http_url(chain.get("rpc_url")) or "https://bsc-dataseed.binance.org/"
    env_rpc = _http_url(os.environ.get("BSC_RPC_URL", ""))
    if env_rpc:
        rpc = env_rpc
    fallbacks: list[str] = []
    for item in chain.get("fallback_rpc_urls") or []:
        url = _http_url(item)
        if url and url not in fallbacks and url != rpc:
            fallbacks.append(url)
    env_fallback = _http_url(os.environ.get("BSC_RPC_FALLBACK_URL", ""))
    if env_fallback and env_fallback not in fallbacks and env_fallback != rpc:
        fallbacks.insert(0, env_fallback)
    max_results = int(raw.get("max_results") or 10)
    daily_raw = farming.get("daily_cap", None)
    daily_cap = None if daily_raw in (None, "", "null") else int(daily_raw)
    per_run_raw = farming.get("per_run_cap", 5)
    per_run_cap = 5 if per_run_raw is None else max(0, int(per_run_raw))
    return ScanConfig(
        queries=[item.strip() for item in queries if item.strip()],
        accounts=accounts,
        exclude_retweets=bool(raw.get("exclude_retweets", True)),
        max_results=min(100, max(10, max_results)),
        max_pages=max(1, int(raw.get("max_pages") or 1)),
        max_posts=max(1, int(raw.get("max_posts") or 50)),
        rpc_url=rpc,
        fallback_rpc_urls=fallbacks,
        sold_out_progress=float(thresholds.get("sold_out_progress") or 0.999),
        min_followers=int(thresholds.get("min_followers") or 100),
        new_account_days=int(thresholds.get("new_account_days") or 30),
        cadence_minutes=max(1, int(monitoring.get("cadence_minutes") or 30)),
        active_window=str(monitoring.get("active_window") or "07:00-23:00"),
        timezone=str(monitoring.get("timezone") or "Asia/Jakarta"),
        opening_soon_minutes=max(1, int(monitoring.get("opening_soon_minutes") or 20)),
        per_run_cap=per_run_cap,
        daily_cap=daily_cap,
        standing_permission=bool(farming.get("standing_permission", False)),
        wave_lookback_blocks=max(1, int(monitoring.get("wave_lookback_blocks") or 300)),
        wave_min_mints=max(1, int(monitoring.get("wave_min_mints") or 3)),
    )
