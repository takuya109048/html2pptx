"""Convert stable deck_source.json into slide JSON and optionally PPTX."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from md_to_json import (
    LAYOUT_REQUIRED_TAGS,
    NANOBANANA_ICON_LAYOUTS,
    NANOBANANA_ICON_MARKER,
    build_cover_slide,
    invoke_to_pptx,
    load_json,
    validate_agenda_slide,
    validate_nanobanana_icon_prompts,
    validate_nanobanana_no_plain_1col,
)

CARD_TAGS = ["card-a", "card-b", "card-c", "card-d"]
STEP_TAGS = ["step-a", "step-b", "step-c", "step-d"]


def warn(message: str) -> None:
    print(f"[警告] {message}", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert deck_source.json to slide JSON and optionally PPTX."
    )
    parser.add_argument("input_json", type=Path, help="Input deck_source.json path.")
    parser.add_argument("output_pptx", nargs="?", type=Path, help="Output PPTX path.")
    parser.add_argument("--json", dest="output_json", type=Path, default=None)
    parser.add_argument("--templates", type=Path, default=Path(__file__).resolve().parent / "templates.json")
    parser.add_argument("--assets-dir", type=Path, default=None)
    parser.add_argument("--no-pptx", action="store_true")
    parser.add_argument("--nanobanana2", action="store_true")
    parser.add_argument("--require-agenda", action="store_true")
    parser.add_argument("--strict-blocks", action="store_true")
    return parser.parse_args()


def _find_prefixed(directory: Path, filename: str) -> Path:
    exact = directory / filename
    if exact.exists():
        return exact
    matches = list(directory.glob(f"assistant-*-{filename}"))
    return matches[0] if matches else exact


def load_source(path: Path, assets_dir: Path | None) -> dict[str, Any]:
    candidates = [path]
    if assets_dir is not None:
        candidates.append(assets_dir / path.name)
        candidates.append(_find_prefixed(assets_dir, path.name))
    for candidate in candidates:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("deck_source.json root must be an object.")
            return data
    raise FileNotFoundError(path)


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value)


def split_heading(markdown: str) -> tuple[str, str]:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("### "):
            return stripped[4:].strip(), "\n".join(lines[index + 1 :]).strip()
        if stripped.startswith("## "):
            return stripped[3:].strip(), "\n".join(lines[index + 1 :]).strip()
    return "", markdown.strip()


def table_payload(value: Any) -> tuple[list[str], list[list[str]]]:
    if isinstance(value, dict):
        head = value.get("head", [])
        rows = value.get("rows", [])
    elif isinstance(value, list) and value:
        head = value[0]
        rows = value[1:]
    else:
        head, rows = [], []
    return [str(c) for c in head], [[str(c) for c in row] for row in rows]


def note_with_icon(slide_def: dict[str, Any], nanobanana2: bool) -> str:
    note = as_text(slide_def.get("note")).strip()
    layout = str(slide_def.get("layout", "")).strip()
    icon_prompt = as_text(slide_def.get("icon_prompt")).strip()
    if nanobanana2 and layout in NANOBANANA_ICON_LAYOUTS:
        if icon_prompt and NANOBANANA_ICON_MARKER not in note:
            note = f"{note}\n\n---\n\n{NANOBANANA_ICON_MARKER}\n{icon_prompt}".strip()
    return note


def validate_source(source: dict[str, Any], nanobanana2: bool, strict_blocks: bool) -> int:
    errors = 0
    body_slides = source.get("slides", [])
    if not isinstance(body_slides, list) or not body_slides:
        warn("deck_source.json must contain a non-empty slides array.")
        return 1
    for index, slide in enumerate(body_slides, start=3):
        if not isinstance(slide, dict):
            warn(f"Slide #{index} must be an object.")
            errors += 1
            continue
        layout = str(slide.get("layout", "")).strip()
        title = str(slide.get("title", "")).strip()
        blocks = slide.get("blocks", {})
        if not isinstance(blocks, dict):
            warn(f"Slide #{index} blocks must be an object." + (f" Title: {title}" if title else ""))
            errors += 1
            continue
        required = LAYOUT_REQUIRED_TAGS.get(layout)
        if not required:
            warn(f"Slide #{index} uses unknown layout '{layout}'." + (f" Title: {title}" if title else ""))
            errors += 1
            continue
        if strict_blocks:
            for tag in required:
                if tag not in blocks:
                    warn(f"Slide #{index} layout '{layout}' is missing block '{tag}'." + (f" Title: {title}" if title else ""))
                    errors += 1
        if nanobanana2:
            if index >= 3 and layout == "plain_1col":
                warn(f"Slide #{index} uses plain_1col while nanobanana2 is enabled." + (f" Title: {title}" if title else ""))
                errors += 1
            if layout in NANOBANANA_ICON_LAYOUTS:
                prompt = as_text(slide.get("icon_prompt")).strip()
                if not prompt:
                    warn(f"Slide #{index} layout '{layout}' is missing icon_prompt." + (f" Title: {title}" if title else ""))
                    errors += 1
                elif "6:5" in prompt:
                    warn(f"Slide #{index} layout '{layout}' icon_prompt uses 6:5. Use 3:1 or 4:1." + (f" Title: {title}" if title else ""))
                    errors += 1
    return errors


def build_agenda_slide(source: dict[str, Any], templates: dict[str, Any]) -> dict[str, Any]:
    agenda = copy.deepcopy(templates["plain_2col"]["SLIDES"][0])
    agenda["layout"] = "plain_2col"
    agenda["header"]["title"] = "目次"
    agenda["header"]["message"] = "構成を章ごとにたどる"
    agenda["logo"] = "logo.png"
    agenda["note"] = "本資料の流れを確認する。目次の小見出しは各スライドタイトルから自動生成しているため、本文スライドとの不一致を避けられる。"
    slides = [s for s in source.get("slides", []) if isinstance(s, dict)]
    grouped: list[tuple[str, list[str]]] = []
    for slide in slides:
        section = str(slide.get("section", "本編")).strip() or "本編"
        title = str(slide.get("title", "")).strip()
        if not title:
            continue
        if not grouped or grouped[-1][0] != section:
            grouped.append((section, []))
        grouped[-1][1].append(title)
    left_groups = grouped[:]
    right_groups: list[tuple[str, list[str]]] = []
    total_items = sum(len(items) for _, items in left_groups)
    while total_items > 5 and len(left_groups) > 1:
        moved = left_groups.pop()
        right_groups.insert(0, moved)
        total_items = sum(len(items) for _, items in left_groups)

    def render_groups(groups: list[tuple[str, list[str]]], fallback: str) -> str:
        if not groups:
            return fallback
        parts = []
        for section, titles in groups:
            parts.append(f"### {section}")
            parts.extend(f"- {title}" for title in titles)
        return "\n".join(parts)

    agenda["grid"][0][0]["markdown"] = render_groups(left_groups, "### 本編")
    agenda["grid"][0][1]["markdown"] = render_groups(right_groups, "### overflow")
    return agenda


def build_content_slide(slide_def: dict[str, Any], templates: dict[str, Any], nanobanana2: bool) -> dict[str, Any]:
    layout = str(slide_def.get("layout", "")).strip()
    slide = copy.deepcopy(templates[layout]["SLIDES"][0])
    slide["layout"] = layout
    slide["logo"] = "logo.png"
    if isinstance(slide.get("header"), dict):
        slide["header"]["title"] = str(slide_def.get("title", ""))
        slide["header"]["message"] = str(slide_def.get("message", ""))
    note = note_with_icon(slide_def, nanobanana2)
    if note:
        slide["note"] = note
    blocks = slide_def.get("blocks", {})
    step_labels: dict[str, str] = {}
    step_bodies: dict[str, str] = {}
    for tag in STEP_TAGS:
        heading, body = split_heading(as_text(blocks.get(tag)))
        step_labels[tag] = heading
        step_bodies[tag] = body or as_text(blocks.get(tag))
    card_cursor = 0
    step_cursor = 0
    plain_cursor = 0
    for row in slide.get("grid", []):
        if not isinstance(row, list):
            continue
        for cell in row:
            if not isinstance(cell, dict):
                continue
            cell_type = cell.get("type")
            if cell_type == "step_head":
                tag = STEP_TAGS[step_cursor] if step_cursor < len(STEP_TAGS) else ""
                cell["markdown"] = step_labels.get(tag) or as_text(blocks.get(tag))
                step_cursor += 1
            elif cell_type == "card":
                if layout in {"flow_3step", "flow_4step"}:
                    tag = STEP_TAGS[card_cursor] if card_cursor < len(STEP_TAGS) else ""
                    cell["markdown"] = step_bodies.get(tag, "")
                else:
                    tag = CARD_TAGS[card_cursor] if card_cursor < len(CARD_TAGS) else ""
                    cell["markdown"] = as_text(blocks.get(tag))
                card_cursor += 1
            elif cell_type == "plain":
                tag = CARD_TAGS[plain_cursor] if plain_cursor < len(CARD_TAGS) else ""
                cell["markdown"] = as_text(blocks.get(tag))
                plain_cursor += 1
            elif cell_type in {"section", "conclusion"}:
                cell["markdown"] = as_text(blocks.get(cell_type))
            elif cell_type in {"table", "matrix", "flow_matrix", "h_flow_matrix", "compare"}:
                head, rows = table_payload(blocks.get(cell_type))
                cell["head"] = head
                cell["rows"] = rows
    return slide


def convert_source_to_slides(source: dict[str, Any], templates: dict[str, Any], nanobanana2: bool) -> list[dict[str, Any]]:
    cover_meta = {
        "title": source.get("title", ""),
        "message": source.get("subtitle", ""),
        "affiliation": source.get("affiliation", ""),
        "presenter": source.get("presenter", ""),
        "date": source.get("date", ""),
        "note": source.get("note", ""),
    }
    slides = [build_cover_slide(cover_meta), build_agenda_slide(source, templates)]
    for slide_def in source.get("slides", []):
        slides.append(build_content_slide(slide_def, templates, nanobanana2))
    return slides


def main() -> int:
    args = parse_args()
    assets_dir = args.assets_dir
    if assets_dir is not None and args.templates == Path(__file__).resolve().parent / "templates.json":
        args.templates = _find_prefixed(assets_dir, "templates.json")
    templates = load_json(args.templates)
    if not templates:
        return 1
    try:
        source = load_source(args.input_json, assets_dir)
    except Exception as exc:
        warn(f"Failed to read deck_source.json: {exc}")
        return 1
    errors = validate_source(source, args.nanobanana2, args.strict_blocks)
    if errors:
        warn(f"deck_source validation failed: {errors} error(s).")
        return 1
    slides = convert_source_to_slides(source, templates, args.nanobanana2)
    if args.require_agenda and validate_agenda_slide(slides):
        return 1
    if args.nanobanana2:
        if validate_nanobanana_no_plain_1col(slides):
            return 1
        if validate_nanobanana_icon_prompts(slides):
            return 1
    output_json = args.output_json or args.input_json.with_suffix(".slides.json")
    output_json.write_text(json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.no_pptx:
        print(str(output_json))
        return 0
    output_pptx = args.output_pptx or args.input_json.with_suffix(".pptx")
    rc = invoke_to_pptx(slides, output_pptx, assets_dir)
    if rc:
        return rc
    print(str(output_pptx))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
