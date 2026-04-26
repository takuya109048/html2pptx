"""Overflow analysis for deck-from-source layouts.

Computes max visual lines and chars per visual line for each layout/cell type.

Scope: bullet-only content (single-level). heading / nested bullet /
ordered list / blockquote use different spacing and are NOT modeled here.
Output values are approximations based on geometry (no fonttools required).
"""

import csv
import json
import math
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "deck-from-source"
OUT_DIR = Path(__file__).resolve().parent

BULLET_INDENT_INCH = 228600 / 914400  # ≈ 0.25 inch (marL EMU → inches)

CELL_FONT = {
    # (font_size_pt, line_spacing_mult, space_after_pt)
    "card":       (11, 1.8, 4),
    "plain":      (12, 1.8, 4),
    "section":    (12, 1.8, 4),
    "conclusion": (12, 1.8, 4),
    # step_head: rendered by text(), no _set_line_spacing → PowerPoint default ≈ 1.2×
    "step_head":  (14, 1.2, 0),
}

TARGET_LAYOUTS = [
    "list_3card", "plain_1col", "plain_2col",
    "flow_3step", "flow_4step", "diffuse_3card",
]
TARGET_CELL_TYPES = {"card", "plain", "section", "conclusion", "step_head"}


def compute_cells(sd, L):
    mainX = L["mainPadX"]
    mainY = L["headerH"] + L["mainPadY"]
    mainW = L["slideW"] - L["mainPadX"] * 2
    mainH = L["footerY"] - mainY - L["mainPadY"]
    gap = L["gridGap"]
    grid = sd["grid"]
    numRows = len(grid)
    numCols = max(sum(c.get("span", 1) for c in row) for row in grid)
    ratios = sd.get("rowHeightRatios", [1.0 / numRows] * numRows)
    rowHeights = [mainH * r for r in ratios]

    def rowTop(r):
        return mainY + sum(rowHeights[:r])

    unitW = (mainW - gap * (numCols + 1)) / numCols
    cells = []
    for ri, row in enumerate(grid):
        col = 0
        for cell in row:
            span = cell.get("span", 1)
            cx = mainX + gap + col * (unitW + gap)
            cy = rowTop(ri) + (gap if ri == 0 else gap / 2)
            cw = unitW * span + gap * (span - 1)
            ch = (rowHeights[ri]
                  - (gap if ri == 0 else gap / 2)
                  - (gap if ri == numRows - 1 else gap / 2))
            cells.append({
                "type": cell.get("type", ""),
                "cx": cx, "cy": cy, "cw": cw, "ch": ch,
            })
            col += span
    return cells


def text_area(cell_type, cx, cy, cw, ch, L):
    """Return (text_w_in, text_h_in) for the writable text area of a cell."""
    padX = L["cardPadX"]
    padY = L["cardPadY"]
    hPadX = L["headerPadX"]
    hPadY = L["mainPadY"]

    if cell_type == "card":
        # With title: body starts below divider line
        divY_abs = cy + L["cardDivY"]
        body_w = cw - padX * 2
        body_h = (cy + ch) - divY_abs - 0.08 - padY
        return body_w, body_h

    elif cell_type == "plain":
        return cw - hPadX * 2, ch - hPadY * 2

    elif cell_type == "section":
        return cw - padX * 2, ch - padY * 2

    elif cell_type == "conclusion":
        accentW = L.get("conclusionAccentW", 0.07)
        return cw - accentW - padX * 2, ch - padY * 2

    elif cell_type == "step_head":
        # text(label, cx+0.15, cy, cw*0.85, ch, ...) in to_pptx.py
        return cw * 0.85, ch

    return cw, ch


def analyze_cell(layout_name, cell_type, text_w_in, text_h_in):
    font_size, spacing, space_after = CELL_FONT[cell_type]
    line_height_pt = font_size * spacing + space_after
    text_h_pt = text_h_in * 72
    text_w_pt = text_w_in * 72
    max_visual_lines = math.floor(text_h_pt / line_height_pt)

    if cell_type == "step_head":
        bullet_w_pt = text_w_pt
    else:
        bullet_w_pt = text_w_pt - BULLET_INDENT_INCH * 72

    chars_cjk = math.floor(bullet_w_pt / font_size)
    chars_ascii = math.floor(bullet_w_pt / (font_size * 0.55))
    chars_mixed = math.floor(bullet_w_pt / (font_size * 0.775))

    def max_items(n_chars, chars_per_line):
        if chars_per_line <= 0:
            return 0
        vlines_per_item = math.ceil(n_chars / chars_per_line)
        return max_visual_lines // max(1, vlines_per_item)

    return {
        "layout": layout_name,
        "cell_type": cell_type,
        "text_w_in": round(text_w_in, 3),
        "text_h_in": round(text_h_in, 3),
        "font_size": font_size,
        "max_visual_lines": max_visual_lines,
        "CJK_per_vline": chars_cjk,
        "ASCII_per_vline": chars_ascii,
        "Mixed_per_vline": chars_mixed,
        "max_items_15CJK": max_items(15, chars_cjk),
        "max_items_40CJK": max_items(40, chars_cjk),
        "max_items_25ASCII": max_items(25, chars_ascii),
        "max_items_35ASCII": max_items(35, chars_ascii),
    }


def run():
    with open(SKILL_DIR / "design.json", encoding="utf-8") as f:
        design = json.load(f)
    with open(SKILL_DIR / "templates.json", encoding="utf-8") as f:
        templates = json.load(f)

    L = design["LAYOUT"]
    rows = []
    seen = set()

    for layout_name in TARGET_LAYOUTS:
        if layout_name not in templates:
            print(f"[skip] {layout_name} not found in templates.json")
            continue
        tpl = templates[layout_name]
        slide = tpl["SLIDES"][0]
        cells = compute_cells(slide, L)

        for c in cells:
            ctype = c["type"]
            if ctype not in TARGET_CELL_TYPES:
                continue
            key = (layout_name, ctype, round(c["cw"], 3), round(c["ch"], 3))
            if key in seen:
                continue
            seen.add(key)
            tw, th = text_area(ctype, c["cx"], c["cy"], c["cw"], c["ch"], L)
            rows.append(analyze_cell(layout_name, ctype, tw, th))

    return rows


def print_table(rows):
    headers = [
        "layout", "cell_type", "w(in)", "h(in)", "font",
        "max_vis", "CJK/vln", "ASCII/vln", "Mix/vln",
        "@15CJK", "@40CJK", "@25ASCII", "@35ASCII",
    ]
    keys = [
        "layout", "cell_type", "text_w_in", "text_h_in", "font_size",
        "max_visual_lines", "CJK_per_vline", "ASCII_per_vline", "Mixed_per_vline",
        "max_items_15CJK", "max_items_40CJK", "max_items_25ASCII", "max_items_35ASCII",
    ]
    fmt_rows = [[str(r[k]) for k in keys] for r in rows]
    widths = [max(len(h), max(len(v) for v in col))
              for h, col in zip(headers, zip(*fmt_rows))]

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    line = lambda vals: "| " + " | ".join(v.ljust(w) for v, w in zip(vals, widths)) + " |"

    print("\n※ bullet-only スコープ（heading/nested/ordered/blockquote 非対応）\n")
    print(line(headers))
    print(sep)
    for r in fmt_rows:
        print(line(r))
    print()


def save_csv(rows):
    path = OUT_DIR / "overflow_analysis.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"→ {path}")


def save_md(rows):
    path = OUT_DIR / "overflow_analysis.md"
    headers = [
        "layout", "cell_type", "w(in)", "h(in)", "font",
        "max_vis", "CJK/vln", "ASCII/vln", "Mix/vln",
        "@15CJK", "@40CJK", "@25ASCII", "@35ASCII",
    ]
    keys = [
        "layout", "cell_type", "text_w_in", "text_h_in", "font_size",
        "max_visual_lines", "CJK_per_vline", "ASCII_per_vline", "Mixed_per_vline",
        "max_items_15CJK", "max_items_40CJK", "max_items_25ASCII", "max_items_35ASCII",
    ]
    lines = [
        "# Overflow Analysis — deck-from-source",
        "",
        "> **スコープ**: 単一レベル箇条書き（bullet）のみ。",
        "> heading / nested bullet / ordered / blockquote を含む場合は適用外。",
        "> geometry ベースの近似値（fonttools なし）。",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(":---" for _ in headers) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(r[k]) for k in keys) + " |")
    lines += [
        "",
        "## 凡例",
        "- `@15CJK`: 15字全角項目を何個収容できるか（= max_vis ÷ ceil(15/CJK_per_vline)）",
        "- `@40CJK`: 40字全角項目（折り返し発生）を何個収容できるか",
        "- `@25ASCII`: 25字半角項目を何個収容できるか",
        "- `@35ASCII`: 35字半角項目（折り返し発生想定）を何個収容できるか",
        "- `CJK/vln`: 1視覚行の全角文字数（文字単位折り返し）",
        "- `ASCII/vln`: 1視覚行の半角文字数（単語境界折り返し: 近似値）",
        "- `Mix/vln`: 1視覚行の混在文字数（全角50%/半角50% 近似）",
        "",
        "## 注記",
        "- `step_head` は `text()` 関数で描画、行間 ≈ 1.2×（PowerPoint デフォルト）",
        "- `step_head` の @items 列はラベル折り返し視覚行数の参考値",
        "- `plain_2col` は `engine: area` + `compute_cells()` 由来（`render_plain2col()` 参照なし）",
        "- card セルはタイトルあり前提（タイトルなしは本文高さが増える）",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"→ {path}")


if __name__ == "__main__":
    rows = run()
    print_table(rows)
    save_csv(rows)
    save_md(rows)
    print("Done.")
