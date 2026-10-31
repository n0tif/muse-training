"""Menjalankan pemindaian sekali dan pemantauan berulang. Keduanya hanya membaca."""

from __future__ import annotations

from scanner.chain import format_wib, inspect_contract, labels_for, read_waves
from scanner.config import ScanConfig
from scanner.extract import extract_post
from scanner.models import NEXT_STEP, ChainFacts, Lead, Post
from scanner.monitor import (
    apply_minted,
    build_item,
    empty_state,
    should_alert,
    summary_for,
    wave_change,
)
from scanner.report import render_changes
from scanner.risk import assess
from scanner.rpc import RpcError


def scan_posts(posts, rpc, config: ScanConfig, now: int) -> list[Lead]:
    leads: list[Lead] = []
    for post in posts:
        extraction = extract_post(post)
        targets = extraction.addresses or [None]
        for address in targets:
            facts = None
            if address:
                facts = inspect_contract(rpc, address, sold_out_at=config.sold_out_progress)
            flags, score, tier = assess(post, extraction, facts, config, now)
            open_time = format_wib(facts.open_time_unix) if facts and facts.open_time_unix else None
            leads.append(
                Lead(
                    post=post,
                    extraction=extraction,
                    chain=facts,
                    statuses=labels_for(facts, sold_out_at=config.sold_out_progress, now=now),
                    red_flags=flags,
                    risk_score=score,
                    open_time_wib=open_time,
                    tier=tier,
                )
            )
    leads.sort(key=lambda lead: (lead.tier, lead.risk_score, lead.post.id))
    return leads


def run_monitor(posts, rpc, config: ScanConfig, state: dict | None, seen_ids: set[str] | None, now: int, minted: set[str] | None = None) -> tuple[dict, set[str], str]:
    state = dict(state or empty_state())
    items = dict(state.get("items") or {})
    seen = set(seen_ids or [])
    minted = {item.lower() for item in (minted or set())}
    changes: list[dict] = []
    fresh = [post for post in posts if post.id not in seen]
    by_address: dict[str, Post | None] = {}
    touched_ids: set[str] = set()
    for post in fresh:
        extraction = extract_post(post)
        if not extraction.addresses:
            flags, _, _ = assess(post, extraction, None, config, now)
            if flags and _text_only_alert(flags):
                changes.append(
                    {
                        "kind": "warning",
                        "summary": (
                            f"Posting {post.id} tanpa alamat kontrak. "
                            + ", ".join(flags)
                            + f". Tautan: {post.url or 'tanpa tautan'}. Jangan menebak alamat. {NEXT_STEP}"
                        ),
                    }
                )
            seen.add(post.id)
            continue
        touched_ids.add(post.id)
        for address in extraction.addresses:
            by_address.setdefault(address.lower(), post)
    for address in list(items):
        by_address.setdefault(address.lower(), None)
    soon_seconds = config.opening_soon_minutes * 60
    for address, post in by_address.items():
        try:
            facts = inspect_contract(rpc, address, sold_out_at=config.sold_out_progress)
        except RpcError as exc:
            facts = _failed(address, str(exc))
        post_obj = post if isinstance(post, Post) else _stub_post(address, items.get(address))
        extraction = extract_post(post_obj)
        flags, score, _tier = assess(post_obj, extraction, facts, config, now)
        previous = items.get(address)
        if post is None and previous:
            flags = list(dict.fromkeys(list(previous.get("red_flags") or []) + flags))
        item = build_item(facts, post if isinstance(post, Post) else None, config, now, flags, previous)
        if post is None and previous and previous.get("tweet_url"):
            item["tweet_url"] = previous.get("tweet_url")
        item["risk_score"] = score
        item = apply_minted(item, address, minted)
        alert, kind = should_alert(previous, item, now=now, soon_seconds=soon_seconds)
        if alert and kind == "soon":
            item["alerted_opening_soon"] = True
        if alert:
            changes.append({"kind": kind, "summary": summary_for(kind, address, item)})
        items[address] = item
    seen.update(touched_ids)
    try:
        waves = read_waves(rpc, lookback_blocks=config.wave_lookback_blocks, min_mints=config.wave_min_mints)
        state["wave_rpc_error"] = False
    except RpcError:
        waves = []
        if not state.get("wave_rpc_error"):
            changes.append(
                {
                    "kind": "rpc",
                    "summary": "Gelombang tidak terbaca. Coba RPC cadangan. Jangan menebak panas.",
                }
            )
            state["wave_rpc_error"] = True
    seen_waves = set(state.get("seen_wave_contracts") or [])
    for wave in waves:
        key = wave.contract.lower()
        if key in seen_waves:
            continue
        seen_waves.add(key)
        changes.append(wave_change(wave))
        if key not in items:
            items[key] = {
                "status": "new",
                "reason": "gelombang baru, belum selesai diverifikasi",
                "price_wei": None,
                "paused": False,
                "sold_out": False,
                "open_time_unix": None,
                "open_time_wib": None,
                "progress": None,
                "risk_score": 0,
                "red_flags": [],
                "tweet_url": None,
                "rpc_error": False,
                "updated_at": "",
                "alerted_opening_soon": False,
            }
    state["items"] = items
    state["seen_wave_contracts"] = sorted(seen_waves)
    markdown = render_changes(
        changes,
        cadence_minutes=config.cadence_minutes,
        per_run_cap=config.per_run_cap,
        daily_cap=config.daily_cap,
        standing_permission=config.standing_permission,
        active_window=config.active_window,
        timezone_name=config.timezone,
    )
    return state, seen, markdown


def _failed(address: str, message: str):
    return inspect_contract_error(address, message)


def inspect_contract_error(address: str, message: str):
    from scanner.models import ChainFacts

    return ChainFacts(address=address, has_code=False, read_error=message[:160])


def _stub_post(address: str, previous: dict | None):
    from scanner.models import Post

    return Post(
        id=f"recheck-{address[-6:]}",
        text="",
        source="recheck",
        url=(previous or {}).get("tweet_url"),
    )


def _text_only_alert(flags: list[str]) -> bool:
    from scanner.risk import is_severe

    return is_severe(flags)
