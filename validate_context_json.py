"""Validate Custom GPT skill context JSON files.

Usage:
    python validate_context_json.py .agents/skills/deck-from-source
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TEXT_LIMIT = 800
OUTPUT_LIMIT = 800
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
        return f"DONE {total:03d}/{total:03d} ACK deadbeef"
    chunk_id = ids[index]
    text = data["chunks"][chunk_id]["text"]
    header = f"[ctx {phase} {index + 1:03d}/{total:03d} {chunk_id}]"
    if index + 1 >= total:
        footer = f"DONE {total:03d}/{total:03d} ACK deadbeef"
    else:
        footer = f"NEXT {index + 2:03d}/{total:03d} ACK deadbeef"
    return f"{header}\n{text}\n{footer}"


def run_loader(loader: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(loader), *args],
        cwd=str(loader.parent),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout + result.stderr).strip()


def extract_ack(output: str) -> str:
    match = re.search(r"\bACK ([0-9a-f]{8})\b", output)
    if not match:
        raise ValueError(f"ACK not found in output: {output[:120]}")
    return match.group(1)


def check_loader_api(loader: Path, errors: list[str]) -> None:
    init_result = run_loader(loader, "init", "turn_b_yes")
    init_text = combined_output(init_result)
    if init_result.returncode != 0 or "NEXT 002/" not in init_text or " ACK " not in init_text:
        errors.append(f"loader init failed: {init_text[:200]}")
        return
    if len(init_text) > OUTPUT_LIMIT:
        errors.append(f"loader init output {len(init_text)}>{OUTPUT_LIMIT}")
    ack = extract_ack(init_text)

    bad_ack_result = run_loader(loader, "advance", "00000000")
    if bad_ack_result.returncode == 0 or "bad ACK" not in combined_output(bad_ack_result):
        errors.append("loader bad ACK was not rejected")

    advance_result = run_loader(loader, "advance", ack)
    advance_text = combined_output(advance_result)
    if advance_result.returncode != 0 or "NEXT 003/" not in advance_text or " ACK " not in advance_text:
        errors.append(f"loader advance failed: {advance_text[:200]}")
        return
    if len(advance_text) > OUTPUT_LIMIT:
        errors.append(f"loader advance output {len(advance_text)}>{OUTPUT_LIMIT}")

    repeat_result = run_loader(loader, "repeat")
    repeat_text = combined_output(repeat_result)
    if repeat_result.returncode != 0 or "NEXT 003/" not in repeat_text or " ACK " not in repeat_text:
        errors.append(f"loader repeat failed: {repeat_text[:200]}")
        return
    if len(repeat_text) > OUTPUT_LIMIT:
        errors.append(f"loader repeat output {len(repeat_text)}>{OUTPUT_LIMIT}")

    status_result = run_loader(loader, "status")
    status_text = combined_output(status_result)
    if status_result.returncode != 0 or "STATUS route=turn_b_yes" not in status_text:
        errors.append(f"loader status failed: {status_text[:200]}")
    if "ACK " in status_text:
        errors.append("loader status must not display ACK")

    repair_result = run_loader(loader, "repair", "setup")
    repair_text = combined_output(repair_result)
    if repair_result.returncode != 0 or "setup" not in repair_text or " ACK " not in repair_text:
        errors.append(f"loader repair failed: {repair_text[:200]}")
        return
    if len(repair_text) > OUTPUT_LIMIT:
        errors.append(f"loader repair output {len(repair_text)}>{OUTPUT_LIMIT}")

    done_text = repair_text
    safety = 0
    while "NEXT " in done_text and safety < 10:
        safety += 1
        next_ack = extract_ack(done_text)
        done_result = run_loader(loader, "advance", next_ack)
        done_text = combined_output(done_result)
        if done_result.returncode != 0:
            errors.append(f"loader repair advance failed: {done_text[:200]}")
            return
        if len(done_text) > OUTPUT_LIMIT:
            errors.append(f"loader repair advance output {len(done_text)}>{OUTPUT_LIMIT}")
    if "DONE " not in done_text:
        errors.append("loader repair route did not reach DONE during validation")
        return
    done_ack = extract_ack(done_text)
    phase_done_result = run_loader(loader, "phase-done", done_ack)
    phase_done_text = combined_output(phase_done_result)
    if phase_done_result.returncode != 0 or not phase_done_text.startswith("DONE route=repair:setup"):
        errors.append(f"loader phase-done failed: {phase_done_text[:200]}")

    legacy_result = run_loader(loader, "start", "turn_b_yes")
    if legacy_result.returncode == 0 or "unsupported command" not in combined_output(legacy_result):
        errors.append("loader legacy start command was not rejected")


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
    catalog_loader = skill_dir / "template_catalog_loader.py"

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
        encoding="utf-8",
        errors="replace",
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
        check_loader_api(loader, errors)

    if catalog_loader.exists():
        catalog_result = subprocess.run(
            [sys.executable, str(catalog_loader), "validate"],
            cwd=str(skill_dir),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        catalog_text = (catalog_result.stdout + catalog_result.stderr).strip()
        if catalog_result.returncode != 0 or not catalog_text.startswith("OK "):
            errors.append(f"template catalog validate failed: {catalog_text[:200]}")
        elif len(catalog_text) > OUTPUT_LIMIT:
            errors.append(f"template catalog validate output {len(catalog_text)}>{OUTPUT_LIMIT}")
        else:
            ok(catalog_text)

    if errors:
        for error in errors:
            fail(error)
        return 1

    ok(f"context_data.json chunks={len(chunks)} phases={len(phases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
