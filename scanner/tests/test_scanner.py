"""Tes tanpa jaringan untuk ekstraksi, rantai, API palsu, dan pemantauan."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scanner.chain import decode_string, inspect_contract, read_waves
from scanner.config import load_config
from scanner.engine import run_monitor, scan_posts
from scanner.extract import extract_post
from scanner.keccak_util import eip1967_slot, selector
from scanner.models import NEXT_STEP, Post
from scanner.report import QUIET_MESSAGE, redact, render_changes
from scanner.rpc import JsonRpcClient, RpcError
from scanner.sources import XSearchClient, load_posts, search_queries
from scanner.tests.conftest import FakeRpc, FakeTransport, abi_string, fake_addr, response, word


def _config(tmp_path: Path, extra: str = "") -> object:
    path = tmp_path / "config.yaml"
    path.write_text(
        "queries:\n  - free mint\naccounts:\n  - akun_contoh\n" + extra,
        encoding="utf-8",
    )
    return load_config(path)


def test_keccak_known_selectors():
    assert selector("mint(uint256)").hex() == "a0712d68"
    assert selector("mint()").hex() == "1249c58b"
    assert selector("claim()").hex() == "4e71d92d"
    assert eip1967_slot("eip1967.proxy.implementation").hex().startswith("360894a1")


def test_defaults_are_thirty_minutes_and_five(tmp_path):
    config = _config(tmp_path)
    assert config.cadence_minutes == 30
    assert config.per_run_cap == 5
    assert config.daily_cap is None
    assert config.active_window == "07:00-23:00"
    assert config.timezone == "Asia/Jakarta"


def test_config_rejects_secret_key(tmp_path):
    path = tmp_path / "bad.yaml"
    secret_key = "private_" + "key"
    path.write_text(f"queries: []\n{secret_key}: rahasia\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(path)


def test_extract_address_url_time_and_keywords():
    address = fake_addr("12")
    post = Post(
        id="p1",
        text=f"free mint jam 20:00 gas only {address} https://t.co/abcd",
        source="file",
        extra_urls=["https://t.co/abcd"],
    )
    found = extract_post(post, expand=lambda url: "https://proyek-contoh.example/mint")
    assert found.addresses == [address]
    assert "https://proyek-contoh.example/mint" in found.urls
    assert "20:00" in found.times_mentioned
    assert "free" in found.keywords


def test_extract_skips_zero_address():
    post = Post(id="z", text="mint 0x" + ("0" * 40), source="file")
    assert extract_post(post).addresses == []


def test_chain_reads_free_open_contract():
    address = fake_addr("34")
    mint = "0x" + selector("mint(uint256)").hex()

    def handler(method, params):
        if method == "eth_getCode":
            return "0x63" + mint[2:]
        if method == "eth_getStorageAt":
            return "0x" + ("00" * 32)
        data = params[0]["data"]
        if data == "0x" + selector("name()").hex():
            return abi_string("Contoh")
        if data == "0x" + selector("totalSupply()").hex():
            return word(10)
        if data == "0x" + selector("maxSupply()").hex():
            return word(100)
        if data == "0x" + selector("price()").hex():
            return word(0)
        if data == "0x" + selector("maxPerWallet()").hex():
            return word(1)
        if data == "0x" + selector("paused()").hex():
            return word(0)
        return None

    facts = inspect_contract(FakeRpc(handler), address, sold_out_at=0.999)
    assert facts.has_code
    assert facts.name == "Contoh"
    assert facts.price_wei == 0
    assert facts.max_per_wallet == 1
    assert facts.progress == pytest.approx(0.1)
    assert "mint(uint256)" in facts.mint_selectors
    assert not facts.is_proxy
    assert decode_string(abi_string("Contoh")) == "Contoh"


def test_chain_flags_proxy_paid_and_sold_out():
    address = fake_addr("56")
    impl = fake_addr("78")

    def handler(method, params):
        if method == "eth_getCode":
            return "0x60"
        if method == "eth_getStorageAt":
            return "0x" + ("00" * 12) + impl[2:]
        data = params[0]["data"]
        if data == "0x" + selector("price()").hex():
            return word(5)
        if data == "0x" + selector("totalSupply()").hex():
            return word(999)
        if data == "0x" + selector("maxSupply()").hex():
            return word(1000)
        return None

    facts = inspect_contract(FakeRpc(handler), address, sold_out_at=0.999)
    assert facts.is_proxy
    assert facts.implementation == impl
    assert facts.price_wei == 5
    assert facts.progress == pytest.approx(0.999)


def test_waves_count_distinct_callers():
    contract = fake_addr("9a")
    caller_a = fake_addr("ab")
    caller_b = fake_addr("cd")
    topic = "0x" + __import__("scanner.keccak_util", fromlist=["keccak256"]).keccak256(
        b"Transfer(address,address,uint256)"
    ).hex()
    zero = "0x" + ("00" * 32)

    def tx(caller: str) -> dict:
        return {"from": caller}

    logs = [
        {"address": contract, "topics": [topic, zero, "0x" + ("11" * 32)], "transactionHash": "0x" + ("aa" * 32)},
        {"address": contract, "topics": [topic, zero, "0x" + ("22" * 32)], "transactionHash": "0x" + ("bb" * 32)},
        {"address": contract, "topics": [topic, zero, "0x" + ("33" * 32)], "transactionHash": "0x" + ("cc" * 32)},
    ]
    tx_map = {
        "0x" + ("aa" * 32): tx(caller_a),
        "0x" + ("bb" * 32): tx(caller_a),
        "0x" + ("cc" * 32): tx(caller_b),
    }

    def handler(method, params):
        if method == "eth_blockNumber":
            return hex(1000)
        if method == "eth_getLogs":
            return logs
        if method == "eth_getTransactionByHash":
            return tx_map[params[0]]
        return None

    waves = read_waves(FakeRpc(handler), lookback_blocks=20, min_mints=3)
    assert len(waves) == 1
    assert waves[0].mint_count == 3
    assert waves[0].distinct_callers == 2


def test_rpc_failover_and_readonly(tmp_path):
    calls = []

    class Transport:
        def send(self, request):
            calls.append(request.url)
            if request.url.endswith("mati"):
                from scanner.http_util import HttpResponse

                return HttpResponse(500, {}, b"{}")
            body = json.dumps({"jsonrpc": "2.0", "id": 1, "result": "0x1"}).encode()
            from scanner.http_util import HttpResponse

            return HttpResponse(200, {}, body)

    client = JsonRpcClient(["https://rpc.example/mati", "https://rpc.example/hidup"], Transport())
    assert client.call("eth_blockNumber", []) == "0x1"
    assert calls == ["https://rpc.example/mati", "https://rpc.example/hidup"]
    with pytest.raises(Exception):
        client.call("eth_sendTransaction", [])


def test_x_client_backs_off_and_hides_token():
    slept = []
    token = "token-contoh-bukan-rahasia-sungguhan"
    ok = {
        "data": [
            {
                "id": "100",
                "text": "free mint",
                "author_id": "7",
                "created_at": "2026-10-31T01:00:00Z",
            }
        ],
        "includes": {
            "users": [
                {
                    "id": "7",
                    "username": "akun_contoh",
                    "created_at": "2020-01-01T00:00:00Z",
                    "public_metrics": {"followers_count": 20},
                }
            ]
        },
        "meta": {},
    }
    transport = FakeTransport(
        [
            response(429, {}, {"retry-after": "0"}),
            response(200, ok),
        ]
    )
    client = XSearchClient(token, transport, sleep=lambda seconds: slept.append(seconds), now=lambda: 0)
    posts, page = client.search_page("free mint", 10)
    assert slept == [0.0]
    assert posts[0].author == "akun_contoh"
    assert posts[0].followers == 20
    assert page is None
    assert token not in transport.sent[0].url
    denied = FakeTransport([response(401, body=f"no {token}".encode())])
    bad = XSearchClient(token, denied, sleep=lambda _s: None, now=lambda: 0)
    with pytest.raises(Exception) as caught:
        bad.search_page("free mint", 10)
    assert token not in str(caught.value)
    assert "[redacted]" in str(caught.value)


def test_file_input_and_search_queries(tmp_path):
    path = tmp_path / "posts.json"
    path.write_text(
        json.dumps({"posts": [{"id": "a", "text": "gratis", "author": "akun_contoh"}]}),
        encoding="utf-8",
    )
    posts = load_posts(path)
    assert posts[0].source == "file"
    text = tmp_path / "paste.txt"
    text.write_text("baris satu\n\nhttps://proyek-contoh.example/mint\n", encoding="utf-8")
    assert len(load_posts(text)) == 2
    config = _config(tmp_path)
    queries = search_queries(config)
    assert any("free mint" in item for item in queries)
    assert any("from:akun_contoh" in item for item in queries)
    assert all("-is:retweet" in item for item in queries)


def _free_rpc(address: str, price: int = 0, supply: int = 10, maximum: int = 100, start: int | None = None, paused: int = 0):
    def handler(method, params):
        if method == "eth_blockNumber":
            return hex(50)
        if method == "eth_getLogs":
            return []
        if method == "eth_getCode":
            return "0x63" + selector("mint(uint256)").hex()
        if method == "eth_getStorageAt":
            return "0x" + ("00" * 32)
        if method != "eth_call":
            return None
        target = params[0]["to"]
        if target.lower() != address.lower():
            return None
        data = params[0]["data"]
        if data == "0x" + selector("price()").hex():
            return word(price)
        if data == "0x" + selector("totalSupply()").hex():
            return word(supply)
        if data == "0x" + selector("maxSupply()").hex():
            return word(maximum)
        if data == "0x" + selector("paused()").hex():
            return word(paused)
        if data == "0x" + selector("mintStart()").hex() and start is not None:
            return word(start)
        return None

    return FakeRpc(handler)


def test_monitor_alerts_then_stays_quiet(tmp_path):
    config = _config(tmp_path)
    address = fake_addr("11")
    post = Post(id="lead-1", text=f"free mint {address}", source="file", url="https://x.com/i/web/status/lead-1")
    now = 1_700_000_000
    state, seen, markdown = run_monitor([post], _free_rpc(address), config, None, set(), now)
    assert "Boleh dipratinjau" in markdown
    assert NEXT_STEP in markdown
    assert "30 menit" in markdown
    assert state["items"][address.lower()]["status"] == "open"
    state2, seen2, again = run_monitor([post], _free_rpc(address), config, state, seen, now + 1800)
    assert again == QUIET_MESSAGE
    assert seen2 == seen


def test_monitor_opening_soon_only_once_and_cap(tmp_path):
    config = _config(tmp_path)
    now = 1_700_000_000
    soon = now + 600
    posts = []
    addresses = []
    for index, pair in enumerate(("21", "22", "23", "24", "25", "26", "27"), start=1):
        address = fake_addr(pair)
        addresses.append(address)
        start = soon if index == 1 else None
        posts.append(Post(id=f"id-{index}", text=f"free mint {address}", source="file", url=f"https://x.com/i/web/status/id-{index}"))
    # First address waits. The other five are already open, so six would exceed the cap
    # if the waiting one were also open. Here five are open.

    def handler(method, params):
        if method == "eth_blockNumber":
            return hex(80)
        if method == "eth_getLogs":
            return []
        if method == "eth_getCode":
            return "0x60"
        if method == "eth_getStorageAt":
            return "0x" + ("00" * 32)
        if method != "eth_call":
            return None
        target = params[0]["to"].lower()
        data = params[0]["data"]
        if data == "0x" + selector("price()").hex():
            return word(0)
        if data == "0x" + selector("mintStart()").hex() and target == addresses[0].lower():
            return word(soon)
        return None

    state, seen, markdown = run_monitor(posts, FakeRpc(handler), config, None, set(), now)
    assert "Segera buka" in markdown
    assert "Boleh dipratinjau" in markdown
    assert "Melebihi batas per putaran" in markdown
    _state, _seen, again = run_monitor([], FakeRpc(handler), config, state, seen, now + 60)
    assert again == QUIET_MESSAGE


def test_monitor_status_change_sold_out(tmp_path):
    config = _config(tmp_path)
    address = fake_addr("44")
    post = Post(id="habis", text=f"free mint {address}", source="file")
    now = 1_700_000_000
    state, seen, _first = run_monitor([post], _free_rpc(address, supply=10, maximum=100), config, None, set(), now)
    _state, _seen, second = run_monitor(
        [],
        _free_rpc(address, supply=999, maximum=1000),
        config,
        state,
        seen,
        now + 1800,
    )
    assert "sold out" in second
    assert "Perubahan status" in second


def test_paid_called_free_is_warning_not_mint(tmp_path):
    config = _config(tmp_path)
    address = fake_addr("55")
    post = Post(id="bayar", text=f"free mint gas only {address}", source="file")
    _state, _seen, markdown = run_monitor([post], _free_rpc(address, price=2), config, None, set(), 1_700_000_000)
    assert "Peringatan" in markdown or "berbayar" in markdown
    assert "Boleh dipratinjau" not in markdown


def test_scan_writes_next_step(tmp_path):
    config = _config(tmp_path)
    address = fake_addr("66")
    post = Post(id="scan", text=f"mint {address}", source="file", url="https://x.com/i/web/status/scan")
    leads = scan_posts([post], _free_rpc(address), config, 1_700_000_000)
    assert leads[0].next_step == NEXT_STEP
    assert leads[0].chain is not None and leads[0].chain.price_wei == 0


def test_redact_long_hex_and_package_has_no_sender():
    hidden = "0x" + ("ab" * 32)
    assert "disunting" in redact(f"lihat {hidden}")
    root = Path(__file__).resolve().parents[1]
    blob = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    assert "eth_sendTransaction" not in blob
    assert "sign_transaction" not in blob


def test_json_rpc_error_on_dead_node():
    class Transport:
        def send(self, request):
            from scanner.http_util import HttpResponse

            return HttpResponse(599, {}, b"down")

    client = JsonRpcClient(["https://rpc.example/mati"], Transport())
    with pytest.raises(RpcError):
        client.call("eth_blockNumber", [])
