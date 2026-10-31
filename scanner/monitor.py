"""Siklus watchlist dan diff antar putaran. Tidak mengirim transaksi."""

from __future__ import annotations

from datetime import datetime, timezone

from scanner.chain import ChainFacts, Wave, format_wib
from scanner.config import ScanConfig
from scanner.models import NEXT_STEP, Post
from scanner.risk import is_severe

ACTIVE = {"new", "verified", "waiting_open", "open"}


def empty_state() -> dict:
    return {"items": {}, "seen_wave_contracts": [], "wave_rpc_error": False}


def _now_stamp(now: int) -> str:
    return datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _severe(flags: list[str]) -> bool:
    return is_severe(flags)


def _soon(item: dict, now: int, soon_seconds: int) -> bool:
    timestamp = item.get("open_time_unix")
    return isinstance(timestamp, int) and now < timestamp <= now + soon_seconds


def _actionable(item: dict) -> bool:
    return (
        item.get("status") == "open"
        and str(item.get("price_wei")) == "0"
        and not item.get("paused")
        and not item.get("sold_out")
        and not item.get("rpc_error")
        and not _severe(item.get("red_flags") or [])
    )


def classify_facts(facts: ChainFacts, *, sold_out_at: float, flags: list[str], now: int) -> tuple[str, str, bool]:
    sold_out = facts.progress is not None and facts.progress >= sold_out_at
    if facts.read_error and not facts.has_code:
        return "new", "cek on-chain gagal", False
    if not facts.has_code:
        return "skipped", "bytecode kosong", False
    if _severe(flags):
        return "skipped", "bendera merah", sold_out
    if sold_out:
        return "ended", "sold out atau progres melewati ambang", True
    if facts.paused:
        return "skipped", "paused", False
    if facts.price_wei is not None and facts.price_wei > 0:
        return "skipped", "berbayar", False
    if facts.open_time_unix and facts.open_time_unix > now:
        return "waiting_open", "menunggu waktu buka on-chain", False
    if facts.price_wei == 0:
        return "open", "gratis dan tidak sedang menunggu waktu buka", False
    if facts.mint_selectors or facts.name or facts.total_supply is not None:
        return "verified", "terbaca sebagian, harga atau waktu belum lengkap", False
    return "new", "belum cukup data on-chain", False


def build_item(facts: ChainFacts, post: Post | None, config: ScanConfig, now: int, flags: list[str], previous: dict | None) -> dict:
    if facts.read_error and previous:
        kept = dict(previous)
        kept["rpc_error"] = True
        kept["updated_at"] = _now_stamp(now)
        return kept
    status, reason, sold_out = classify_facts(facts, sold_out_at=config.sold_out_progress, flags=flags, now=now)
    item = {
        "status": status,
        "reason": reason,
        "price_wei": None if facts.price_wei is None else str(facts.price_wei),
        "paused": bool(facts.paused),
        "sold_out": sold_out,
        "open_time_unix": facts.open_time_unix,
        "open_time_wib": format_wib(facts.open_time_unix) if facts.open_time_unix else None,
        "progress": None if facts.progress is None else round(facts.progress, 4),
        "risk_score": 0,
        "red_flags": list(flags),
        "tweet_url": (post.url if post and post.url else None) or (previous or {}).get("tweet_url"),
        "rpc_error": bool(facts.read_error),
        "updated_at": _now_stamp(now),
        "alerted_opening_soon": False,
    }
    if previous and previous.get("open_time_unix") == item.get("open_time_unix"):
        item["alerted_opening_soon"] = bool(previous.get("alerted_opening_soon"))
    return item


def should_alert(previous: dict | None, item: dict, *, now: int, soon_seconds: int) -> tuple[bool, str]:
    if item.get("status") == "minted":
        return False, ""
    if item.get("rpc_error"):
        if previous and previous.get("rpc_error"):
            return False, ""
        return True, "rpc"
    if previous and previous.get("rpc_error") and _actionable(item):
        return True, "actionable"
    if previous is None:
        if _severe(item.get("red_flags") or []):
            return True, "warning"
        if _actionable(item):
            return True, "actionable"
        if item.get("status") == "waiting_open" and _soon(item, now, soon_seconds) and not item.get("alerted_opening_soon"):
            return True, "soon"
        return False, ""
    if str(previous.get("price_wei")) != str(item.get("price_wei")):
        return True, "actionable" if _actionable(item) else "status"
    if bool(item.get("paused")) and not previous.get("paused"):
        return True, "status"
    if item.get("sold_out") and not previous.get("sold_out"):
        return True, "status"
    if previous.get("status") != item.get("status"):
        if _actionable(item):
            return True, "actionable"
        if item.get("status") == "ended" and previous.get("status") in ACTIVE:
            return True, "status"
        if item.get("status") == "skipped" and previous.get("status") in ACTIVE and item.get("paused"):
            return True, "status"
        if _severe(item.get("red_flags") or []) and not _severe(previous.get("red_flags") or []):
            return True, "warning"
        return False, ""
    if item.get("status") == "waiting_open" and _soon(item, now, soon_seconds) and not previous.get("alerted_opening_soon"):
        return True, "soon"
    return False, ""


def summary_for(kind: str, address: str, item: dict) -> str:
    when = item.get("open_time_wib") or "waktu on-chain tidak terbaca"
    reason = item.get("reason") or item.get("status")
    flags = ", ".join(item.get("red_flags") or []) or "tidak ada"
    link = item.get("tweet_url") or "tanpa tautan"
    base = f"{address} — {reason}. WIB: {when}. Risiko: {flags}. Tautan: {link}."
    if kind == "actionable":
        return base + " " + NEXT_STEP
    if kind == "soon":
        return base + " Jadwalkan satu cek tambahan sebelum waktu itu, jangan andalkan grid saja."
    if kind == "warning":
        return base + " Jangan mint dan jangan connect."
    if kind == "rpc":
        return f"{address} — cek on-chain gagal. Coba RPC cadangan. Jangan menebak status."
    if kind == "status" and item.get("status") == "open" and not item.get("rpc_error"):
        return base + " " + NEXT_STEP
    return base


def wave_change(wave: Wave) -> dict:
    return {
        "kind": "wave",
        "summary": (
            f"{wave.contract} — gelombang {wave.mint_count} Transfer dari address(0), "
            f"panas {wave.distinct_callers} pemanggil. Sinyal baca, bukan izin. {NEXT_STEP}"
        ),
    }


def apply_minted(item: dict, address: str, minted: set[str]) -> dict:
    if address.lower() in {value.lower() for value in minted}:
        updated = dict(item)
        updated["status"] = "minted"
        updated["reason"] = "ditandai sudah dikerjakan"
        return updated
    return item
