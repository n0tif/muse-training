"""Antarmuka baris perintah: scan sekali, atau monitor yang hanya menulis perubahan."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from scanner.config import ScanConfig, load_config
from scanner.engine import run_monitor, scan_posts
from scanner.http_util import UrllibTransport
from scanner.report import dumps_leads, render_leads_md
from scanner.rpc import JsonRpcClient
from scanner.sources import SourceError, XSearchClient, fetch_api_posts, load_posts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pemindai posting X yang hanya membaca. Tidak mengirim transaksi.")
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default="scanner/config.example.yaml")
    common.add_argument("--input", help="Berkas posts.json atau teks tempelan dari browser. Jika diisi, API tidak dipanggil.")
    common.add_argument("--seen", default="state/seen.json")
    scan = sub.add_parser("scan", parents=[common], help="Satu putaran, tulis leads.json dan leads.md")
    scan.add_argument("--out", default="out")
    monitor = sub.add_parser("monitor", parents=[common], help="Diff watchlist, tulis hanya perubahan")
    monitor.add_argument("--watchlist", default="state/watchlist.json")
    monitor.add_argument("--decisions", default="state/decisions.json")
    monitor.add_argument("--out", default="out/changes.md")
    args = parser.parse_args(argv)
    try:
        config = load_config(Path(args.config))
        posts = _load_posts(args.input, config)
    except (OSError, ValueError, SourceError) as exc:
        print(str(exc))
        return 2
    now = int(time.time())
    rpc = JsonRpcClient([config.rpc_url, *config.fallback_rpc_urls], UrllibTransport())
    seen_path = Path(args.seen)
    seen = _load_seen(seen_path)
    if args.command == "scan":
        leads = scan_posts(posts, rpc, config, now)
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "leads.json").write_text(dumps_leads(leads, now), encoding="utf-8")
        (out / "leads.md").write_text(render_leads_md(leads), encoding="utf-8")
        _save_seen(seen_path, seen | {post.id for post in posts})
        return 0
    watch_path = Path(args.watchlist)
    state = _load_json(watch_path, {"items": {}, "seen_wave_contracts": [], "wave_rpc_error": False})
    minted = _minted(Path(args.decisions))
    state, seen_after, markdown = run_monitor(posts, rpc, config, state, seen, now, minted)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown, encoding="utf-8")
    _save_json(watch_path, state)
    _save_seen(seen_path, seen_after)
    return 0


def _load_posts(path: str | None, config: ScanConfig):
    if path:
        return load_posts(Path(path))
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token:
        raise SourceError(
            "Tidak ada sumber posting. Isi --input dari browser, atau X_BEARER_TOKEN. "
            "Kalau browser logout, berhenti dan beri tahu pengguna. Jangan menebak."
        )
    client = XSearchClient(token, UrllibTransport())
    return fetch_api_posts(config, client)


def _load_seen(path: Path) -> set[str]:
    data = _load_json(path, {"ids": []})
    return {str(item) for item in data.get("ids") or []}


def _save_seen(path: Path, seen: set[str]) -> None:
    _save_json(path, {"ids": sorted(seen)})


def _minted(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = _load_json(path, {})
    return {str(item) for item in data.get("minted") or []}


def _load_json(path: Path, default: dict) -> dict:
    if not path.is_file():
        return dict(default)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else dict(default)


def _save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
