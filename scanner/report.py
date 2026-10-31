"""Laporan Indonesian untuk manusia, plus JSON berkas lead."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from scanner.chain import format_wib
from scanner.models import NEXT_STEP, Lead

_HEX64 = re.compile(r"\b(?:0x)?[a-fA-F0-9]{64}\b")
_SECRET_ASSIGN = re.compile(
    r"(?i)\b(?:private[\s_-]*key|mnemonic|seed[\s_-]*phrase)\b\s*[:=]\s*\S+"
)

QUIET_MESSAGE = "Tidak ada yang baru. Jangan kirim pesan ke pengguna.\n"


def redact(text: str, limit: int = 240) -> str:
    cleaned = _SECRET_ASSIGN.sub("[rahasia disunting]", text)
    cleaned = _HEX64.sub("[hex disunting]", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned[:limit]


def lead_record(lead: Lead, rank: int) -> dict:
    facts = lead.chain
    return {
        "rank": rank,
        "tweet_id": lead.post.id,
        "tweet_url": lead.post.url,
        "author": lead.post.author,
        "followers": lead.post.followers,
        "contract": facts.address if facts else None,
        "status": lead.statuses,
        "risk_score": lead.risk_score,
        "red_flags": lead.red_flags,
        "open_time_wib": lead.open_time_wib,
        "progress": None if facts is None or facts.progress is None else round(facts.progress, 4),
        "price_wei": None if facts is None else facts.price_wei,
        "max_per_wallet": None if facts is None else facts.max_per_wallet,
        "paused": None if facts is None else facts.paused,
        "proxy": None if facts is None else facts.is_proxy,
        "mint_selectors": [] if facts is None else facts.mint_selectors,
        "keywords": lead.extraction.keywords,
        "urls": lead.extraction.urls,
        "times_mentioned": lead.extraction.times_mentioned,
        "snippet": redact(lead.post.text),
        "next_step": NEXT_STEP,
        "source": lead.post.source,
    }


def dumps_leads(leads: list[Lead], now: int) -> str:
    payload = {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Baca saja. Jangan auto-mint. " + NEXT_STEP,
        "leads": [lead_record(lead, index) for index, lead in enumerate(leads, start=1)],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_leads_md(leads: list[Lead]) -> str:
    lines = [
        "# Lead dari pemindaian (baca saja)",
        "",
        "Tidak ada transaksi yang dikirim.",
        f"Langkah berikut untuk setiap kandidat: {NEXT_STEP}",
        "",
    ]
    if not leads:
        lines.append("Tidak ada lead pada putaran ini.")
        lines.append("")
        return "\n".join(lines)
    for index, lead in enumerate(leads, start=1):
        contract = lead.chain.address if lead.chain else "tidak ada"
        lines.append(f"## {index}. Risiko {lead.risk_score} — {contract}")
        lines.append("")
        if lead.post.url:
            lines.append(f"- Tautan: {lead.post.url}")
        lines.append(f"- Status: {', '.join(lead.statuses) if lead.statuses else 'tidak ada'}")
        lines.append(f"- Waktu buka on-chain (WIB): {lead.open_time_wib or 'tidak terbaca'}")
        if lead.extraction.times_mentioned:
            lines.append(
                "- Waktu yang disebut di posting (bukan sumber kebenaran): "
                + ", ".join(lead.extraction.times_mentioned)
            )
        flags = ", ".join(lead.red_flags) if lead.red_flags else "tidak ada"
        lines.append(f"- Risiko: {flags}")
        if lead.chain and lead.chain.max_per_wallet is not None:
            lines.append(f"- Batas per dompet: {lead.chain.max_per_wallet}")
        if lead.chain and lead.chain.progress is not None:
            lines.append(f"- Progres: {lead.chain.progress:.1%}")
        lines.append(f"- Cuplikan: {redact(lead.post.text)}")
        lines.append(f"- Langkah berikut: {NEXT_STEP}")
        lines.append("")
    return "\n".join(lines)


def render_changes(changes: list[dict], *, cadence_minutes: int, per_run_cap: int, daily_cap: int | None, standing_permission: bool, active_window: str, timezone_name: str) -> str:
    if not changes:
        return QUIET_MESSAGE
    actionable = [item for item in changes if item["kind"] == "actionable"]
    in_quota = actionable[:per_run_cap]
    overflow = actionable[per_run_cap:]
    daily_note = (
        "belum ditetapkan — tanyakan, jangan mengarang"
        if daily_cap is None
        else str(daily_cap)
    )
    lines = [
        "# Perubahan pemantauan",
        "",
        f"Irama grid: tiap {cadence_minutes} menit, jendela {active_window} {timezone_name}.",
        f"Batas per putaran: {per_run_cap} mint gratis (langit-langit, bukan target). Batas harian: {daily_note}.",
        "Posting yang sudah ada di seen tidak diulang. Tidak ada transaksi.",
        NEXT_STEP,
        "",
    ]
    if standing_permission:
        lines.append("Izin tetap tercatat, tetapi tiap mint tetap satu pratinjau dan kata confirm. Jangan auto-mint.")
        lines.append("")
    else:
        lines.append("Belum ada izin tetap. Tanyakan dulu sebelum pratinjau mint.")
        lines.append("")
    _section(lines, "Boleh dipratinjau pada putaran ini", in_quota)
    _section(lines, "Melebihi batas per putaran — tunda", overflow)
    _section(lines, "Segera buka", [item for item in changes if item["kind"] == "soon"])
    _section(lines, "Perubahan status", [item for item in changes if item["kind"] == "status"])
    _section(lines, "Peringatan", [item for item in changes if item["kind"] == "warning"])
    _section(lines, "Gelombang dan panas", [item for item in changes if item["kind"] == "wave"])
    _section(lines, "Gangguan baca", [item for item in changes if item["kind"] == "rpc"])
    return "\n".join(lines).rstrip() + "\n"


def _section(lines: list[str], title: str, rows: list[dict]) -> None:
    if not rows:
        return
    lines.append(f"## {title}")
    lines.append("")
    for row in rows:
        lines.append(f"- {row['summary']}")
    lines.append("")


def open_label(timestamp: int | None) -> str | None:
    if not timestamp:
        return None
    return format_wib(timestamp)
