#!/usr/bin/env python3
"""Build data/train.jsonl and data/eval.jsonl from scripts/dataset/part_*.py.

The system message on every row is the exact text of prompts/system_prompt.md.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(__file__).resolve().parent / "dataset"
SYSTEM_PATH = ROOT / "prompts" / "system_prompt.md"
PARTS = [
    "part_safety.py",
    "part_audit.py",
    "part_signals.py",
    "part_style.py",
    "part_multiturn.py",
    "part_eval.py",
]


def load_system() -> str:
    return SYSTEM_PATH.read_text(encoding="utf-8").strip()


def load_parts() -> list[dict]:
    rows: list[dict] = []
    for name in PARTS:
        path = DATASET / name
        spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
        if spec is None or spec.loader is None:
            raise SystemExit(f"cannot load {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows.extend(module.EXAMPLES)
    return rows


def to_record(example: dict, system: str) -> dict:
    turns = example["turns"]
    if not turns or turns[0][0] != "user" or turns[-1][0] != "assistant":
        raise SystemExit(f"bad turns for tag {example.get('tag')}")
    messages = [{"role": "system", "content": system}]
    for role, content in turns:
        if role not in {"user", "assistant"}:
            raise SystemExit(f"bad role {role}")
        messages.append({"role": role, "content": content.strip()})
    return {"messages": messages}


def dump(path: Path, records: list[dict]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records)


def main() -> int:
    check = "--check" in sys.argv
    system = load_system()
    examples = load_parts()
    train_records = []
    eval_records = []
    for example in examples:
        record = to_record(example, system)
        if example["split"] == "train":
            train_records.append(record)
        elif example["split"] == "eval":
            eval_records.append(record)
        else:
            raise SystemExit(f"unknown split {example['split']}")
    outputs = {
        ROOT / "data" / "train.jsonl": train_records,
        ROOT / "data" / "eval.jsonl": eval_records,
    }
    for path, records in outputs.items():
        body = dump(path, records)
        if check:
            existing = path.read_text(encoding="utf-8") if path.is_file() else ""
            if existing != body:
                raise SystemExit(f"{path} is out of date; run python scripts/build_dataset.py")
        else:
            path.write_text(body, encoding="utf-8")
    tags: dict[str, int] = {}
    for example in examples:
        if example["split"] != "train":
            continue
        tags[example["tag"]] = tags.get(example["tag"], 0) + 1
    print(
        f"dataset ok: train={len(train_records)} eval={len(eval_records)} "
        f"tags={len(tags)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
