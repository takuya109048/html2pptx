"""Validate Custom GPT skill context JSON files.

Usage:
    python validate_context_json.py .agents/skills/deck-from-source
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TEXT_LIMIT = 400
OUTPUT_LIMIT = 400
SKILL_LIMIT = 5_000
CONTEXT_LIMIT = 20_000


def count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"[NG] {message}")


def ok(message: str) -> None:
    print(f"[OK] {message}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rendered_output(data: dict[str, Any], phase: str, index: int) -> str:
    ids = data["phases"][phase]["chunks"]
    total = len(ids)
    if index >= total:
        return f"DONE {phase} {total}/{total}"
    chunk_id = ids[index]
    text = data["chunks"][chunk_id]["text"]
    header = f"[{phase} {index + 1:03d}/{total:03d} {chunk_id}]"
    if index + 1 >= total:
        footer = f"DONE {phase} {total}/{total}"
    else:
        footer = f"NEXT {phase} {index + 2:03d}/{total:03d}"
    return f"{header}\n{text}\n{footer}"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_context_json.py <skill_dir>")
        return 2

    skill_dir = Path(sys.argv[1]).resolve()
    if not skill_dir.exists():
        fail(f"skill_dir not found: {skill_dir}")
        return 1

    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    context_md = skill_dir / "context.md"
    data_path = skill_dir / "context_data.json"
    loader = skill_dir / "context_loader.py"

    for path, limit in [(skill_md, SKILL_LIMIT), (context_md, CONTEXT_LIMIT)]:
        if not path.exists():
            errors.append(f"missing {path.name}")
            continue
        n = count(path)
        if n > limit:
            errors.append(f"{path.name} {n}>{limit}")
        else:
            ok(f"{path.name} {n}/{limit}")

    if not data_path.exists():
        errors.append("missing context_data.json")
    if not loader.exists():
        errors.append("missing context_loader.py")
    if errors:
        for error in errors:
            fail(error)
        return 1

    data = load_json(data_path)
    chunks = data.get("chunks", {})
    phases = data.get("phases", {})
    referenced: set[str] = set()

    for chunk_id, chunk in chunks.items():
        text = chunk.get("text", "")
        if len(text) > TEXT_LIMIT:
            errors.append(f"chunk {chunk_id} {len(text)}>{TEXT_LIMIT}")

    for phase, phase_data in phases.items():
        seen_in_phase: set[str] = set()
        for index, chunk_id in enumerate(phase_data.get("chunks", [])):
            if chunk_id not in chunks:
                errors.append(f"phase {phase} missing chunk {chunk_id}")
                continue
            if chunk_id in seen_in_phase:
                errors.append(f"phase {phase} duplicate chunk {chunk_id}")
            seen_in_phase.add(chunk_id)
            referenced.add(chunk_id)
            output_len = len(rendered_output(data, phase, index))
            if output_len > OUTPUT_LIMIT:
                errors.append(f"loader output {phase}:{chunk_id} {output_len}>{OUTPUT_LIMIT}")

    unused = sorted(set(chunks) - referenced)
    if unused:
        print(f"[WARN] unused chunks={len(unused)} first={unused[0]}")

    result = subprocess.run(
        [sys.executable, str(loader), "validate"],
        cwd=str(skill_dir),
        text=True,
        capture_output=True,
        check=False,
    )
    loader_text = (result.stdout + result.stderr).strip()
    if result.returncode != 0 or not loader_text.startswith("OK "):
        errors.append(f"loader validate failed: {loader_text[:200]}")
    elif len(loader_text) > OUTPUT_LIMIT:
        errors.append(f"loader validate output {len(loader_text)}>{OUTPUT_LIMIT}")
    else:
        ok(loader_text)

    if errors:
        for error in errors:
            fail(error)
        return 1

    ok(f"context_data.json chunks={len(chunks)} phases={len(phases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
