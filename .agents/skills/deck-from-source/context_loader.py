"""Stateful deck-from-source context loader for Custom GPTs.

The Custom GPT code interpreter console may expose only the first 400 and
last 400 characters to the model. This loader emits exactly one context chunk
per run, advances by saved state, and requires the ACK printed by the previous
run before moving on.
"""

from __future__ import annotations

import datetime
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
JST = datetime.timezone(datetime.timedelta(hours=9), "JST")

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
    "repair_schema": ["repair_schema"],
    "repair_text": ["repair_text"],
    "setup": ["setup"],
}

FLOW_ALIASES = {
    "emphasis": "repair_emphasis",
    "density": "repair_density",
    "schema": "repair_schema",
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


def log_path() -> Path:
    return runtime_dir() / "code_interpreter_log.md"


def jst_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone(JST).isoformat(timespec="seconds")


def compact_text(value: str) -> str:
    return " ".join(str(value).split())


def human_phase(phase: str) -> str:
    phase_topics = {
        "plan": "計画",
        "schema": "JSON骨格",
        "layout": "レイアウト",
        "image": "画像設計",
        "body": "本文作成",
        "emphasis": "強調表現",
        "notes": "発表者ノート",
        "check_convert": "変換前確認",
    }
    if phase.startswith("yes_") or phase.startswith("no_"):
        route = "画像あり方針" if phase.startswith("yes_") else "画像なし方針"
        topic = phase_topics.get(phase.split("_", 1)[1], phase)
        return f"{route}の{topic}フェーズ"
    if phase.startswith("repair_"):
        repair_topic = {
            "emphasis": "強調表現の修復",
            "density": "情報密度の修復",
            "schema": "JSON骨格の修復",
            "text": "文字化けの修復",
        }.get(phase.split("_", 1)[1], phase)
        return f"{repair_topic}フェーズ"
    labels = {
        "setup": "初期設定フェーズ",
        "status": "進捗確認",
        "validate": "設定検証",
        "context_loader": "コンテキスト読み込み",
        "activity": "作業活動",
        "manual": "手動判断",
        "file_search": "file search",
        "resolve_uploads": "アップロード初期化",
        "conversion": "変換処理",
        "verification": "検証処理",
        "download_links": "リンク提示",
    }
    return labels.get(phase, f"{phase}フェーズ")


def human_action(purpose: str) -> str:
    actions = {
        "context_loader init": "最初のコンテキスト取得",
        "context_loader advance": "次のコンテキスト取得",
        "context_loader phase-done": "フェーズ完了の記録",
        "context_loader repeat": "直前コンテキストの再表示",
        "context_loader status": "現在位置の確認",
        "context_loader validate": "設定の検証",
        "context_loader error": "エラー内容の記録",
        "manual event": "活動ログの追記",
        "gpt decision": "判断内容の記録",
        "code interpreter start": "code interpreter実行開始の記録",
        "code interpreter done": "code interpreter実行完了の記録",
        "code interpreter error": "code interpreter失敗の記録",
    }
    return actions.get(purpose, compact_text(purpose))


def human_result(result: str) -> str:
    text = compact_text(result)
    parts = text.split()
    if parts and parts[0] in {"NEXT", "DONE"}:
        status = parts[0]
        progress = parts[1] if len(parts) > 1 and "/" in parts[1] else ""
        if progress:
            current, total = progress.split("/", 1)
            current_num = int(current)
            total_num = int(total)
            if status == "NEXT":
                return f"全{total_num}件中{current_num}件目を読み取り、次の読み取りが必要な状態にしました"
            return f"全{total_num}件の読み取りを終え、このフェーズを作業可能な状態にしました"
        if status == "NEXT":
            return "次の読み取りが必要な状態にしました"
        return "このフェーズを作業可能な状態にしました"
    if text == "ROUTE_DONE":
        return "すべてのフェーズの読み取りを完了しました"
    if text.startswith("ROUTE_DONE "):
        return "すべてのフェーズの読み取りを完了しました"
    if text.startswith("STATUS "):
        return "現在の読み取り位置を確認しました"
    if text.startswith("OK "):
        return "検証は成功しました"
    if text.startswith("ERROR "):
        return f"エラーとして「{text}」を記録しました"
    return f"結果は「{text}」でした"


def human_io(inputs: list[str] | None, outputs: list[str] | None) -> str:
    input_items = [compact_text(item) for item in inputs or [] if compact_text(item)]
    output_items = [compact_text(item) for item in outputs or [] if compact_text(item)]
    input_text = "、".join(input_items)
    output_text = "、".join(output_items)
    if input_text and output_text:
        return f"入力として{input_text}を使い、出力として{output_text}を更新しました"
    if input_text:
        return f"入力として{input_text}を使いました"
    if output_text:
        return f"出力として{output_text}を更新しました"
    return ""


def append_log(
    phase: str,
    purpose: str,
    result: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
) -> None:
    try:
        result_text = human_result(result)
        if purpose in {"manual event", "gpt decision"} and not compact_text(result).startswith("ERROR "):
            result_text = f"内容として「{compact_text(result)}」を残しました"
        fragments = [
            f"{jst_timestamp()}（日本時間）に{human_phase(phase)}で{human_action(purpose)}を行い、{result_text}"
        ]
        io_text = human_io(inputs, outputs)
        if io_text:
            fragments.append(io_text)
        sentence = "、".join(fragments) + "。"
        with log_path().open("a", encoding="utf-8") as f:
            f.write("- " + sentence + "\n")
    except Exception:
        pass


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


def emit_next_chunk(data: dict[str, Any], state: dict[str, Any], command: str) -> None:
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
    append_log(
        phase,
        f"context_loader {command}",
        f"{status} {index + 1:03d}/{len(ids):03d} chunk={chunk_id}",
        inputs=["context_data.json"],
        outputs=[STATE_NAME],
    )
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
    emit_next_chunk(data, state, "init")


def advance(data: dict[str, Any], raw_ack: str | None) -> None:
    state = load_state()
    require_ack(state, raw_ack)
    if state.get("route_done"):
        raise SystemExit("ERROR route already DONE.")
    if state.get("phase_done"):
        raise SystemExit("ERROR phase is DONE. Do the phase work, then run: context_loader.py phase-done <ACK>")
    emit_next_chunk(data, state, "advance")


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
        append_log(phase, "context_loader phase-done", "ROUTE_DONE", outputs=[STATE_NAME])
        emit(f"ROUTE_DONE flow={state.get('flow')} phases={len(completed):03d}/{len(completed):03d}")
        return
    emit_next_chunk(data, state, "phase-done")


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
    append_log(phase, "context_loader repeat", f"{status} chunk={chunk_id}")
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
    append_log("status", "context_loader status", text)
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
        "ERROR legacy chunk API disabled. Use: init yes|no, advance <ACK>, phase-done <ACK>, repeat, status, validate, log-event <phase> <message>."
    )


def log_event(argv: list[str]) -> None:
    if len(argv) < 4:
        raise SystemExit("ERROR usage: log-event <phase> <message>")
    phase = argv[2]
    message = compact_text(" ".join(argv[3:]))
    if not message:
        raise SystemExit("ERROR usage: log-event <phase> <message>")
    append_log(phase, "manual event", message)
    emit("LOGGED")


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        emit("USAGE init yes|no|repair_emphasis|repair_density|repair_schema|repair_text|setup | advance <ACK> | phase-done <ACK> | repeat | status | validate | log-event <phase> <message>")
        return

    cmd = argv[1]
    if cmd in {"log-event", "log"}:
        log_event(argv)
        return

    data = load_data()
    if cmd == "init":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: init yes|no|repair_emphasis|repair_density|repair_schema|repair_text|setup")
        init_flow(data, argv[2])
    elif cmd == "repair":
        if len(argv) != 3:
            raise SystemExit("ERROR usage: repair emphasis|density|schema|text")
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
        append_log("validate", "context_loader validate", result)
        emit(result)
    elif cmd in LEGACY_COMMANDS or cmd in data.get("phases", {}):
        legacy_error()
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
