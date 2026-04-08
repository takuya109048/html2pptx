"""Tests for check_overflow.py"""
import sys
import math
import subprocess
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from check_overflow import (
    char_width,
    visual_width,
    strip_inline_md,
    parse_md_lines,
    measure_text,
    calc_status,
    chars_per_line,
    max_lines,
    split_card_markdown,
    compute_cells,
    CellGeom,
)


# ── char_width ──────────────────────────────────────────────────────────────

class TestCharWidth:
    def test_ascii_letter_is_1(self):
        assert char_width("A") == 1

    def test_ascii_digit_is_1(self):
        assert char_width("5") == 1

    def test_space_is_1(self):
        assert char_width(" ") == 1

    def test_japanese_hiragana_is_2(self):
        assert char_width("あ") == 2

    def test_japanese_katakana_is_2(self):
        assert char_width("ア") == 2

    def test_japanese_kanji_is_2(self):
        assert char_width("漢") == 2

    def test_fullwidth_latin_is_2(self):
        assert char_width("Ａ") == 2  # U+FF21 FULLWIDTH LATIN CAPITAL LETTER A


# ── visual_width ────────────────────────────────────────────────────────────

class TestVisualWidth:
    def test_empty_string(self):
        assert visual_width("") == 0

    def test_ascii_only(self):
        assert visual_width("abc") == 3

    def test_japanese_only(self):
        assert visual_width("あいう") == 6

    def test_mixed_ascii_and_japanese(self):
        # 'a' (1) + ' ' (1) + 'あ' (2) = 4
        assert visual_width("a あ") == 4

    def test_bold_markers_counted_literally(self):
        # strip_inline_md is NOT called here — raw string
        assert visual_width("**X**") == 5


# ── strip_inline_md ─────────────────────────────────────────────────────────

class TestStripInlineMd:
    def test_bold(self):
        assert strip_inline_md("**太字**") == "太字"

    def test_italic(self):
        assert strip_inline_md("*斜体*") == "斜体"

    def test_strikethrough(self):
        assert strip_inline_md("~~取り消し~~") == "取り消し"

    def test_code(self):
        assert strip_inline_md("`コード`") == "コード"

    def test_mixed(self):
        result = strip_inline_md("**bold** and *italic*")
        assert result == "bold and italic"

    def test_no_markdown_unchanged(self):
        assert strip_inline_md("plain text") == "plain text"

    def test_nested_bold_italic_not_supported(self):
        # bold takes priority; inner content preserved
        result = strip_inline_md("**bold**")
        assert "**" not in result


# ── parse_md_lines ──────────────────────────────────────────────────────────

class TestParseMdLines:
    def test_h2_heading(self):
        lines = parse_md_lines("## 見出し")
        assert len(lines) == 1
        assert lines[0][0] == "heading"
        assert "見出し" in lines[0][1]

    def test_h3_heading(self):
        lines = parse_md_lines("### 小見出し")
        assert lines[0][0] == "heading"

    def test_bullet_dash(self):
        lines = parse_md_lines("- 項目")
        assert lines[0][0] == "bullet"
        assert "項目" in lines[0][1]

    def test_bullet_asterisk(self):
        lines = parse_md_lines("* 項目")
        assert lines[0][0] == "bullet"

    def test_ordered_list(self):
        lines = parse_md_lines("1. 番号付き")
        assert lines[0][0] == "ordered"
        assert "番号付き" in lines[0][1]

    def test_blockquote(self):
        lines = parse_md_lines("> 引用テキスト")
        assert lines[0][0] == "blockquote"
        assert "引用テキスト" in lines[0][1]

    def test_para(self):
        lines = parse_md_lines("通常テキスト")
        assert lines[0][0] == "para"
        assert "通常テキスト" in lines[0][1]

    def test_blank_lines_skipped(self):
        lines = parse_md_lines("\n\n項目\n\n")
        assert len(lines) == 1

    def test_inline_md_stripped_in_output(self):
        lines = parse_md_lines("**太字**テキスト")
        assert "**" not in lines[0][1]

    def test_multiple_lines(self):
        md = "## 見出し\n- 項目1\n- 項目2"
        lines = parse_md_lines(md)
        assert len(lines) == 3


# ── measure_text ────────────────────────────────────────────────────────────

class TestMeasureText:
    def test_empty_lines(self):
        assert measure_text([], 20) == (0, 0)

    def test_single_short_line_no_wrap(self):
        lines = [("para", "abc")]  # visual_width=3, cpl=10 → 1 line
        max_w, total = measure_text(lines, 10)
        assert max_w == 3
        assert total == 1

    def test_single_line_wraps(self):
        # visual_width=20, cpl=10 → ceil(20/10)=2 lines
        lines = [("para", "a" * 20)]
        _, total = measure_text(lines, 10)
        assert total == 2

    def test_multiple_lines_max_width(self):
        lines = [("para", "abc"), ("para", "de")]
        max_w, total = measure_text(lines, 10)
        assert max_w == 3
        assert total == 2

    def test_japanese_wrapping(self):
        # 'あ'×5 → visual_width=10, cpl=6 → ceil(10/6)=2 lines
        lines = [("para", "あ" * 5)]
        _, total = measure_text(lines, 6)
        assert total == 2


# ── calc_status ─────────────────────────────────────────────────────────────

class TestCalcStatus:
    def test_ok_both_within_limit(self):
        assert calc_status(10, 20, 3, 5, 0.1) == "OK"

    def test_overflow_width_exceeds_limit(self):
        assert calc_status(25, 20, 3, 5, 0.1) == "OVERFLOW"

    def test_overflow_lines_exceeds_limit(self):
        assert calc_status(10, 20, 7, 5, 0.1) == "OVERFLOW"

    def test_warn_width_near_limit(self):
        # 19 > 20*(1-0.1)=18, and 19 <= 20 → WARN
        assert calc_status(19, 20, 3, 5, 0.1) == "WARN"

    def test_warn_lines_at_limit(self):
        # 5 > 5*(1-0.1)=4.5, and 5 <= 5 → WARN
        assert calc_status(10, 20, 5, 5, 0.1) == "WARN"

    def test_ok_exactly_at_limit(self):
        # width == cpl is not WARN (> check, not >=)
        assert calc_status(18, 20, 4, 5, 0.1) == "OK"


# ── chars_per_line / max_lines ───────────────────────────────────────────────

class TestDimCalc:
    def test_chars_per_line_formula(self):
        # actual: max(1, floor(content_w * 72 / (font_size * em_ratio)))
        expected = max(1, math.floor(9.5 * 72 / (24 * 1.8)))
        assert chars_per_line(9.5, 24, 1.8) == expected

    def test_chars_per_line_12pt(self):
        expected = max(1, math.floor(3.0 * 72 / (12 * 1.8)))
        assert chars_per_line(3.0, 12, 1.8) == expected

    def test_max_lines_formula(self):
        # max(1, ...) ensures result is never 0
        result = max_lines(0.45, 24, 1.35)
        assert result >= 1

    def test_max_lines_tall_box(self):
        expected = max(1, math.floor(4.0 * 72 / (12 * 1.35)))
        assert max_lines(4.0, 12, 1.35) == expected


# ── split_card_markdown ──────────────────────────────────────────────────────

class TestSplitCardMarkdown:
    def test_h2_heading_splits_correctly(self):
        md = "## タイトル\n- 項目1\n- 項目2"
        title, body = split_card_markdown(md)
        assert title is not None
        assert "タイトル" in title
        assert "項目1" in body

    def test_h3_heading_detected(self):
        md = "### 見出し3\n本文テキスト"
        title, body = split_card_markdown(md)
        assert title is not None

    def test_no_heading_returns_none_title(self):
        md = "- 項目1\n- 項目2"
        title, body = split_card_markdown(md)
        assert title is None
        assert "項目1" in body

    def test_heading_only_no_body(self):
        md = "## 見出しのみ"
        title, body = split_card_markdown(md)
        assert title is not None


# ── compute_cells ────────────────────────────────────────────────────────────

class TestComputeCells:
    @staticmethod
    def _layout():
        return {
            "mainPadX": 0.1,
            "mainPadY": 0.1,
            "headerH": 0.85,
            "footerY": 5.225,
            "gridGap": 0.08,
            "slideW": 10.0,
        }

    def test_list_3card_returns_3_cells(self):
        slide_data = {
            "layout": "list_3card",
            "rowHeightRatios": [1.0],
            "grid": [[
                {"type": "card", "markdown": "## A\n- a"},
                {"type": "card", "markdown": "## B\n- b"},
                {"type": "card", "markdown": "## C\n- c"},
            ]],
        }
        cells = compute_cells(slide_data, self._layout())
        assert len(cells) == 3

    def test_plain_1col_returns_1_cell(self):
        slide_data = {
            "layout": "plain_1col",
            "rowHeightRatios": [1.0],
            "grid": [[{"type": "plain", "markdown": "テスト"}]],
        }
        cells = compute_cells(slide_data, self._layout())
        assert len(cells) == 1

    def test_cell_dimensions_are_positive(self):
        slide_data = {
            "layout": "plain_1col",
            "rowHeightRatios": [1.0],
            "grid": [[{"type": "plain", "markdown": "テスト"}]],
        }
        cells = compute_cells(slide_data, self._layout())
        assert cells[0].w > 0
        assert cells[0].h > 0

    def test_2col_cells_have_equal_width(self):
        slide_data = {
            "layout": "plain_2col",
            "rowHeightRatios": [1.0],
            "grid": [[
                {"type": "plain", "markdown": "左"},
                {"type": "plain", "markdown": "右"},
            ]],
        }
        cells = compute_cells(slide_data, self._layout())
        assert len(cells) == 2
        assert abs(cells[0].w - cells[1].w) < 0.01

    def test_flow_3step_returns_6_cells(self):
        # 2 rows × 3 cols
        slide_data = {
            "layout": "flow_3step",
            "rowHeightRatios": [0.28, 0.72],
            "grid": [
                [
                    {"type": "step_head", "markdown": "A"},
                    {"type": "step_head", "markdown": "B"},
                    {"type": "step_head", "markdown": "C"},
                ],
                [
                    {"type": "card", "markdown": "- a"},
                    {"type": "card", "markdown": "- b"},
                    {"type": "card", "markdown": "- c"},
                ],
            ],
        }
        cells = compute_cells(slide_data, self._layout())
        assert len(cells) == 6

    def test_spanned_cell_has_wider_width(self):
        # section with span=3 should be wider than a normal 3-col cell
        slide_data = {
            "layout": "diffuse_3card",
            "rowHeightRatios": [0.25, 0.75],
            "grid": [
                [{"type": "section", "span": 3, "markdown": "共通方針"}],
                [
                    {"type": "card", "markdown": "- a"},
                    {"type": "card", "markdown": "- b"},
                    {"type": "card", "markdown": "- c"},
                ],
            ],
        }
        cells = compute_cells(slide_data, self._layout())
        section_cell = next(c for c in cells if c.cell["type"] == "section")
        card_cell = next(c for c in cells if c.cell["type"] == "card")
        assert section_cell.w > card_cell.w


# ── CLI integration ──────────────────────────────────────────────────────────

class TestCLI:
    def test_sample_deck_exits_0_or_1(self):
        root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", str(root / "check_overflow.py"),
             str(root / "sample_deck.md"), "--no-color"],
            capture_output=True,
            text=True,
        )
        assert result.returncode in (0, 1), (
            f"Unexpected exit code {result.returncode}\n"
            f"stderr: {result.stderr}"
        )

    def test_sample_deck_output_contains_summary(self):
        root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", str(root / "check_overflow.py"),
             str(root / "sample_deck.md"), "--no-color"],
            capture_output=True,
            text=True,
        )
        assert "Summary" in result.stdout

    def test_missing_file_exits_2(self):
        root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", str(root / "check_overflow.py"),
             "nonexistent_file.md", "--no-color"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2

    def test_custom_em_ratio_runs(self):
        root = Path(__file__).parent.parent
        result = subprocess.run(
            ["python", str(root / "check_overflow.py"),
             str(root / "sample_deck.md"), "--em-ratio", "2.0", "--no-color"],
            capture_output=True,
            text=True,
        )
        assert result.returncode in (0, 1)
