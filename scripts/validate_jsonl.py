#!/usr/bin/env python3
"""Validate Muse chat JSONL files against prompts/system_prompt.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_PATH = ROOT / "prompts" / "system_prompt.md"
TRAIN_PATH = ROOT / "data" / "train.jsonl"
EVAL_PATH = ROOT / "data" / "eval.jsonl"

ID_HINTS = ("yang", "tidak", "aku", "sudah", "belum", "kalau", "ini", "jangan", "kamu", "untuk")
SHORT_USER_OK = {"confirm", "confirm.", "batal", "ya confirm"}


def load_system() -> str:
    if not SYSTEM_PATH.is_file():
        raise SystemExit(f"missing system prompt: {SYSTEM_PATH}")
    text = SYSTEM_PATH.read_text(encoding="utf-8").strip()
    if "Muse" not in text:
        raise SystemExit("system prompt does not look like the Muse prompt")
    return text


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        raise SystemExit(f"missing file: {path}")
    rows: list[dict] = []
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raise SystemExit(f"{path} has a BOM")
    if not raw.endswith("\n"):
        raise SystemExit(f"{path} must end with a newline")
    for lineno, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            raise SystemExit(f"{path}:{lineno}: blank line")
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{lineno}: invalid JSON ({exc})") from exc
        if list(obj.keys()) != ["messages"]:
            raise SystemExit(f"{path}:{lineno}: only 'messages' is allowed")
        rows.append(obj)
    return rows


def check_messages(path: Path, obj: dict, lineno: int, system: str) -> list[dict]:
    messages = obj["messages"]
    if not isinstance(messages, list) or len(messages) < 3:
        raise SystemExit(f"{path}:{lineno}: need at least system, user, assistant")
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise SystemExit(f"{path}:{lineno}: message {index} is not an object")
        if set(message.keys()) != {"role", "content"}:
            raise SystemExit(f"{path}:{lineno}: message {index} must have role and content only")
        if message["role"] not in {"system", "user", "assistant"}:
            raise SystemExit(f"{path}:{lineno}: bad role {message['role']}")
        if not isinstance(message["content"], str) or not message["content"].strip():
            raise SystemExit(f"{path}:{lineno}: empty content")
    if messages[0]["role"] != "system" or messages[0]["content"] != system:
        raise SystemExit(f"{path}:{lineno}: system message must match prompts/system_prompt.md")
    expect = "user"
    for message in messages[1:]:
        if message["role"] != expect:
            raise SystemExit(f"{path}:{lineno}: expected alternating {expect}")
        expect = "assistant" if expect == "user" else "user"
    if messages[-1]["role"] != "assistant":
        raise SystemExit(f"{path}:{lineno}: must end with assistant")
    assistant_text = "\n".join(m["content"] for m in messages if m["role"] == "assistant")
    hits = sum(1 for word in ID_HINTS if word in assistant_text.lower())
    if hits < 2:
        raise SystemExit(f"{path}:{lineno}: assistant text does not look Indonesian")
    if len(messages[-1]["content"].strip()) < 40:
        raise SystemExit(f"{path}:{lineno}: assistant reply is too short")
    return messages


def fingerprint(messages: list[dict]) -> str:
    return json.dumps(messages[1:], ensure_ascii=False, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Muse train and eval JSONL")
    parser.add_argument("--train", type=Path, default=TRAIN_PATH)
    parser.add_argument("--eval", type=Path, default=EVAL_PATH)
    parser.add_argument("--min-train", type=int, default=150)
    parser.add_argument("--min-eval", type=int, default=30)
    args = parser.parse_args()

    system = load_system()
    train = load_jsonl(args.train)
    heldout = load_jsonl(args.eval)
    if len(train) < args.min_train:
        raise SystemExit(f"train has {len(train)} examples, need >= {args.min_train}")
    if len(heldout) < args.min_eval:
        raise SystemExit(f"eval has {len(heldout)} examples, need >= {args.min_eval}")

    def consume(path: Path, rows: list[dict], seen_full: set[str], seen_assistant: set[str]) -> set[str]:
        openings: set[str] = set()
        for lineno, obj in enumerate(rows, start=1):
            messages = check_messages(path, obj, lineno, system)
            full = fingerprint(messages)
            if full in seen_full:
                raise SystemExit(f"{path}:{lineno}: duplicate conversation")
            seen_full.add(full)
            assistant_blob = "\n---\n".join(m["content"] for m in messages if m["role"] == "assistant")
            if assistant_blob in seen_assistant:
                raise SystemExit(f"{path}:{lineno}: duplicate assistant text")
            seen_assistant.add(assistant_blob)
            users = [m["content"].strip() for m in messages if m["role"] == "user"]
            opening = users[0]
            if opening in openings and opening.lower() not in SHORT_USER_OK:
                raise SystemExit(f"{path}:{lineno}: duplicate opening user message")
            openings.add(opening)
        return openings

    seen_full: set[str] = set()
    seen_assistant: set[str] = set()
    train_open = consume(args.train, train, seen_full, seen_assistant)
    eval_open = consume(args.eval, heldout, seen_full, seen_assistant)
    leaked = train_open & eval_open
    if leaked:
        raise SystemExit(f"eval opening repeats train: {sorted(leaked)[:3]}")

    multi_train = sum(1 for obj in train if len(obj["messages"]) > 3)
    multi_eval = sum(1 for obj in heldout if len(obj["messages"]) > 3)
    print(
        f"jsonl ok: train={len(train)} (multi-turn={multi_train}) "
        f"eval={len(heldout)} (multi-turn={multi_eval})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
