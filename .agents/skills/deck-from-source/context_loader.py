"""Load deck-from-source context chunks safely for Custom GPTs.

The Custom GPT code interpreter console may expose only the first 400 and
last 400 characters to the model. This loader prints one chunk per run,
keeps progress in a small state file, and gates advancement with ACK tokens.
"""

from __future__ import annotations

import glob
import hashlib
import json
import secrets
import sys
import tempfile
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

MAX_OUTPUT_CHARS = 650
STATE_NAME = "deck_context_state.json"

ROUTES: dict[str, list[str]] = {
    "turn_b_yes": ["turn_b_yes"],
    "turn_b_no": ["turn_b_no"],
}

REPAIRS: dict[str, str] = {
    "emphasis": "repair_emphasis",
    "strict-emphasis": "repair_emphasis",
    "repair_emphasis": "repair_emphasis",
    "density": "repair_density",
    "strict-density": "repair_density",
    "repair_density": "repair_density",
    "text": "repair_text",
    "repair_text": "repair_text",
    "setup": "setup",
}

LEGACY_COMMANDS = {"start", "next", "get", "read"}


def runtime_dir() -> Path:
    mnt = Path("/mnt/data")
    if mnt.exists():
        return mnt
    path = Path(tempfile.gettempdir()) / "deck_from_source_context"
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
    state_path().write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        raise SystemExit("ERROR no state. Run: context_loader.py init <route>")
    return json.loads(path.read_text(encoding="utf-8"))


def maybe_load_state() -> dict[str, Any] | None:
    path = state_path()
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def emit(text: str) -> None:
    if len(text) > MAX_OUTPUT_CHARS:
        raise SystemExit(f"ERROR output too long len={len(text)}")
    print(text)


def new_ack() -> str:
    return secrets.token_hex(4)


def ack_hash(ack: str) -> str:
    return hashlib.sha256(ack.encode("utf-8")).hexdigest()


def set_ack(state: dict[str, Any], ack: str) -> None:
    state["ack_hash"] = ack_hash(ack)


def verify_ack(state: dict[str, Any], ack: str) -> None:
    expected = state.get("ack_hash")
    if not expected or not secrets.compare_digest(str(expected), ack_hash(ack)):
        raise SystemExit("ERROR bad ACK. Use repeat if the last ACK was lost.")


def phase_ids(data: dict[str, Any], phase: str) -> list[str]:
    if phase not in data.get("phases", {}):
        known = ",".join(sorted(data.get("phases", {})))
        raise SystemExit(f"ERROR unknown phase. phases={known}")
    return list(data["phases"][phase].get("chunks", []))


def format_chunk(data: dict[str, Any], phase: str, index: int, ack: str) -> str:
    ids = phase_ids(data, phase)
    total = len(ids)
    if index < 0 or index >= total:
        raise SystemExit(f"ERROR index out of range {index + 1}/{total}")

    chunk_id = ids[index]
    chunk = data["chunks"][chunk_id]["text"]
    header = f"[ctx {phase} {index + 1:03d}/{total:03d} {chunk_id}]"
    if index + 1 >= total:
        footer = f"DONE {total:03d}/{total:03d} ACK {ack}"
    else:
        footer = f"NEXT {index + 2:03d}/{total:03d} ACK {ack}"
    return f"{header}\n{chunk}\n{footer}"


def emit_phase_index(data: dict[str, Any], state: dict[str, Any], phase: str, index: int) -> None:
    ids = phase_ids(data, phase)
    total = len(ids)
    ack = new_ack()
    completed = set(state.get("completed_phases", []))
    phase_done = index + 1 >= total
    if phase_done:
        completed.add(phase)

    state.update(
        {
            "phase": phase,
            "next_index": min(index + 1, total),
            "last_index": index,
            "phase_done": phase_done,
            "route_done": False,
            "completed_phases": sorted(completed),
        }
    )
    set_ack(state, ack)
    save_state(state)
    emit(format_chunk(data, phase, index, ack))


def init_state(route: str, phases: list[str], completed: list[str] | None = None) -> dict[str, Any]:
    return {
        "route": route,
        "route_phases": phases,
        "route_index": 0,
        "completed_phases": completed or [],
    }


def command_init(data: dict[str, Any], route: str) -> None:
    if route not in ROUTES:
        known = ",".join(sorted(ROUTES))
        raise SystemExit(f"ERROR unknown route. routes={known}")
    phases = ROUTES[route]
    state = init_state(route, phases)
    emit_phase_index(data, state, phases[0], 0)


def command_repair(data: dict[str, Any], repair_type: str) -> None:
    if repair_type not in REPAIRS:
        known = ",".join(sorted(REPAIRS))
        raise SystemExit(f"ERROR unknown repair. repairs={known}")
    phase = REPAIRS[repair_type]
    previous = maybe_load_state() or {}
    state = init_state(f"repair:{repair_type}", [phase], previous.get("completed_phases", []))
    emit_phase_index(data, state, phase, 0)


def command_advance(data: dict[str, Any], ack: str) -> None:
    state = load_state()
    verify_ack(state, ack)
    if state.get("route_done"):
        raise SystemExit("ERROR route already DONE. Run init <route> for a new route.")
    if state.get("phase_done"):
        raise SystemExit("ERROR phase already DONE. Run phase-done <ACK> after finishing work.")
    emit_phase_index(data, state, str(state["phase"]), int(state["next_index"]))


def command_phase_done(data: dict[str, Any], ack: str) -> None:
    state = load_state()
    verify_ack(state, ack)
    if not state.get("phase_done"):
        raise SystemExit("ERROR phase is not DONE yet. Run advance <ACK> first.")

    phases = list(state.get("route_phases", []))
    next_route_index = int(state.get("route_index", 0)) + 1
    if next_route_index < len(phases):
        state["route_index"] = next_route_index
        emit_phase_index(data, state, phases[next_route_index], 0)
        return

    final_ack = new_ack()
    state["route_done"] = True
    set_ack(state, final_ack)
    save_state(state)
    emit(f"DONE route={state.get('route')} phase={state.get('phase')} ACK {final_ack}")


def command_repeat(data: dict[str, Any]) -> None:
    state = load_state()
    if state.get("route_done"):
        ack = new_ack()
        set_ack(state, ack)
        save_state(state)
        emit(f"DONE route={state.get('route')} phase={state.get('phase')} ACK {ack}")
        return
    emit_phase_index(data, state, str(state["phase"]), int(state["last_index"]))


def command_status(data: dict[str, Any]) -> None:
    state = maybe_load_state()
    if not state:
        emit("STATUS no_state")
        return
    phase = str(state.get("phase"))
    total = len(phase_ids(data, phase))
    if state.get("route_done"):
        status = "ROUTE_DONE"
        pos = f"{total:03d}/{total:03d}"
    elif state.get("phase_done"):
        status = "DONE"
        pos = f"{total:03d}/{total:03d}"
    else:
        status = "NEXT"
        pos = f"{int(state.get('next_index', 0)) + 1:03d}/{total:03d}"
    emit(f"STATUS route={state.get('route')} phase={phase} {status} {pos}")


def validate(data: dict[str, Any]) -> str:
    max_chunk = int(data.get("max_chunk_chars", 560))
    errors: list[str] = []
    chunks = data.get("chunks", {})
    phases = data.get("phases", {})

    for chunk_id, chunk in chunks.items():
        text = chunk.get("text", "")
        if len(text) > max_chunk:
            errors.append(f"chunk>{max_chunk}:{chunk_id}:{len(text)}")

    for phase, phase_data in phases.items():
        seen: set[str] = set()
        ids = phase_data.get("chunks", [])
        for index, chunk_id in enumerate(ids):
            if chunk_id in seen:
                errors.append(f"duplicate:{phase}:{chunk_id}")
            seen.add(chunk_id)
            if chunk_id not in chunks:
                errors.append(f"missing:{phase}:{chunk_id}")
                continue
            rendered = format_chunk(data, phase, index, "deadbeef")
            if len(rendered) > MAX_OUTPUT_CHARS:
                errors.append(f"output>{MAX_OUTPUT_CHARS}:{phase}:{chunk_id}:{len(rendered)}")

    for route, route_phases in ROUTES.items():
        for phase in route_phases:
            if phase not in phases:
                errors.append(f"route-missing:{route}:{phase}")
    for repair_type, phase in REPAIRS.items():
        if phase not in phases:
            errors.append(f"repair-missing:{repair_type}:{phase}")

    if errors:
        shown = "; ".join(errors[:3])
        return f"ERROR {len(errors)} issue(s): {shown}"
    return f"OK phases={len(phases)} chunks={len(chunks)} max_output={MAX_OUTPUT_CHARS}"


def main(argv: list[str]) -> None:
    data = load_data()
    if len(argv) < 2:
        emit("USAGE init <route> | advance <ACK> | phase-done <ACK> | repair <type> | repeat | status | validate")
        return

    cmd = argv[1]
    if cmd in LEGACY_COMMANDS:
        raise SystemExit("ERROR unsupported command. Use init/advance/phase-done/repair/repeat/status/validate.")
    if cmd == "init":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: init <route>")
        command_init(data, argv[2])
    elif cmd == "advance":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: advance <ACK>")
        command_advance(data, argv[2])
    elif cmd == "phase-done":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: phase-done <ACK>")
        command_phase_done(data, argv[2])
    elif cmd == "repair":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: repair <type>")
        command_repair(data, argv[2])
    elif cmd == "repeat":
        if len(argv) != 2:
            raise SystemExit("ERROR usage: repeat")
        command_repeat(data)
    elif cmd == "status":
        if len(argv) != 2:
            raise SystemExit("ERROR usage: status")
        command_status(data)
    elif cmd == "validate":
        if len(argv) != 2:
            raise SystemExit("ERROR usage: validate")
        emit(validate(data))
    else:
        raise SystemExit(f"ERROR unknown command {cmd}")


if __name__ == "__main__":
    main(sys.argv)
