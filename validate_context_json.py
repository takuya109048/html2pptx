"""Validate Custom GPT skill context JSON files.

Usage:
    python validate_context_json.py .agents/skills/deck-from-source
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TEXT_LIMIT = 800
OUTPUT_LIMIT = 800
SKILL_LIMIT = 5_000
CONTEXT_LIMIT = 18_000


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
        return f"DONE {total:03d}/{total:03d}"
    chunk_id = ids[index]
    text = data["chunks"][chunk_id]["text"]
    header = f"[ctx {index + 1:03d}/{total:03d} {chunk_id}]"
    if index + 1 >= total:
        footer = f"DONE {total:03d}/{total:03d}"
    else:
        footer = f"NEXT {index + 2:03d}/{total:03d}"
    return f"{header}\n{text}\n{footer}"


def run_loader(loader: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(loader), *args],
        cwd=str(loader.parent),
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout + result.stderr).strip()


def last_output_file() -> Path:
    mnt = Path("/mnt/data")
    if mnt.exists():
        return mnt / "deck_context_last_output.txt"
    return Path(tempfile.gettempdir()) / "deck_from_source_context" / "deck_context_last_output.txt"


def check_loader_api(loader: Path, data: dict[str, Any], errors: list[str]) -> None:
    start_result = run_loader(loader, "start", "turn_b_yes")
    start_text = combined_output(start_result)
    if start_result.returncode != 0 or "NEXT 002/" not in start_text:
        errors.append(f"loader start failed: {start_text[:200]}")
        return
    if len(start_text) > OUTPUT_LIMIT:
        errors.append(f"loader start output {len(start_text)}>{OUTPUT_LIMIT}")
    last_text = last_output_file().read_text(encoding="utf-8") if last_output_file().exists() else ""
    if "turn_b_yes" not in last_text or "NEXT 002/" not in last_text:
        errors.append("loader last output file was not written after start")

    next_result = run_loader(loader, "next")
    next_text = combined_output(next_result)
    if next_result.returncode != 0 or "NEXT 003/" not in next_text:
        errors.append(f"loader next failed: {next_text[:200]}")
        return
    if len(next_text) > OUTPUT_LIMIT:
        errors.append(f"loader next output {len(next_text)}>{OUTPUT_LIMIT}")
    last_text = last_output_file().read_text(encoding="utf-8") if last_output_file().exists() else ""
    if "NEXT 003/" not in last_text:
        errors.append("loader last output file was not updated after next")

    status_result = run_loader(loader, "status")
    status_text = combined_output(status_result)
    if status_result.returncode != 0 or "STATUS turn_b_yes NEXT 003/" not in status_text:
        errors.append(f"loader status failed: {status_text[:200]}")

    get_chunk_id = next(
        (
            chunk_id
            for phase_data in data.get("phases", {}).values()
            for chunk_id in phase_data.get("chunks", [])
        ),
        None,
    )
    if not get_chunk_id:
        errors.append("loader get failed: no chunk ids available")
        return

    get_result = run_loader(loader, "get", get_chunk_id)
    get_text = combined_output(get_result)
    if get_result.returncode != 0 or f"[{get_chunk_id}]" not in get_text:
        errors.append(f"loader get failed: {get_text[:200]}")
    if len(get_text) > OUTPUT_LIMIT:
        errors.append(f"loader get output {len(get_text)}>{OUTPUT_LIMIT}")

    setup_start_result = run_loader(loader, "start", "setup")
    setup_text = combined_output(setup_start_result)
    if setup_start_result.returncode != 0 or "setup" not in setup_text:
        errors.append(f"loader setup start failed: {setup_text[:200]}")
        return
    done_text = setup_text
    safety = 0
    while "NEXT " in done_text and safety < 10:
        safety += 1
        done_result = run_loader(loader, "next")
        done_text = combined_output(done_result)
        if done_result.returncode != 0:
            errors.append(f"loader setup next failed: {done_text[:200]}")
            return
        if len(done_text) > OUTPUT_LIMIT:
            errors.append(f"loader setup next output {len(done_text)}>{OUTPUT_LIMIT}")
    if "DONE " not in done_text:
        errors.append("loader setup phase did not reach DONE during validation")

    invalid_result = run_loader(loader, "unsupported-command")
    if invalid_result.returncode == 0 or "unknown command" not in combined_output(invalid_result):
        errors.append("loader unknown command was not rejected")


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
        check_loader_api(loader, data, errors)

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
