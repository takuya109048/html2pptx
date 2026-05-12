"""Manage the deck-from-source runtime Markdown checklist.

Custom GPTs may only expose about 800 console characters to the model, so
status-like commands intentionally print a compact summary.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 800
DEFAULT_NAME = "task_checklist.md"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


YES_ITEMS = [
    ("P01-T01", "yes_plan", "ソース分析と全体構成", "保存名、章立て、密度方針を決める"),
    ("P02-T01", "yes_schema", "JSON骨格作成", "root、summary、slides骨格を書く"),
    ("P03-T01", "yes_layout", "layout確定", "各スライドのlayoutと必須blocksを決める"),
    ("P04-T01", "yes_check_convert", "FINAL_SELF_CHECKと変換", "strict変換を通し成果物を作る"),
]

NO_ITEMS = [
    ("P01-T01", "no_plan", "ソース分析と全体構成", "保存名、章立て、密度方針を決める"),
    ("P02-T01", "no_schema", "JSON骨格作成", "root、summary、slides骨格を書く"),
    ("P03-T01", "no_layout", "layout確定", "各スライドのlayoutと必須blocksを決める"),
    ("P04-T01", "no_check_convert", "FINAL_SELF_CHECKと変換", "strict変換を通し成果物を作る"),
]

REPAIR_ITEMS = [
    ("R01-T01", "repair_emphasis", "太字修復", "strict-emphasis失敗箇所を直す"),
    ("R02-T01", "repair_density", "密度修復", "本文不足や薄いカードを直す"),
    ("R03-T01", "repair_text", "文字と構造修復", "文字化け、markup、block keyを直す"),
]

LINE_RE = re.compile(r"^(?P<indent>\s*)- \[(?P<mark>[ xX])\] (?P<id>[^|]+)(?P<meta>(?: \| .*)?)$")
SLIDE_ITEM_RE = re.compile(r"^S\d{3}-T\d{2}$")


def runtime_dir() -> Path:
    env_dir = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or os.environ.get("DECK_OUTPUT_DIR")
    if env_dir:
        path = Path(env_dir)
    else:
        mnt = Path("/mnt/data")
        path = mnt if os.name != "nt" and mnt.exists() else Path.cwd()
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_path() -> Path:
    return runtime_dir() / DEFAULT_NAME


def log_path() -> Path:
    return runtime_dir() / "code_interpreter_log.md"


def emit(text: str) -> None:
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:360] + "\n...\n" + text[-360:]
    print(text)


def append_log(phase: str, purpose: str, result: str, outputs: list[str] | None = None) -> None:
    try:
        record = {
            "time": _dt.datetime.now().isoformat(timespec="seconds"),
            "phase": phase,
            "purpose": purpose,
            "inputs": [DEFAULT_NAME],
            "outputs": outputs or [DEFAULT_NAME],
            "result": result,
        }
        with log_path().open("a", encoding="utf-8") as f:
            f.write("- " + json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def normalize_items(items: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in items:
        if isinstance(item, dict):
            item_id = str(item["id"])
            phase = str(item["phase"])
            ctx = str(item.get("ctx", phase))
            task = str(item["task"])
            done = str(item.get("done", "完了条件を満たす"))
        else:
            item_id, phase, task, done = item
            ctx = phase
        normalized.append({"id": item_id, "phase": phase, "ctx": ctx, "task": task, "done": done})
    return normalized


def clean_field(value: Any, max_len: int = 80) -> str:
    text = str(value or "").replace("\n", " ").replace("|", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def render_item(item: dict[str, str], checked: bool = False, indent: str = "") -> str:
    mark = "x" if checked else " "
    keys = ["phase", "ctx", "parent", "slide", "task", "done"]
    meta = " | ".join(f"{key}={item[key]}" for key in keys if item.get(key))
    return f"{indent}- [{mark}] {item['id']} | {meta}"


def init_checklist(path: str | Path | None = None, items: list[Any] | None = None, mode: str | None = None) -> Path:
    target = Path(path) if path else default_path()
    if items is None:
        selected = (mode or "yes").lower()
        if selected == "yes":
            items = YES_ITEMS + REPAIR_ITEMS
        elif selected == "no":
            items = NO_ITEMS + REPAIR_ITEMS
        else:
            raise SystemExit("ERROR mode must be yes or no")
    normalized = normalize_items(items)
    lines = [
        "# task_checklist",
        "",
        f"mode: {mode or 'custom'}",
        f"created: {_dt.datetime.now().isoformat(timespec='seconds')}",
        "",
    ]
    for item in normalized:
        lines.append(render_item(item))
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_log("checklist", "init", f"DONE items={len(normalized)}", outputs=[target.name])
    return target


def parse_meta(meta: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for part in meta.split("|"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def parse(path: str | Path | None = None) -> list[dict[str, str]]:
    target = Path(path) if path else default_path()
    if not target.exists():
        raise SystemExit(f"ERROR checklist not found: {target}")
    items: list[dict[str, str]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        data = {k: v.strip() for k, v in match.groupdict().items()}
        data.update(parse_meta(data.pop("meta", "")))
        data["checked"] = "1" if data["mark"].lower() == "x" else "0"
        for key in ["phase", "ctx", "task", "done", "parent", "slide"]:
            data.setdefault(key, "")
        items.append(data)
    return items


def primary_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return [item for item in items if not item["id"].startswith("R")]


def counts(items: list[dict[str, str]], primary_only: bool = False) -> tuple[int, int]:
    scoped = primary_items(items) if primary_only else items
    done = sum(1 for item in scoped if item["checked"] == "1")
    return done, len(scoped)


def next_item(items: list[dict[str, str]], primary_only: bool = True) -> dict[str, str] | None:
    scoped = primary_items(items) if primary_only else items
    return next((item for item in scoped if item["checked"] != "1"), None)


def format_status(items: list[dict[str, str]]) -> str:
    done, total = counts(items, primary_only=True)
    item = next_item(items)
    if not item:
        repair_total = len(items) - total
        return f"STATUS DONE primary={done}/{total} optional_repair={repair_total}"
    return (
        f"STATUS NEXT {done}/{total}\n"
        f"id={item['id']} phase={item['phase']} ctx={item['ctx']}\n"
        f"task={item['task']}\n"
        f"done={item['done']}"
    )


def show_status(path: str | Path | None = None) -> None:
    items = parse(path)
    text = format_status(items)
    phase = next_item(items)["phase"] if next_item(items) else "checklist"
    append_log(phase, "status", text.replace("\n", " / "))
    emit(text)


def show_next(path: str | Path | None = None) -> None:
    show_status(path)


def check_item(path: str | Path | None, item_id: str) -> None:
    target = Path(path) if path else default_path()
    text = target.read_text(encoding="utf-8")
    found = False
    phase = "checklist"
    new_lines: list[str] = []
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if match and match.group("id").strip() == item_id:
            found = True
            meta = parse_meta(match.group("meta"))
            phase = meta.get("phase", "checklist")
            line = line.replace("- [ ] ", "- [x] ", 1)
        new_lines.append(line)
    if not found:
        raise SystemExit(f"ERROR item not found: {item_id}")
    target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    items = parse(target)
    done, total = counts(items, primary_only=not item_id.startswith("R"))
    result = f"DONE item={item_id} progress={done}/{total}"
    append_log(phase, "check", result, outputs=[target.name])
    emit(result)


def detect_mode(path: Path, mode: str | None = None) -> str:
    selected = (mode or "").lower()
    if selected in {"yes", "no"}:
        return selected
    text = path.read_text(encoding="utf-8")
    match = re.search(r"^mode:\s*(yes|no)\s*$", text, flags=re.MULTILINE)
    if match:
        return match.group(1)
    items = parse(path)
    for item in items:
        if item["ctx"].startswith("yes_"):
            return "yes"
        if item["ctx"].startswith("no_"):
            return "no"
    raise SystemExit("ERROR mode not found; pass --mode yes or --mode no")


def resolve_source_json(source: str | Path | None) -> Path:
    if source:
        candidate = Path(source)
        if candidate.exists():
            return candidate
        runtime_candidate = runtime_dir() / candidate
        if runtime_candidate.exists():
            return runtime_candidate
        raise SystemExit(f"ERROR source json not found: {source}")
    matches = sorted(runtime_dir().glob("*deck_source.json"))
    if matches:
        return matches[0]
    raise SystemExit("ERROR source json not found")


def slide_context(mode: str) -> str:
    if mode == "yes":
        return "yes_image,yes_body,yes_emphasis,yes_notes"
    return "no_body,no_emphasis,no_notes"


def build_slide_items(source_json: Path, mode: str) -> list[dict[str, str]]:
    data = json.loads(source_json.read_text(encoding="utf-8-sig"))
    slides = data.get("slides")
    if not isinstance(slides, list) or not slides:
        raise SystemExit("ERROR source json has no slides array")
    items: list[dict[str, str]] = []
    for idx, slide in enumerate(slides, start=1):
        title = clean_field(slide.get("title") if isinstance(slide, dict) else "", 36) or f"slide {idx}"
        items.append(
            {
                "id": f"S{idx:03d}-T01",
                "phase": f"{mode}_slide_build",
                "ctx": slide_context(mode),
                "parent": "P03-T01",
                "slide": str(idx),
                "task": clean_field(f"スライド{idx}: {title} 作成・修正", 72),
                "done": "layout、blocks、強調、noteを1枚分完成",
            }
        )
    return items


def insert_slide_items(
    path: str | Path | None = None,
    source: str | Path | None = None,
    mode: str | None = None,
    replace: bool = False,
) -> None:
    target = Path(path) if path else default_path()
    if not target.exists():
        raise SystemExit(f"ERROR checklist not found: {target}")
    selected_mode = detect_mode(target, mode)
    source_json = resolve_source_json(source)
    slide_items = build_slide_items(source_json, selected_mode)
    lines = target.read_text(encoding="utf-8").splitlines()
    existing = [
        item["id"]
        for item in parse(target)
        if SLIDE_ITEM_RE.match(item["id"]) and item.get("parent") == "P03-T01"
    ]
    if existing and not replace:
        result = f"OK slide subitems already present count={len(existing)}"
        append_log("checklist", "insert-slides", f"{result} source={source_json.name}", outputs=[target.name])
        emit(result)
        return

    new_lines: list[str] = []
    inserted = False
    for line in lines:
        match = LINE_RE.match(line)
        item_id = match.group("id").strip() if match else ""
        if replace and SLIDE_ITEM_RE.match(item_id):
            continue
        new_lines.append(line)
        if item_id == "P03-T01":
            new_lines.extend(render_item(item, indent="  ") for item in slide_items)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR parent item not found: P03-T01")
    target.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    result = f"DONE insert-slides count={len(slide_items)} mode={selected_mode}"
    append_log("checklist", "insert-slides", f"{result} source={source_json.name}", outputs=[target.name])
    emit(result)


def verify(path: str | Path | None = None) -> None:
    items = parse(path)
    ids = [item["id"] for item in items]
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("duplicate_id")
    for item in items:
        if not item["ctx"]:
            errors.append(f"missing_ctx:{item['id']}")
        for ctx in [part.strip() for part in item["ctx"].split(",") if part.strip()]:
            if not re.match(r"^(yes|no|repair|setup)[A-Za-z0-9_]*$", ctx):
                errors.append(f"bad_ctx:{item['id']}:{ctx}")
    unfinished = [item["id"] for item in items if item["checked"] != "1" and not item["id"].startswith("R")]
    if unfinished:
        errors.append(f"unfinished:{','.join(unfinished[:3])}")
    done, total = counts(items, primary_only=True)
    if errors:
        result = f"ERROR issues={len(errors)} first={errors[0]} progress={done}/{total}"
    else:
        result = f"OK checklist progress={done}/{total} output<={MAX_OUTPUT_CHARS}"
    append_log("checklist", "verify", result)
    emit(result)
    if errors:
        raise SystemExit(1)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Manage task_checklist.md")
    parser.add_argument("command", choices=["init", "status", "next", "check", "verify", "insert-slides"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--path", default=None)
    parser.add_argument("--mode", choices=["yes", "no"], default=None)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args(argv[1:])

    if args.command == "init":
        mode = (args.value or "yes").lower()
        path = init_checklist(args.path, mode=mode)
        emit(f"OK checklist init mode={mode} file={path.name}")
    elif args.command == "status":
        show_status(args.path)
    elif args.command == "next":
        show_next(args.path)
    elif args.command == "check":
        if not args.value:
            raise SystemExit("ERROR usage: check <item_id>")
        check_item(args.path, args.value)
    elif args.command == "verify":
        verify(args.path)
    elif args.command == "insert-slides":
        insert_slide_items(args.path, args.value, mode=args.mode, replace=args.replace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
