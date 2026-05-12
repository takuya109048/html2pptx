"""Load deck-from-source context chunks safely for Custom GPTs.

The Custom GPT code interpreter console may expose only the first 400 and
last 400 characters to the model. This loader prints exactly one chunk per
run and refuses output longer than 800 characters.
"""

from __future__ import annotations

import glob
import json
import sys
import datetime
import os
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 800
STATE_NAME = "deck_context_state.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def runtime_dir() -> Path:
    env_dir = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or os.environ.get("DECK_OUTPUT_DIR")
    if env_dir:
        path = Path(env_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    mnt = Path("/mnt/data")
    if os.name != "nt" and mnt.exists():
        return mnt
    path = Path.cwd()
    if (path / "SKILL.md").exists() and (path / "context_data.json").exists():
        parts = {part.lower() for part in path.parts}
        if ".agents" in parts or ".codex" in parts or ".claude" in parts:
            parents = list(path.parents)
            if len(parents) >= 3:
                path = parents[2]
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_data_path() -> Path:
    base = runtime_dir()
    candidates = [
        base / "context_data.json",
        Path(__file__).resolve().with_name("context_data.json"),
    ]
    candidates.extend(Path(p) for p in glob.glob(str(base / "*context_data.json")))
    for path in candidates:
        if path.exists():
            return path
    raise SystemExit("ERROR context_data.json not found")


def state_path() -> Path:
    return runtime_dir() / STATE_NAME


def log_path() -> Path:
    return runtime_dir() / "code_interpreter_log.md"


def append_log(phase: str, purpose: str, result: str, inputs: list[str] | None = None, outputs: list[str] | None = None) -> None:
    try:
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        line = {
            "time": ts,
            "phase": phase,
            "purpose": purpose,
            "inputs": inputs or [],
            "outputs": outputs or [],
            "result": result,
        }
        with log_path().open("a", encoding="utf-8") as f:
            f.write("- " + json.dumps(line, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_data() -> dict[str, Any]:
    path = find_data_path()
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    state_path().write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        raise SystemExit("ERROR no state. Run: context_loader.py start <phase>")
    return json.loads(path.read_text(encoding="utf-8"))


def emit(text: str) -> None:
    if len(text) > MAX_OUTPUT_CHARS:
        raise SystemExit(f"ERROR output too long len={len(text)}")
    print(text)


def format_chunk(data: dict[str, Any], phase: str, index: int) -> str:
    phase_data = data["phases"][phase]
    ids = phase_data["chunks"]
    total = len(ids)
    if index >= total:
        return f"DONE {total:03d}/{total:03d}"

    chunk_id = ids[index]
    chunk = data["chunks"][chunk_id]["text"]
    header = f"[ctx {index + 1:03d}/{total:03d} {chunk_id}]"
    if index + 1 >= total:
        footer = f"DONE {total:03d}/{total:03d}"
    else:
        footer = f"NEXT {index + 2:03d}/{total:03d}"
    return f"{header}\n{chunk}\n{footer}"


def emit_phase_index(data: dict[str, Any], phase: str, index: int) -> None:
    if phase not in data["phases"]:
        known = ",".join(sorted(data["phases"]))
        raise SystemExit(f"ERROR unknown phase. phases={known}")
    ids = data["phases"][phase]["chunks"]
    text = format_chunk(data, phase, index)
    if index < len(ids):
        done = index + 1 >= len(ids)
        save_state({"phase": phase, "next_index": index + 1, "done": done})
        status = f"NEXT {index + 2:03d}/{len(ids):03d}" if not done else f"DONE {len(ids):03d}/{len(ids):03d}"
    else:
        save_state({"phase": phase, "next_index": index, "done": True})
        status = f"DONE {len(ids):03d}/{len(ids):03d}"
    chunk_id = ids[index] if index < len(ids) else "complete"
    append_log(phase, "context_loader", f"{status} chunk={chunk_id}", outputs=[STATE_NAME])
    emit(text)


def validate(data: dict[str, Any]) -> str:
    max_chunk = int(data.get("max_chunk_chars", 800))
    errors: list[str] = []
    chunks = data.get("chunks", {})
    phases = data.get("phases", {})

    for chunk_id, chunk in chunks.items():
        text = chunk.get("text", "")
        if len(text) > max_chunk:
            errors.append(f"chunk>{max_chunk}:{chunk_id}:{len(text)}")
    for phase, phase_data in phases.items():
        for chunk_id in phase_data.get("chunks", []):
            if chunk_id not in chunks:
                errors.append(f"missing:{phase}:{chunk_id}")
            else:
                idx = phase_data["chunks"].index(chunk_id)
                rendered = format_chunk(data, phase, idx)
                if len(rendered) > MAX_OUTPUT_CHARS:
                    errors.append(f"output>800:{phase}:{chunk_id}:{len(rendered)}")

    if errors:
        shown = "; ".join(errors[:3])
        return f"ERROR {len(errors)} issue(s): {shown}"
    return f"OK phases={len(phases)} chunks={len(chunks)} max_output={MAX_OUTPUT_CHARS}"


def main(argv: list[str]) -> None:
    data = load_data()
    if len(argv) < 2:
        emit("USAGE start <phase> | next | get <chunk_id> | status | validate")
        return

    cmd = argv[1]
    if cmd == "start":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: start <phase>")
        emit_phase_index(data, argv[2], 0)
    elif cmd == "next":
        state = load_state()
        emit_phase_index(data, state["phase"], int(state["next_index"]))
    elif cmd == "get":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: get <chunk_id>")
        chunk_id = argv[2]
        chunk = data["chunks"].get(chunk_id)
        if not chunk:
            raise SystemExit(f"ERROR unknown chunk {chunk_id}")
        append_log("get", "context_loader", f"DONE chunk={chunk_id}")
        emit(f"[{chunk_id}]\n{chunk['text']}")
    elif cmd == "status":
        state = load_state()
        phase = state["phase"]
        total = len(data["phases"][phase]["chunks"])
        idx = min(int(state["next_index"]), total)
        current = f"{idx:03d}/{total:03d}" if idx >= total else f"{idx + 1:03d}/{total:03d}"
        status = "DONE" if idx >= total else "NEXT"
        append_log(phase, "context_loader status", f"{status} {current}")
        emit(f"STATUS {phase} {status} {current}")
    elif cmd == "validate":
        result = validate(data)
        append_log("validate", "context_loader validate", result)
        emit(result)
    else:
        raise SystemExit(f"ERROR unknown command {cmd}")


if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit as exc:
        if exc.code:
            append_log("context_loader", "context_loader error", f"ERROR {exc}")
        raise
    except Exception as exc:
        append_log("context_loader", "context_loader error", f"ERROR {type(exc).__name__}: {exc}")
        raise
