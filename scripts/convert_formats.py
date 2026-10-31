#!/usr/bin/env python3
"""Convert Muse chat JSONL to Alpaca instruction/input/output JSONL.

Mapping:
- instruction: the last user message
- input: the system prompt, then earlier turns if the conversation is multi-turn
- output: the last assistant message

Default inputs are data/train.jsonl and data/eval.jsonl.
Default outputs are data/alpaca.jsonl and data/alpaca_eval.jsonl.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def to_alpaca(obj: dict) -> dict:
    messages = obj["messages"]
    if messages[-1]["role"] != "assistant":
        raise ValueError("conversation must end with assistant")
    last_user_index = max(i for i, m in enumerate(messages) if m["role"] == "user")
    instruction = messages[last_user_index]["content"]
    parts: list[str] = []
    system_bits = [m["content"] for m in messages if m["role"] == "system"]
    if system_bits:
        parts.append("Aturan sistem:\n" + "\n\n".join(system_bits))
    history = messages[1:last_user_index]
    if history:
        lines = []
        for message in history:
            speaker = "Pengguna" if message["role"] == "user" else "Muse"
            lines.append(f"{speaker}: {message['content']}")
        parts.append("Riwayat:\n" + "\n\n".join(lines))
    return {
        "instruction": instruction,
        "input": "\n\n".join(parts),
        "output": messages[-1]["content"],
    }


def convert_file(src: Path) -> list[dict]:
    rows = []
    for lineno, line in enumerate(src.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(to_alpaca(json.loads(line)))
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            raise SystemExit(f"{src}:{lineno}: {exc}") from exc
    return rows


def dump(path: Path, rows: list[dict]) -> str:
    body = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    return body


def check_row(row: dict, where: str) -> None:
    if list(row.keys()) != ["instruction", "input", "output"]:
        raise SystemExit(f"{where}: keys must be instruction, input, output")
    for key in ("instruction", "input", "output"):
        if not isinstance(row[key], str) or not row[key].strip():
            raise SystemExit(f"{where}: empty {key}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert chat JSONL to Alpaca JSONL")
    parser.add_argument("--train", type=Path, default=ROOT / "data" / "train.jsonl")
    parser.add_argument("--eval", type=Path, default=ROOT / "data" / "eval.jsonl")
    parser.add_argument("--alpaca", type=Path, default=ROOT / "data" / "alpaca.jsonl")
    parser.add_argument("--alpaca-eval", type=Path, default=ROOT / "data" / "alpaca_eval.jsonl")
    parser.add_argument("--check", action="store_true", help="compare to files already on disk")
    args = parser.parse_args()

    pairs = [
        (args.train, args.alpaca),
        (args.eval, args.alpaca_eval),
    ]
    counts = []
    for src, dest in pairs:
        if not src.is_file():
            raise SystemExit(f"missing {src}")
        rows = convert_file(src)
        for index, row in enumerate(rows, start=1):
            check_row(row, f"{src}:{index}")
        body = dump(dest, rows)
        if args.check:
            existing = dest.read_text(encoding="utf-8") if dest.is_file() else ""
            if existing != body:
                raise SystemExit(f"{dest} is out of date; run python scripts/convert_formats.py")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(body, encoding="utf-8")
        counts.append(f"{dest.name}={len(rows)}")
    print("alpaca ok: " + ", ".join(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
