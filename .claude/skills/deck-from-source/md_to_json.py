"""Convert Markdown slide decks into JSON slide objects using templates."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SECTION_LINE_RE = re.compile(r"(?m)^##\s+(.*)$")
FENCE_OPEN_RE  = re.compile(r"(?m)^```([\w-]+)\s*$")
FENCE_CLOSE_RE = re.compile(r"(?m)^```\s*$")
TABLE_SEPARATOR_RE = re.compile(
    r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$"
)

CARD_TAGS = ["card-a", "card-b", "card-c", "card-d"]
STEP_TAGS = ["step-a", "step-b", "step-c", "step-d"]
CONTENT_SECTION_TAGS = set(CARD_TAGS + STEP_TAGS + ["section", "conclusion", "table", "matrix", "flow_matrix", "h_flow_matrix", "compare"])


def warn(message: str) -> None:
    """Print a non-fatal warning."""
    print(f"[警告] {message}", file=sys.stderr)


def _find_prefixed(directory: Path, filename: str) -> Path:
    """カスタムGPTs環境の assistant-{id}- プレフィックスに対応したファイル検索。"""
    exact = directory / filename
    if exact.exists():
        return exact
    matches = list(directory.glob(f"assistant-*-{filename}"))
    return matches[0] if matches else exact


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Convert markdown slide deck to JSON and optionally PPTX."
    )
    parser.add_argument("input_md", type=Path, help="Input markdown file path.")
    parser.add_argument(
        "output_pptx",
        nargs="?",
        type=Path,
        help="Output PPTX file path (default: same name as input with .pptx).",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        type=Path,
        default=None,
        help="Output JSON file path.",
    )
    parser.add_argument(
        "--templates",
        type=Path,
        default=Path(__file__).resolve().parent / "templates.json",
        help="Path to templates.json (default: project root).",
    )
    parser.add_argument(
        "--no-pptx",
        action="store_true",
        help="Skip PPTX conversion and output JSON only.",
    )
    parser.add_argument(
        "--assets-dir",
        dest="assets_dir",
        type=Path,
        default=None,
        help="Directory containing to_pptx.py, templates.json, logo.png, etc. (default: script directory).",
    )
    return parser.parse_args()


def parse_slide_blocks(markdown_text: str) -> list[dict[str, Any]]:
    """Parse markdown text into slide blocks separated by lines containing only '---'."""
    blocks: list[dict[str, Any]] = []
    current_lines: list[str] = []

    def flush_block(lines: list[str]) -> None:
        metadata: dict[str, Any] = {}
        body_lines = lines[:]

        cursor = 0
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

        # New slide header format:
        # 1) "# title"
        # 2) optional "## message" before metadata table
        # 3) metadata table for layout and other keys
        if cursor < len(lines):
            title_match = re.match(r"^\s*#\s+(.+?)\s*$", lines[cursor])
            if title_match:
                metadata["title"] = title_match.group(1).strip()
                cursor += 1

                while cursor < len(lines) and not lines[cursor].strip():
                    cursor += 1

                if cursor < len(lines):
                    message_match = re.match(r"^\s*##\s+(.+?)\s*$", lines[cursor])
                    if message_match:
                        metadata["message"] = message_match.group(1).strip()
                        cursor += 1

        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1

        if cursor + 1 < len(lines):
            header_line = lines[cursor].strip()
            separator_line = lines[cursor + 1].strip()
            if is_table_row(header_line) and TABLE_SEPARATOR_RE.match(separator_line):
                end = cursor + 2
                while end < len(lines) and is_table_row(lines[end]):
                    end += 1

                table_lines = [line.strip() for line in lines[cursor:end]]
                for raw in table_lines[2:]:
                    if TABLE_SEPARATOR_RE.match(raw):
                        continue
                    cells = [cell.strip() for cell in raw.strip("|").split("|")]
                    if len(cells) >= 2 and cells[0]:
                        key = cells[0]
                        if key == "image" or (key.startswith("image_") and not key.startswith("image_label_")):
                            continue
                        metadata[key] = "|".join(cells[1:]).strip()
                body_lines = lines[end:]

        body = "\n".join(body_lines).strip()
        if metadata or body:
            blocks.append({"front_matter": metadata, "body": body})

    for raw_line in markdown_text.splitlines():
        if raw_line.strip() == "---":
            flush_block(current_lines)
            current_lines = []
            continue
        current_lines.append(raw_line)

    flush_block(current_lines)
    return blocks


def parse_sections(body: str) -> list[dict[str, str]]:
    """Parse :::tag fenced blocks from slide body."""
    content = body.strip()
    if not content:
        return []
    sections: list[dict[str, str]] = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        m = FENCE_OPEN_RE.match(lines[i])
        if m:
            tag = m.group(1).strip()
            i += 1
            body_lines: list[str] = []
            while i < len(lines):
                if FENCE_CLOSE_RE.match(lines[i]):
                    i += 1
                    break
                body_lines.append(lines[i])
                i += 1
            sections.append({"tag": tag, "body": "\n".join(body_lines).strip()})
        else:
            i += 1
    return sections


def is_table_row(line: str) -> bool:
    """Check if a line looks like a markdown table row."""
    stripped = line.strip()
    return stripped.startswith("|") and "|" in stripped[1:]


def split_markdown_table(body: str) -> tuple[list[str], list[list[str]], str]:
    """Extract first markdown table and return remaining body."""
    lines = body.splitlines()
    start = -1
    end = -1

    for i in range(len(lines) - 1):
        line = lines[i].strip()
        next_line = lines[i + 1].strip()
        if is_table_row(line) and TABLE_SEPARATOR_RE.match(next_line):
            start = i
            end = i + 2
            while end < len(lines) and is_table_row(lines[end]):
                end += 1
            break

    if start == -1:
        return [], [], body

    table_lines = lines[start:end]
    parsed_rows: list[list[str]] = []
    for raw in table_lines:
        stripped = raw.strip()
        if not stripped or TABLE_SEPARATOR_RE.match(stripped):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        parsed_rows.append(cells)

    if not parsed_rows:
        return [], [], body

    head = parsed_rows[0]
    rows = parsed_rows[1:]
    remaining_lines = lines[:start] + lines[end:]
    remaining_body = "\n".join(remaining_lines).strip()
    return head, rows, remaining_body


def parse_markdown_matrix(body: str) -> list[list[str]]:
    """Extract pipe-delimited rows for matrix content, skipping separator rows."""
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or not is_table_row(stripped) or TABLE_SEPARATOR_RE.match(stripped):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows


def section_map(sections: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    """Build a tag -> section mapping. Last section with same tag wins."""
    result: dict[str, dict[str, str]] = {}
    for section in sections:
        result[section["tag"]] = section
    return result


def apply_layout_mapping(
    layout: str,
    front_matter: dict[str, Any],
    body: str,
    slide_template: dict[str, Any],
) -> dict[str, Any]:
    """Apply content mapping from markdown tags to a slide skeleton."""
    slide = copy.deepcopy(slide_template)
    slide["layout"] = layout

    header = slide.get("header")
    if isinstance(header, dict):
        header["title"] = str(front_matter.get("title", header.get("title", "")))
        header["message"] = str(front_matter.get("message", header.get("message", "")))

    slide["logo"] = "logo.png"
    note_val = front_matter.get("note", "")
    if note_val:
        slide["note"] = str(note_val)

    sections = parse_sections(body)
    tags = section_map(sections)

    grid = slide.get("grid", [])
    if not isinstance(grid, list):
        warn(f"Layout '{layout}': grid is not a list. Returning slide as-is.")
        return slide

    step_head_cursor = 0
    flow_step_cursor = 0
    normal_card_cursor = 0
    plain_cursor = 0
    image_cursor = 1

    for row in grid:
        if not isinstance(row, list):
            continue
        for cell in row:
            if not isinstance(cell, dict):
                continue
            cell_type = cell.get("type")

            if cell_type == "step_head":
                if step_head_cursor < len(STEP_TAGS):
                    section = tags.get(STEP_TAGS[step_head_cursor])
                    if section is not None:
                        cell["label"] = section["tag"]
                step_head_cursor += 1
                continue

            if cell_type == "card":
                if layout in {"flow_3step", "flow_4step"}:
                    if flow_step_cursor < len(STEP_TAGS):
                        section = tags.get(STEP_TAGS[flow_step_cursor])
                        if section is not None:
                            cell["markdown"] = section["body"]
                    flow_step_cursor += 1
                else:
                    if normal_card_cursor < len(CARD_TAGS):
                        section = tags.get(CARD_TAGS[normal_card_cursor])
                        if section is not None:
                            cell["markdown"] = section["body"]
                    normal_card_cursor += 1
                continue

            if cell_type == "plain":
                if plain_cursor < len(CARD_TAGS):
                    section = tags.get(CARD_TAGS[plain_cursor])
                    if section is not None:
                        cell["markdown"] = section["body"]
                plain_cursor += 1
                continue

            if cell_type == "section":
                section = tags.get("section")
                if section is not None:
                    cell["markdown"] = section["body"]
                continue

            if cell_type == "conclusion":
                section = tags.get("conclusion")
                if section is not None:
                    cell["markdown"] = section["body"]
                continue

            if cell_type == "table":
                section = tags.get("table")
                if section is None:
                    warn(f"Layout '{layout}': missing ':::table' section.")
                    continue
                head, rows, _ = split_markdown_table(section["body"])
                if not head:
                    warn(f"Layout '{layout}': ':::table' has no markdown table.")
                    continue
                cell["head"] = head
                cell["rows"] = rows
                continue

            if cell_type in ("matrix", "flow_matrix", "h_flow_matrix", "compare"):
                tag_name = cell_type
                section = tags.get(tag_name) or tags.get("matrix")
                if section is None:
                    warn(f"Layout '{layout}': missing '```{tag_name}' section.")
                    continue
                rows = parse_markdown_matrix(section["body"])
                if not rows:
                    warn(f"Layout '{layout}': '```{tag_name}' has no pipe-delimited rows.")
                    continue
                # 1行目を列ヘッダー(head)、残りをデータ行(rows)として分割
                cell["head"] = rows[0]
                cell["rows"] = rows[1:]
                continue

            if cell_type == "image":
                image_key = f"image_{image_cursor}"
                image_val = front_matter.get(image_key)
                if image_val:
                    cell["src"] = str(image_val)
                label_key = f"image_label_{image_cursor}"
                label_val = front_matter.get(label_key)
                if label_val:
                    cell["markdown"] = str(label_val)
                image_cursor += 1
                continue

            if cell_type == "arrow":
                continue

    return slide


def build_cover_slide(front_matter: dict[str, Any]) -> dict[str, Any]:
    """Build a cover slide directly from metadata."""
    slide = {
        "layout": "cover",
        "title": str(front_matter.get("title", "")),
        "affiliation": str(front_matter.get("affiliation", "")),
        "presenter": "山田 花子",
        "date": str(front_matter.get("date", "")),
        "bg": str(front_matter.get("bg", "background.png")),
    }
    note_val = front_matter.get("note", "")
    if note_val:
        slide["note"] = str(note_val)
    return slide


def convert_markdown_to_slides(
    markdown_text: str, templates: dict[str, Any]
) -> list[dict[str, Any]]:
    """Convert markdown deck text to slide JSON array."""
    blocks = parse_slide_blocks(markdown_text)
    slides: list[dict[str, Any]] = []

    for index, block in enumerate(blocks, start=1):
        front_matter = block.get("front_matter", {})
        body = str(block.get("body", ""))
        layout = str(front_matter.get("layout", "")).strip()
        if not layout:
            warn(f"Block #{index}: missing layout. Skipped.")
            continue

        if layout == "cover":
            slides.append(build_cover_slide(front_matter))
            continue

        template_entry = templates.get(layout)
        if not isinstance(template_entry, dict):
            warn(f"Block #{index}: layout '{layout}' not found in templates. Skipped.")
            continue

        slide_defs = template_entry.get("SLIDES")
        if not isinstance(slide_defs, list) or not slide_defs:
            warn(f"Block #{index}: layout '{layout}' has invalid SLIDES template. Skipped.")
            continue

        base_slide = slide_defs[0]
        if not isinstance(base_slide, dict):
            warn(f"Block #{index}: layout '{layout}' first template slide is invalid.")
            continue

        converted = apply_layout_mapping(layout, front_matter, body, base_slide)
        converted.pop("page", None)
        slides.append(converted)

    return slides


def load_json(path: Path) -> dict[str, Any]:
    """Load JSON file and return mapping."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        warn(f"Templates file is not a JSON object: {path}")
        return {}
    except Exception as exc:
        warn(f"Failed to read JSON file '{path}': {exc}")
        return {}


def resolve_output_json_path(
    input_md: Path, explicit_output_json: Path | None, no_pptx: bool
) -> tuple[Path, bool]:
    """Resolve JSON output path. Returns (path, is_temporary)."""
    if explicit_output_json is not None:
        return explicit_output_json, False
    if no_pptx:
        return input_md.with_suffix(".json"), False

    tmp_dir = input_md.parent if input_md.parent.exists() else None
    fd, tmp_name = tempfile.mkstemp(
        prefix=f"{input_md.stem}_", suffix=".json", dir=tmp_dir
    )
    # We only need the path. The file is written later.
    os.close(fd)
    return Path(tmp_name), True


def resolve_output_pptx_path(input_md: Path, explicit_output_pptx: Path | None) -> Path:
    """Resolve PPTX output path."""
    if explicit_output_pptx is not None:
        return explicit_output_pptx
    return input_md.with_suffix(".pptx")


def invoke_to_pptx(slides: list[dict[str, Any]], output_pptx: Path, assets_dir: Path | None = None) -> int:
    """Call to_pptx.py through subprocess with temporary template injection."""
    project_root = assets_dir.resolve() if assets_dir is not None else Path(__file__).resolve().parent
    to_pptx_path = _find_prefixed(project_root, "to_pptx.py")
    templates_path = project_root / "templates.json"  # 書き込みターゲットは常にクリーン名
    generated_key = "__md_to_json_generated__"
    generated_name = "Generated from markdown"
    generated_pptx = project_root / f"{generated_key}.pptx"
    backup_templates = templates_path.read_bytes() if templates_path.exists() else None
    payload = {
        generated_key: {
            "name": generated_name,
            "engine": "area",
            "SLIDES": slides,
        }
    }

    try:
        templates_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        command = [sys.executable, str(to_pptx_path), generated_key]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                check=False,
            )
        except PermissionError:
            # Some environments expose a non-launchable sys.executable.
            fallback_command = ["python", str(to_pptx_path), generated_key]
            result = subprocess.run(
                fallback_command,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                check=False,
            )
        if result.returncode != 0:
            warn("to_pptx.py failed.")
            if result.stdout.strip():
                warn(f"to_pptx stdout:\n{result.stdout.strip()}")
            if result.stderr.strip():
                warn(f"to_pptx stderr:\n{result.stderr.strip()}")
            return result.returncode

        if not generated_pptx.exists():
            warn(f"Expected PPTX not found: {generated_pptx}")
            return 1

        output_pptx.parent.mkdir(parents=True, exist_ok=True)
        if output_pptx.resolve() != generated_pptx.resolve():
            shutil.move(str(generated_pptx), str(output_pptx))
        return 0
    finally:
        if backup_templates is not None:
            templates_path.write_bytes(backup_templates)
        else:
            try:
                templates_path.unlink()
            except FileNotFoundError:
                pass
        try:
            if generated_pptx.exists():
                generated_pptx.unlink()
        except OSError:
            pass


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    if args.assets_dir is not None and args.templates == Path(__file__).resolve().parent / "templates.json":
        args.templates = _find_prefixed(args.assets_dir, "templates.json")
    templates = load_json(args.templates)
    if not templates:
        warn("No templates loaded. Output will be empty.")

    try:
        markdown_text = args.input_md.read_text(encoding="utf-8")
    except Exception as exc:
        warn(f"Failed to read input markdown '{args.input_md}': {exc}")
        markdown_text = ""

    slides = convert_markdown_to_slides(markdown_text, templates)
    output_json, json_is_temp = resolve_output_json_path(
        args.input_md, args.output_json, args.no_pptx
    )

    try:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(
            json.dumps(slides, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except Exception as exc:
        warn(f"Failed to write output JSON '{output_json}': {exc}")
        return 1

    if args.no_pptx:
        print(str(output_json))
        return 0

    output_pptx = resolve_output_pptx_path(args.input_md, args.output_pptx)
    rc = invoke_to_pptx(slides, output_pptx, args.assets_dir)
    if rc != 0:
        return rc

    if json_is_temp:
        try:
            output_json.unlink()
        except OSError:
            pass
    print(str(output_pptx))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
