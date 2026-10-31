"""Pembacaan kontrak: eth_call, eth_getCode, eth_getStorageAt, dan log Transfer. Tanpa tanda tangan."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from scanner.keccak_util import eip1967_slot, keccak256, selector
from scanner.models import ChainFacts
from scanner.rpc import RpcError, ensure_readonly

WIB = ZoneInfo("Asia/Jakarta")

_VIEWS: tuple[tuple[str, str, str], ...] = (
    ("name", "name()", "string"),
    ("symbol", "symbol()", "string"),
    ("totalSupply", "totalSupply()", "uint"),
    ("maxSupply", "maxSupply()", "uint"),
    ("MAX_SUPPLY", "MAX_SUPPLY()", "uint"),
    ("price", "price()", "uint"),
    ("mintPrice", "mintPrice()", "uint"),
    ("cost", "cost()", "uint"),
    ("mintStart", "mintStart()", "uint"),
    ("startTime", "startTime()", "uint"),
    ("saleStart", "saleStart()", "uint"),
    ("paused", "paused()", "bool"),
    ("maxPerWallet", "maxPerWallet()", "uint"),
)
_MINT_SIGS = (
    "mint(uint256)",
    "mint(address)",
    "mint()",
    "claim()",
    "publicMint(uint256)",
    "publicMint()",
    "freeMint(uint256)",
    "freeMint()",
)
_OPEN_ORDER = ("mintStart", "startTime", "saleStart")


@dataclass
class Wave:
    contract: str
    mint_count: int
    distinct_callers: int


def format_wib(timestamp: int) -> str:
    moment = datetime.fromtimestamp(timestamp, WIB)
    return moment.strftime("%Y-%m-%d %H:%M WIB")


def _hex_bytes(value: object) -> bytes:
    if not isinstance(value, str):
        return b""
    text = value[2:] if value.startswith("0x") or value.startswith("0X") else value
    if not text:
        return b""
    if len(text) % 2:
        text = "0" + text
    try:
        return bytes.fromhex(text)
    except ValueError:
        return b""


def decode_uint(data: object) -> int | None:
    raw = _hex_bytes(data)
    if len(raw) < 32:
        return None
    return int.from_bytes(raw[:32], "big")


def decode_string(data: object) -> str | None:
    raw = _hex_bytes(data)
    if len(raw) < 64:
        return None
    offset = int.from_bytes(raw[:32], "big")
    if offset < 0 or offset + 32 > len(raw):
        return None
    length = int.from_bytes(raw[offset : offset + 32], "big")
    start = offset + 32
    if length < 0 or start + length > len(raw):
        return None
    return raw[start : start + length].decode("utf-8", "replace")


def _call_view(rpc, address: str, signature: str) -> object:
    ensure_readonly("eth_call")
    data = "0x" + selector(signature).hex()
    try:
        return rpc.call("eth_call", [{"to": address, "data": data}, "latest"])
    except RpcError:
        raise
    except Exception:
        return None


def _selectors_in(bytecode: bytes) -> list[str]:
    found = []
    for signature in _MINT_SIGS:
        if selector(signature) in bytecode:
            found.append(signature)
    return found


def inspect_contract(rpc, address: str, *, sold_out_at: float) -> ChainFacts:
    try:
        code_hex = rpc.call("eth_getCode", [address, "latest"])
    except RpcError as exc:
        return ChainFacts(address=address, has_code=False, read_error=str(exc)[:160])
    code = _hex_bytes(code_hex)
    facts = ChainFacts(address=address, has_code=len(code) > 0)
    if not facts.has_code:
        return facts
    slot = "0x" + eip1967_slot("eip1967.proxy.implementation").hex()
    try:
        stored = rpc.call("eth_getStorageAt", [address, slot, "latest"])
    except RpcError as exc:
        facts.read_error = str(exc)[:160]
        return facts
    word = _hex_bytes(stored).rjust(32, b"\x00")[-32:]
    impl = word[-20:]
    if word[:12] == b"\x00" * 12 and impl != b"\x00" * 20:
        facts.is_proxy = True
        facts.implementation = "0x" + impl.hex()
        try:
            impl_code = _hex_bytes(rpc.call("eth_getCode", [facts.implementation, "latest"]))
        except RpcError:
            impl_code = b""
        code = code + impl_code
    views: dict[str, object] = {}
    targets = [address]
    if facts.implementation:
        targets.append(facts.implementation)
    for key, signature, kind in _VIEWS:
        if key in views:
            continue
        decoded = None
        for target in targets:
            try:
                raw = _call_view(rpc, target, signature)
            except RpcError as exc:
                facts.read_error = str(exc)[:160]
                return facts
            if raw in (None, "0x", "0X"):
                continue
            if kind == "string":
                decoded = decode_string(raw)
            elif kind == "bool":
                number = decode_uint(raw)
                decoded = None if number is None else bool(number)
            else:
                decoded = decode_uint(raw)
            if decoded is not None:
                break
        if decoded is not None:
            views[key] = decoded
    facts.name = views.get("name") if isinstance(views.get("name"), str) else None
    facts.symbol = views.get("symbol") if isinstance(views.get("symbol"), str) else None
    supply = views.get("totalSupply")
    facts.total_supply = supply if isinstance(supply, int) else None
    max_candidates = [views.get("maxSupply"), views.get("MAX_SUPPLY")]
    max_values = [item for item in max_candidates if isinstance(item, int) and item > 0]
    facts.max_supply = max(max_values) if max_values else None
    prices = [views[key] for key in ("price", "mintPrice", "cost") if isinstance(views.get(key), int)]
    facts.price_wei = max(prices) if prices else None
    for key in _OPEN_ORDER:
        value = views.get(key)
        if isinstance(value, int) and value > 0:
            facts.open_time_unix = value
            break
    if isinstance(views.get("paused"), bool):
        facts.paused = views["paused"]
    if isinstance(views.get("maxPerWallet"), int):
        facts.max_per_wallet = views["maxPerWallet"]
    facts.mint_selectors = _selectors_in(code)
    facts.has_withdraw_selector = selector("withdraw()") in code
    if facts.total_supply is not None and facts.max_supply:
        facts.progress = facts.total_supply / facts.max_supply
    if sold_out_at < 0:
        sold_out_at = 0.999
    return facts


def labels_for(facts: ChainFacts | None, *, sold_out_at: float, now: int) -> list[str]:
    if facts is None:
        return ["tanpa alamat kontrak"]
    if facts.read_error and not facts.has_code:
        return ["cek on-chain gagal"]
    if not facts.has_code:
        return ["bytecode kosong"]
    labels: list[str] = []
    if facts.is_proxy:
        labels.append("proxy")
    if facts.price_wei is None:
        labels.append("harga tidak terbaca")
    elif facts.price_wei == 0:
        labels.append("gratis (harga 0)")
    else:
        labels.append("berbayar")
    if facts.progress is not None and facts.progress >= sold_out_at:
        labels.append("sold out")
    if facts.paused:
        labels.append("paused")
    if facts.open_time_unix and facts.open_time_unix > now:
        labels.append("belum buka")
    elif facts.open_time_unix:
        labels.append("waktu buka on-chain sudah lewat")
    if facts.max_per_wallet is not None:
        labels.append(f"batas per dompet {facts.max_per_wallet}")
    unknown = (
        not facts.mint_selectors
        and facts.name is None
        and facts.total_supply is None
        and facts.price_wei is None
    )
    if unknown:
        labels.append("tidak dikenal")
    if facts.mint_selectors:
        labels.append("ada selector mint")
    return labels


def read_waves(rpc, *, lookback_blocks: int, min_mints: int) -> list[Wave]:
    ensure_readonly("eth_getLogs")
    block_hex = rpc.call("eth_blockNumber", [])
    if not isinstance(block_hex, str):
        raise RpcError("nomor blok tidak terbaca")
    latest = int(block_hex, 16)
    start = max(0, latest - lookback_blocks)
    topic = "0x" + keccak256(b"Transfer(address,address,uint256)").hex()
    zero_topic = "0x" + ("00" * 32)
    logs = rpc.call(
        "eth_getLogs",
        [
            {
                "fromBlock": hex(start),
                "toBlock": hex(latest),
                "topics": [topic, zero_topic],
            }
        ],
    )
    if not isinstance(logs, list):
        return []
    grouped: dict[str, list[dict]] = {}
    for item in logs:
        if not isinstance(item, dict):
            continue
        contract = str(item.get("address") or "")
        if contract:
            grouped.setdefault(contract.lower(), []).append(item)
    waves: list[Wave] = []
    for contract, rows in grouped.items():
        if len(rows) < min_mints:
            continue
        tx_hashes = []
        for row in rows:
            txh = row.get("transactionHash")
            if isinstance(txh, str) and txh not in tx_hashes:
                tx_hashes.append(txh)
        callers: set[str] = set()
        for txh in tx_hashes[:15]:
            try:
                tx = rpc.call("eth_getTransactionByHash", [txh])
            except RpcError:
                tx = None
            if isinstance(tx, dict) and isinstance(tx.get("from"), str):
                callers.add(tx["from"].lower())
        heat = len(callers) if callers else len(tx_hashes)
        waves.append(Wave(contract=contract, mint_count=len(rows), distinct_callers=heat))
    waves.sort(key=lambda item: (-item.distinct_callers, -item.mint_count, item.contract))
    return waves
