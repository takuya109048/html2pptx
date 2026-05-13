"""Stateful deck-from-source context loader for Custom GPTs.

The Custom GPT code interpreter console may expose only the first 400 and
last 400 characters to the model. This loader emits exactly one context chunk
per run, advances by saved state, and requires the ACK printed by the previous
run before moving on.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 800
STATE_NAME = "deck_context_state.json"
LEGACY_COMMANDS = {"read", "start", "next", "get"}

FLOW_PHASES: dict[str, list[str]] = {
    "yes": [
        "yes_plan",
        "yes_schema",
        "yes_layout",
        "yes_image",
        "yes_body",
        "yes_emphasis",
        "yes_notes",
        "yes_check_convert",
    ],
    "no": [
        "no_plan",
        "no_schema",
        "no_layout",
        "no_body",
        "no_emphasis",
        "no_notes",
        "no_check_convert",
    ],
    "repair_emphasis": ["repair_emphasis"],
    "repair_density": ["repair_density"],
    "repair_text": ["repair_text"],
    "setup": ["setup"],
}

FLOW_ALIASES = {
    "emphasis": "repair_emphasis",
    "density": "repair_density",
    "text": "repair_text",
}

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


def load_data() -> dict[str, Any]:
    path = find_data_path()
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    state_path().write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        raise SystemExit("ERROR no state. Run: context_loader.py init yes|no")
    return json.loads(path.read_text(encoding="utf-8"))


def emit(text: str) -> None:
    if len(text) > MAX_OUTPUT_CHARS:
        raise SystemExit(f"ERROR output too long len={len(text)}")
    print(text)


def normalize_flow(raw: str) -> str:
    flow = FLOW_ALIASES.get(raw, raw)
    if flow not in FLOW_PHASES:
        known = ",".join(sorted(FLOW_PHASES))
        raise SystemExit(f"ERROR unknown flow. flows={known}")
    return flow


def new_ack() -> str:
    return secrets.token_hex(4)


def ack_hash(raw_ack: str) -> str:
    return hashlib.sha256(raw_ack.encode("utf-8")).hexdigest()


def require_ack(state: dict[str, Any], raw_ack: str | None) -> None:
    expected_hash = str(state.get("ack_hash", ""))
    legacy_expected = str(state.get("ack", ""))
    if not expected_hash and not legacy_expected:
        raise SystemExit("ERROR no ACK in state. Run init yes|no again.")
    if expected_hash and ack_hash(raw_ack or "") != expected_hash:
        raise SystemExit("ERROR ACK required. Use the ACK printed at the end of the previous loader output.")
    if legacy_expected and raw_ack != legacy_expected:
        raise SystemExit("ERROR ACK required. Use the ACK printed at the end of the previous loader output.")


def current_phase(state: dict[str, Any]) -> str:
    phases = state.get("phases") or []
    pos = int(state.get("phase_pos", 0))
    if pos >= len(phases):
        raise SystemExit("ERROR route is complete.")
    return str(phases[pos])


def format_chunk(data: dict[str, Any], phase: str, index: int, ack: str) -> tuple[str, str, str]:
    phase_data = data["phases"][phase]
    ids = phase_data["chunks"]
    total = len(ids)
    if index >= total:
        return f"DONE {total:03d}/{total:03d} ACK {ack}", "DONE", "complete"

    chunk_id = ids[index]
    chunk = data["chunks"][chunk_id]["text"]
    header = f"[ctx {index + 1:03d}/{total:03d} {phase}]"
    if index + 1 >= total:
        status = "DONE"
        footer = f"DONE {total:03d}/{total:03d} ACK {ack}"
    else:
        status = "NEXT"
        footer = f"NEXT {index + 2:03d}/{total:03d} ACK {ack}"
    return f"{header}\n{chunk}\n{footer}", status, chunk_id


def emit_next_chunk(data: dict[str, Any], state: dict[str, Any]) -> None:
    phase = current_phase(state)
    ids = data["phases"][phase]["chunks"]
    index = int(state.get("next_index", 0))
    if index >= len(ids):
        state["phase_done"] = True
        save_state(state)
        raise SystemExit("ERROR phase already DONE. Do the phase work, then run: context_loader.py phase-done <ACK>")

    ack = new_ack()
    text, status, chunk_id = format_chunk(data, phase, index, ack)
    state.pop("ack", None)
    state["ack_hash"] = ack_hash(ack)
    state["phase"] = phase
    state["next_index"] = index + 1
    state["phase_done"] = status == "DONE"
    state["route_done"] = False
    state["last_chunk"] = {"phase": phase, "index": index, "status": status, "chunk_id": chunk_id}
    save_state(state)
    emit(text)


def init_flow(data: dict[str, Any], flow_raw: str) -> None:
    flow = normalize_flow(flow_raw)
    phases = FLOW_PHASES[flow]
    missing = [phase for phase in phases if phase not in data.get("phases", {})]
    if missing:
        raise SystemExit(f"ERROR missing phase {missing[0]}")
    state = {
        "flow": flow,
        "phases": phases,
        "phase_pos": 0,
        "next_index": 0,
        "phase_done": False,
        "route_done": False,
        "completed_phases": [],
    }
    emit_next_chunk(data, state)


def advance(data: dict[str, Any], raw_ack: str | None) -> None:
    state = load_state()
    require_ack(state, raw_ack)
    if state.get("route_done"):
        raise SystemExit("ERROR route already DONE.")
    if state.get("phase_done"):
        raise SystemExit("ERROR phase is DONE. Do the phase work, then run: context_loader.py phase-done <ACK>")
    emit_next_chunk(data, state)


def finish_phase(data: dict[str, Any], raw_ack: str | None) -> None:
    state = load_state()
    require_ack(state, raw_ack)
    if not state.get("phase_done"):
        raise SystemExit("ERROR phase is not DONE. Continue with: context_loader.py advance <ACK>")

    phase = current_phase(state)
    completed = list(state.get("completed_phases", []))
    if phase not in completed:
        completed.append(phase)
    state["completed_phases"] = completed
    state["phase_pos"] = int(state.get("phase_pos", 0)) + 1
    state["next_index"] = 0
    state["phase_done"] = False
    if state["phase_pos"] >= len(state.get("phases", [])):
        state["route_done"] = True
        state.pop("ack", None)
        state.pop("ack_hash", None)
        save_state(state)
        emit(f"ROUTE_DONE flow={state.get('flow')} phases={len(completed):03d}/{len(completed):03d}")
        return
    emit_next_chunk(data, state)


def repeat_last(data: dict[str, Any]) -> None:
    state = load_state()
    last = state.get("last_chunk")
    if not isinstance(last, dict):
        raise SystemExit("ERROR no last chunk to repeat.")
    ack = new_ack()
    state.pop("ack", None)
    state["ack_hash"] = ack_hash(ack)
    save_state(state)
    phase = str(last["phase"])
    index = int(last["index"])
    text, status, chunk_id = format_chunk(data, phase, index, ack)
    emit(text)


def status(data: dict[str, Any]) -> None:
    state = load_state()
    phases = state.get("phases") or []
    pos = min(int(state.get("phase_pos", 0)), len(phases))
    if state.get("route_done") or pos >= len(phases):
        text = f"STATUS {state.get('flow')} ROUTE_DONE {pos:03d}/{len(phases):03d}"
    else:
        phase = str(phases[pos])
        total = len(data["phases"][phase]["chunks"])
        idx = min(int(state.get("next_index", 0)), total)
        phase_status = "DONE" if state.get("phase_done") else "NEXT"
        shown = idx if state.get("phase_done") else idx + 1
        text = f"STATUS {state.get('flow')} {phase} {phase_status} {shown:03d}/{total:03d} ACK_REQUIRED"
    emit(text)


def validate(data: dict[str, Any]) -> str:
    max_chunk = int(data.get("max_chunk_chars", 800))
    errors: list[str] = []
    chunks = data.get("chunks", {})
    phases = data.get("phases", {})

    for flow, flow_phases in FLOW_PHASES.items():
        for phase in flow_phases:
            if phase not in phases:
                errors.append(f"missing-flow-phase:{flow}:{phase}")
    for chunk_id, chunk in chunks.items():
        text = chunk.get("text", "")
        if len(text) > max_chunk:
            errors.append(f"chunk>{max_chunk}:{chunk_id}:{len(text)}")
    for phase, phase_data in phases.items():
        for idx, chunk_id in enumerate(phase_data.get("chunks", [])):
            if chunk_id not in chunks:
                errors.append(f"missing:{phase}:{chunk_id}")
            else:
                rendered, _, _ = format_chunk(data, phase, idx, "00000000")
                if len(rendered) > MAX_OUTPUT_CHARS:
                    errors.append(f"output>800:{phase}:{chunk_id}:{len(rendered)}")

    if errors:
        shown = "; ".join(errors[:3])
        return f"ERROR {len(errors)} issue(s): {shown}"
    return f"OK flows={len(FLOW_PHASES)} phases={len(phases)} chunks={len(chunks)} max_output={MAX_OUTPUT_CHARS}"


def legacy_error() -> None:
    raise SystemExit(
        "ERROR legacy chunk API disabled. Use: init yes|no, advance <ACK>, phase-done <ACK>, repeat, status, validate."
    )


def main(argv: list[str]) -> None:
    data = load_data()
    if len(argv) < 2:
        emit("USAGE init yes|no|repair_emphasis|repair_density|repair_text|setup | advance <ACK> | phase-done <ACK> | repeat | status | validate")
        return

    cmd = argv[1]
    if cmd == "init":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: init yes|no|repair_emphasis|repair_density|repair_text|setup")
        init_flow(data, argv[2])
    elif cmd == "repair":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: repair emphasis|density|text")
        init_flow(data, normalize_flow(argv[2]))
    elif cmd == "setup":
        if len(argv) != 2:
            raise SystemExit("ERROR usage: setup")
        init_flow(data, "setup")
    elif cmd == "advance":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: advance <ACK>")
        advance(data, argv[2])
    elif cmd in {"phase-done", "complete", "done"}:
        if len(argv) != 3:
            raise SystemExit("ERROR usage: phase-done <ACK>")
        finish_phase(data, argv[2])
    elif cmd == "repeat":
        repeat_last(data)
    elif cmd == "status":
        status(data)
    elif cmd == "validate":
        result = validate(data)
        emit(result)
    elif cmd in LEGACY_COMMANDS or cmd in data.get("phases", {}):
        legacy_error()
    else:
        raise SystemExit(f"ERROR unknown command {cmd}")


if __name__ == "__main__":
    main(sys.argv)
