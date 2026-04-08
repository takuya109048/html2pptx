from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

EM_RATIO = 0.5  # em per display unit (1 wide char = 1em = 2 units → 0.5em/unit)
LINE_SPACING = 1.35
WARN_RATIO = 0.1

RED_BOLD = "\033[1;31m"
YELLOW = "\033[33m"
RESET = "\033[0m"

_INLINE_RE = re.compile(r"\*\*([^*\n]+?)\*\*|\*([^*\n]+?)\*|~~([^~\n]+?)~~|`([^`\n]+?)`")
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)")
_BULLET_RE = re.compile(r"^\s{0,3}[-*+]\s+(.+)")
_BULLET2_RE = re.compile(r"^\s{4,}[-*+]\s+(.+)")
_ORDERED_RE = re.compile(r"^\s{0,3}\d+\.\s+(.+)")
_BLOCKQUOTE_RE = re.compile(r"^>\s*(.+)")
_CARD_TITLE_RE = re.compile(r"^\s{0,3}#{2,3}\s+(.+?)\s*$")


@dataclass
class CellGeom:
    cell: dict
    x: float
    y: float
    w: float
    h: float


@dataclass
class CellResult:
    slide_idx: int
    layout: str
    cell_label: str
    zone: str
    content_w: float
    content_h: float
    chars_per_line: int
    max_lines: int
    max_line_width: int
    line_count: int
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check text overflow for markdown slide deck.")
    parser.add_argument("deck_md", help="Path to markdown deck file.")
    parser.add_argument("--em-ratio", type=float, default=EM_RATIO)
    parser.add_argument("--line-spacing", type=float, default=LINE_SPACING)
    parser.add_argument("--warn-ratio", type=float, default=WARN_RATIO)
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--project-root", default=None)
    return parser.parse_args()


def char_width(ch: str) -> int:
    eaw = unicodedata.east_asian_width(ch)
    return 2 if eaw in ("W", "F", "A") else 1


def visual_width(s: str) -> int:
    return sum(char_width(c) for c in s)


def strip_inline_md(text: str) -> str:
    return _INLINE_RE.sub(lambda m: next(g for g in m.groups() if g is not None), text)


def parse_md_lines(markdown: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in markdown.splitlines():
        line = raw.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue

        m = _HEADING_RE.match(stripped)
        if m:
            out.append(("heading", strip_inline_md(m.group(1).strip())))
            continue

        m = _BULLET2_RE.match(line)
        if m:
            out.append(("bullet2", strip_inline_md("  - " + m.group(1).strip())))
            continue

        m = _BULLET_RE.match(line)
        if m:
            out.append(("bullet", strip_inline_md("- " + m.group(1).strip())))
            continue

        m = _ORDERED_RE.match(line)
        if m:
            out.append(("ordered", strip_inline_md("N. " + m.group(1).strip())))
            continue

        m = _BLOCKQUOTE_RE.match(stripped)
        if m:
            out.append(("blockquote", strip_inline_md("> " + m.group(1).strip())))
            continue

        out.append(("para", strip_inline_md(stripped)))
    return out


def measure_text(lines: list[tuple[str, str]], chars_per_line: int) -> tuple[int, int]:
    max_w = 0
    total = 0
    for _, text in lines:
        w = visual_width(text)
        max_w = max(max_w, w)
        total += max(1, math.ceil(w / chars_per_line)) if chars_per_line > 0 else 1
    return max_w, total


def calc_status(max_w: int, cpl: int, act_lines: int, max_lines: int, warn_ratio: float) -> str:
    # PPTX text boxes always word-wrap, so width alone does not cause overflow.
    # Status is determined solely by line count vs max_lines.
    # max_w > cpl contributes WARN only (text is wide but still wraps).
    l_over = act_lines > max_lines
    l_warn = (act_lines > max_lines * (1 - warn_ratio)) if not l_over else False
    w_warn = max_w > cpl
    if l_over:
        return "OVERFLOW"
    if l_warn or w_warn:
        return "WARN"
    return "OK"


def compute_cells(slide_data: dict[str, Any], l: dict[str, float]) -> list[CellGeom]:
    grid = slide_data.get("grid")
    if not isinstance(grid, list) or not grid:
        return []

    main_x = l["mainPadX"]
    main_y = l["headerH"] + l["mainPadY"]
    main_w = l["slideW"] - l["mainPadX"] * 2
    main_h = l["footerY"] - main_y - l["mainPadY"]
    gap = l["gridGap"]
    num_rows = len(grid)
    num_cols = max(sum(c.get("span", 1) for c in row) for row in grid)
    ratios = slide_data.get("rowHeightRatios", [1.0 / num_rows] * num_rows)
    row_heights = [main_h * r for r in ratios]

    def row_top(r: int) -> float:
        return main_y + sum(row_heights[:r])

    unit_w = (main_w - gap * (num_cols + 1)) / num_cols
    out: list[CellGeom] = []
    for ri, row in enumerate(grid):
        col = 0
        for cell in row:
            span = cell.get("span", 1)
            cx = main_x + gap + col * (unit_w + gap)
            cy = row_top(ri) + (gap if ri == 0 else gap / 2)
            cw = unit_w * span + gap * (span - 1)
            ch = row_heights[ri] - (gap if ri == 0 else gap / 2) - (gap if ri == num_rows - 1 else gap / 2)
            out.append(CellGeom(cell=cell, x=cx, y=cy, w=cw, h=ch))
            col += span
    return out


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected: {path}")
    return data


def convert_with_import(deck_path: Path, templates: dict[str, Any], project_root: Path) -> list[dict[str, Any]]:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    module = importlib.import_module("md_to_json")
    convert_fn = getattr(module, "convert_markdown_to_slides")
    markdown_text = deck_path.read_text(encoding="utf-8")
    slides = convert_fn(markdown_text, templates)
    if not isinstance(slides, list):
        raise ValueError("convert_markdown_to_slides must return list")
    return slides


def convert_with_fallback(deck_path: Path, project_root: Path) -> list[dict[str, Any]]:
    md_to_json = project_root / "md_to_json.py"
    if not md_to_json.exists():
        raise FileNotFoundError(f"md_to_json.py not found: {md_to_json}")

    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False, encoding="utf-8") as tf:
        tmp_json = Path(tf.name)
    try:
        cmd = [sys.executable, str(md_to_json), str(deck_path), "--json", str(tmp_json), "--no-pptx"]
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            cmd2 = ["python", str(md_to_json), str(deck_path), "--json", str(tmp_json), "--no-pptx"]
            result = subprocess.run(cmd2, cwd=str(project_root), capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"fallback conversion failed: {result.stderr.strip() or result.stdout.strip()}")
        with tmp_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("fallback json must be list")
        return data
    finally:
        try:
            tmp_json.unlink()
        except OSError:
            pass


def chars_per_line(content_w: float, font_size: float, em_ratio: float) -> int:
    if content_w <= 0 or font_size <= 0 or em_ratio <= 0:
        return 0
    return max(1, int(math.floor((content_w * 72.0) / (font_size * em_ratio))))


def max_lines(content_h: float, font_size: float, line_spacing: float) -> int:
    if content_h <= 0 or font_size <= 0 or line_spacing <= 0:
        return 0
    return max(1, int(math.floor((content_h * 72.0) / (font_size * line_spacing))))


def measure_zone(
    text: str,
    content_w: float,
    content_h: float,
    font_size: float,
    em_ratio: float,
    line_spacing: float,
    warn_ratio: float,
) -> tuple[int, int, int, int, str]:
    cpl = chars_per_line(content_w, font_size, em_ratio)
    mlines = max_lines(content_h, font_size, line_spacing)
    lines = parse_md_lines(text)
    if not lines:
        return cpl, mlines, 0, 0, "OK"

    bq_cpl = chars_per_line(max(content_w - 0.25, 0.0), font_size, em_ratio)
    max_w = 0.0
    act_l = 0
    for kind, line_text in lines:
        w = visual_width(line_text)
        local_cpl = cpl
        if kind == "blockquote":
            local_cpl = bq_cpl
            if cpl > 0 and local_cpl > 0:
                w = w * (cpl / local_cpl)
        max_w = max(max_w, w)
        act_l += max(1, math.ceil(w / local_cpl)) if local_cpl > 0 else 1

    max_w_int = int(math.ceil(max_w))
    return cpl, mlines, max_w_int, act_l, calc_status(max_w_int, cpl, act_l, mlines, warn_ratio)


def make_result(
    slide_idx: int,
    layout: str,
    cell_label: str,
    zone: str,
    content_w: float,
    content_h: float,
    font_size: float,
    text: str,
    em_ratio: float,
    line_spacing: float,
    warn_ratio: float,
) -> CellResult:
    cpl, ml, mw, al, status = measure_zone(text, content_w, content_h, font_size, em_ratio, line_spacing, warn_ratio)
    return CellResult(
        slide_idx=slide_idx,
        layout=layout,
        cell_label=cell_label,
        zone=zone,
        content_w=content_w,
        content_h=content_h,
        chars_per_line=cpl,
        max_lines=ml,
        max_line_width=mw,
        line_count=al,
        status=status,
    )


def split_card_markdown(md: str) -> tuple[str | None, str]:
    lines = md.splitlines()
    first_non_empty = None
    for i, line in enumerate(lines):
        if line.strip():
            first_non_empty = i
            break
    if first_non_empty is None:
        return None, ""
    m = _CARD_TITLE_RE.match(lines[first_non_empty])
    if not m:
        return None, md
    title = strip_inline_md(m.group(1).strip())
    body = "\n".join(lines[first_non_empty + 1 :]).lstrip("\n")
    return title, body


def status_str(s: str, use_color: bool) -> str:
    if not use_color:
        return s
    if s == "OVERFLOW":
        return f"{RED_BOLD}{s}{RESET}"
    if s == "WARN":
        return f"{YELLOW}{s}{RESET}"
    return s


def slide_title(slide: dict[str, Any]) -> str:
    layout = str(slide.get("layout", ""))
    if layout == "cover":
        return str(slide.get("title", ""))
    header = slide.get("header", {})
    if isinstance(header, dict):
        return str(header.get("title", ""))
    return ""


def check_slides(
    slides: list[dict[str, Any]],
    design: dict[str, Any],
    em_ratio: float,
    line_spacing: float,
    warn_ratio: float,
) -> list[CellResult]:
    l = design["LAYOUT"]
    f = design["FONTS"]
    out: list[CellResult] = []

    for sidx, slide in enumerate(slides, start=1):
        layout = str(slide.get("layout", ""))

        if layout == "cover":
            out.append(make_result(sidx, layout, "cover-title", "-", 5.5, 1.35, f["coverTitle"]["size"], str(slide.get("title", "")), em_ratio, line_spacing, warn_ratio))
            out.append(make_result(sidx, layout, "cover-affiliation", "-", 5.5, 0.35, f["coverMeta"]["size"], str(slide.get("affiliation", "")), em_ratio, line_spacing, warn_ratio))
            out.append(make_result(sidx, layout, "cover-presenter", "-", 5.5, 0.35, f["coverMeta"]["size"], str(slide.get("presenter", "")), em_ratio, line_spacing, warn_ratio))
            out.append(make_result(sidx, layout, "cover-date", "-", 5.5, 0.35, f["coverMeta"]["size"], str(slide.get("date", "")), em_ratio, line_spacing, warn_ratio))
            continue

        if "header" in slide:
            header = slide.get("header", {})
            if isinstance(header, dict):
                out.append(make_result(sidx, layout, "header-title", "-", 9.5, 0.45, f["title"]["size"], str(header.get("title", "")), em_ratio, line_spacing, warn_ratio))
                out.append(make_result(sidx, layout, "header-message", "-", 9.5, 0.3, f["message"]["size"], str(header.get("message", "")), em_ratio, line_spacing, warn_ratio))

        card_i = 0
        plain_i = 0
        section_i = 0
        conclusion_i = 0
        step_i = 0
        table_i = 0
        for geom in compute_cells(slide, l):
            cell = geom.cell
            ctype = str(cell.get("type", ""))
            if ctype in {"arrow", "image"}:
                continue

            if ctype == "card":
                label = f"card[{card_i}]"
                card_i += 1
                md = str(cell.get("markdown", ""))
                title_text, body_md = split_card_markdown(md)
                body_w = geom.w - l["cardPadX"] * 2
                if title_text is not None:
                    out.append(make_result(sidx, layout, label, "title", body_w, l["cardDivY"] - l["cardPadY"], f["cardTitle"]["size"], title_text, em_ratio, line_spacing, warn_ratio))
                    out.append(make_result(sidx, layout, label, "body", body_w, geom.h - l["cardDivY"] - 0.08 - l["cardPadY"], f["cardBody"]["size"], body_md, em_ratio, line_spacing, warn_ratio))
                else:
                    out.append(make_result(sidx, layout, label, "body", body_w, geom.h - l["cardPadY"] * 2, f["cardBody"]["size"], md, em_ratio, line_spacing, warn_ratio))
                continue

            if ctype == "plain":
                label = f"plain[{plain_i}]"
                plain_i += 1
                out.append(make_result(sidx, layout, label, "-", geom.w - l["headerPadX"] * 2, geom.h - l["mainPadY"] * 2, f["bodyText"]["size"], str(cell.get("markdown", "")), em_ratio, line_spacing, warn_ratio))
                continue

            if ctype == "section":
                label = f"section[{section_i}]"
                section_i += 1
                out.append(make_result(sidx, layout, label, "-", geom.w - l["cardPadX"] * 2, geom.h - l["cardPadY"] * 2, f["bgBody"]["size"], str(cell.get("markdown", "")), em_ratio, line_spacing, warn_ratio))
                continue

            if ctype == "conclusion":
                label = f"conclusion[{conclusion_i}]"
                conclusion_i += 1
                out.append(make_result(sidx, layout, label, "-", geom.w - l["conclusionAccentW"] - l["cardPadX"] * 2, geom.h - l["cardPadY"] * 2, f["conclBody"]["size"], str(cell.get("markdown", "")), em_ratio, line_spacing, warn_ratio))
                continue

            if ctype == "step_head":
                label = f"step_head[{step_i}]"
                step_i += 1
                txt = str(cell.get("markdown", cell.get("label", "")))
                out.append(make_result(sidx, layout, label, "-", geom.w * 0.85 - 0.15, geom.h, f["stepLabel"]["size"], txt, em_ratio, line_spacing, warn_ratio))
                continue

            if ctype == "table":
                label = f"table[{table_i}]"
                table_i += 1
                head = cell.get("head") if isinstance(cell.get("head"), list) else []
                rows = cell.get("rows") if isinstance(cell.get("rows"), list) else []
                has_head = len(head) > 0
                ncols = max(len(head), max((len(r) for r in rows if isinstance(r, list)), default=0))
                nrows = len(rows) + (1 if has_head else 0)
                if ncols <= 0 or nrows <= 0:
                    continue
                cw = geom.w / ncols - (7.0 / 72.0) * 2
                ch = geom.h / nrows - (3.0 / 72.0) * 2
                if has_head:
                    for j in range(ncols):
                        txt = str(head[j]) if j < len(head) else ""
                        out.append(make_result(sidx, layout, f"{label}[0,{j}]", "head", cw, ch, f["tableHead"]["size"], txt, em_ratio, line_spacing, warn_ratio))
                row_offset = 1 if has_head else 0
                for i, row in enumerate(rows):
                    if not isinstance(row, list):
                        continue
                    for j in range(ncols):
                        txt = str(row[j]) if j < len(row) else ""
                        size = f["tableHead"]["size"] if j == 0 else f["tableBody"]["size"]
                        out.append(make_result(sidx, layout, f"{label}[{i + row_offset},{j}]", "body", cw, ch, size, txt, em_ratio, line_spacing, warn_ratio))
                continue

    return out


def print_results(slides: list[dict[str, Any]], results: list[CellResult], no_color: bool) -> None:
    use_color = (not no_color) and sys.stdout.isatty()
    sep = "━" * 69
    sub_sep = "─" * 69

    by_slide: dict[int, list[CellResult]] = {}
    for r in results:
        by_slide.setdefault(r.slide_idx, []).append(r)

    for idx in sorted(by_slide.keys()):
        slide = slides[idx - 1] if idx - 1 < len(slides) else {}
        layout = str(slide.get("layout", ""))
        title = slide_title(slide).replace("\n", " / ")
        print(sep)
        print(f'Slide {idx}  [{layout}]  "{title}"')
        print(sep)
        print("Cell            Zone    CW\"   CH\"  CPL  MaxW  MaxL  ActL  Status")
        print(sub_sep)
        for r in by_slide[idx]:
            st = status_str(r.status, use_color)
            print(
                f"{r.cell_label:<15} {r.zone:<6} {r.content_w:>5.2f} {r.content_h:>5.2f} "
                f"{r.chars_per_line:>4} {r.max_line_width:>5} {r.max_lines:>5} {r.line_count:>5} {st:>8}"
            )
        print()

    total = len(results)
    overflow = sum(1 for r in results if r.status == "OVERFLOW")
    warn = sum(1 for r in results if r.status == "WARN")
    print(f"Summary: {total} cells checked   {overflow} OVERFLOW   {warn} WARN")


def main() -> int:
    args = parse_args()
    deck_path = Path(args.deck_md).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else deck_path.parent.resolve()

    try:
        if not deck_path.exists():
            raise FileNotFoundError(f"deck not found: {deck_path}")
        templates = load_json(project_root / "templates.json")
        design = load_json(project_root / "design.json")
        if "LAYOUT" not in design or "FONTS" not in design:
            raise ValueError("design.json must contain LAYOUT and FONTS")
        try:
            slides = convert_with_import(deck_path, templates, project_root)
        except Exception:
            slides = convert_with_fallback(deck_path, project_root)
        results = check_slides(slides, design, args.em_ratio, args.line_spacing, args.warn_ratio)
        print_results(slides, results, args.no_color)
        overflow = any(r.status == "OVERFLOW" for r in results)
        return 1 if overflow else 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
