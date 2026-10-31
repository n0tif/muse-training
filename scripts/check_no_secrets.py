#!/usr/bin/env python3
"""Scan the repo for raw addresses and secret-like assignments.

Flags:
- 0x + 40 hex characters, except the zero address (0x followed by 40 zeros)
- 64 hex characters, with or without an 0x prefix (typical key or tx hash length)
- "private key", "mnemonic", or "seed phrase" assigned a value, or a mnemonic
  wordlist written out after those words

Placeholders such as 0xYOUR_WALLET do not match, because they are not hex.
Educational mentions of those words without a following secret do not match.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache"}
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".zip",
    ".pyc",
    ".woff",
    ".woff2",
}

ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
HEX64_RE = re.compile(r"\b(?:0x)?[a-fA-F0-9]{64}\b")
ASSIGNED_SECRET_RE = re.compile(
    r"(?i)\b(?:private[\s_-]*key|mnemonic|seed[\s_-]*phrase|seedphrase)\b"
    r"\s*[:=]\s*\S+"
)
MNEMONIC_LIST_RE = re.compile(
    r"(?i)\b(?:mnemonic|seed[\s_-]*phrase|seedphrase)\b\s*[:=]\s*"
    r"(?:[a-z]{2,8}\s+){11,23}[a-z]{2,8}\b"
)
PRIVATE_KEY_HEX_RE = re.compile(
    r"(?i)\bprivate[\s_-]*key\b\s+(?:is\s+|=\s*|:\s*)?(?:0x)?[a-fA-F0-9]{64}\b"
)
PEM_RE = re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC |PGP )?PRIVATE KEY-----")


def address_allowed(addr: str) -> bool:
    body = addr[2:]
    return set(body) == {"0"}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def scan_text(text: str) -> list[tuple[int, str, str]]:
    findings: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for match in ADDRESS_RE.finditer(line):
            if not address_allowed(match.group(0)):
                findings.append((lineno, "address-40", match.group(0)))
        for match in HEX64_RE.finditer(line):
            findings.append((lineno, "hex-64", match.group(0)[:8] + "…"))
        for match in ASSIGNED_SECRET_RE.finditer(line):
            findings.append((lineno, "assigned-secret", match.group(0)[:48]))
        for match in MNEMONIC_LIST_RE.finditer(line):
            findings.append((lineno, "mnemonic-list", "wordlist"))
        for match in PRIVATE_KEY_HEX_RE.finditer(line):
            findings.append((lineno, "private-key-hex", "hex"))
        if PEM_RE.search(line):
            findings.append((lineno, "pem-private-key", "header"))
    return findings


def self_test() -> None:
    bad_addr = "0x" + ("ab" * 20)
    zero_addr = "0x" + ("0" * 40)
    hex64 = "cd" * 32
    key_name = "private " + "key"
    word_name = "mnemo" + "nic"
    seed_name = "seed " + "phrase"
    assert scan_text(f"kirim ke {bad_addr}")
    assert scan_text(f"nol {zero_addr}") == []
    assert scan_text("dompet 0xYOUR_WALLET dan 0xCONTRACT") == []
    assert scan_text(f"hash {hex64}")
    assert scan_text(key_name + ": " + ("ab" * 32))
    words = " ".join(["word"] * 12)
    assert scan_text(word_name + ": " + words)
    assert scan_text("jangan bagikan " + key_name + " kepada siapa pun") == []
    assert scan_text(word_name + " dan " + seed_name + " harus tetap rahasia") == []
    assert scan_text(seed_name + " di chat tidak boleh diulang") == []


def main() -> int:
    self_test()
    findings: list[str] = []
    for path in iter_files(ROOT):
        data = path.read_bytes()
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        for lineno, kind, detail in scan_text(text):
            findings.append(f"{rel}:{lineno}: {kind}: {detail}")
    if findings:
        print("secret check failed:", file=sys.stderr)
        for item in findings:
            print(item, file=sys.stderr)
        return 1
    print(f"secret check passed ({ROOT})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
