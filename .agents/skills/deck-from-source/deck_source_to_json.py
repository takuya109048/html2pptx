"""Convert stable deck_source.json into slide JSON and optionally PPTX."""

from __future__ import annotations

import argparse
import copy
import json
import re
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

DENSITY_LIMITS: dict[str, tuple[list[str], int]] = {
    "plain_1col": (["card-a"], 140),
    "list_3card": (["card-a", "card-b", "card-c"], 100),
    "diffuse_3card": (["card-a", "card-b", "card-c"], 58),
    "bg_3card": (["card-a", "card-b", "card-c"], 58),
    "flow_3step": (["step-a", "step-b", "step-c"], 58),
    "converge_3card": (["card-a", "card-b", "card-c"], 58),
    "flow_4step": (["step-a", "step-b", "step-c", "step-d"], 40),
    "plain_2col": (["card-a", "card-b"], 115),
}

WEAK_EMPHASIS_TERMS = {
    "重要",
    "ポイント",
    "背景",
    "結論",
    "概要",
    "要点",
    "課題",
    "方針",
    "対応",
    "対策",
    "確認",
    "整理",
    "説明",
    "目的",
    "価値",
    "効果",
    "改善",
    "運用",
    "設計",
    "実行",
    "注意",
}


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
    parser.add_argument(
        "--strict-density",
        action="store_true",
        help="Reject thin visible text in card, step, and plain column blocks.",
    )
    parser.add_argument(
        "--strict-agenda-grouping",
        action="store_true",
        help="Reject agenda structures where every section contains only one slide.",
    )
    parser.add_argument(
        "--strict-markup",
        action="store_true",
        help="Reject prose-only card, step, and plain column blocks.",
    )
    parser.add_argument(
        "--strict-emphasis",
        action="store_true",
        help="Reject weak or missing skim-line emphasis in visible text blocks.",
    )
    parser.add_argument(
        "--strict-compact-blocks",
        action="store_true",
        help="Reject headings in compact section and conclusion blocks.",
    )
    parser.add_argument(
        "--strict-text-integrity",
        action="store_true",
        help="Reject replacement characters and suspicious runs of question marks.",
    )
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
            with candidate.open("r", encoding="utf-8-sig") as f:
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


def visible_density_text(markdown: str) -> str:
    body_lines: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        stripped = re.sub(r"^[-*+]\s+", "", stripped)
        stripped = re.sub(r"^\d+[.)]\s+", "", stripped)
        body_lines.append(stripped)
    text = "\n".join(body_lines)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("~~", "").replace("*", "").replace("_", "")
    text = re.sub(r"\s+", "", text)
    return text


def is_nanobanana_prompt_block(markdown: str) -> bool:
    head, body = split_heading(markdown)
    text = f"{head}\n{body}".lower()
    return "nanobanana" in text and ("prompt" in text or "プロンプト" in text)


def has_markdown_structure(markdown: str) -> bool:
    if re.search(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)", markdown):
        return True
    if re.search(r"`[^`]+`|~~[^~]+~~|\*\*[^*\n]+\*\*|__[^_\n]+__", markdown):
        return True
    if re.search(r"(?<!\*)\*[^*\n]+\*(?!\*)|(?<!_)_[^_\n]+_(?!_)", markdown):
        return True
    return False


def bold_segments(markdown: str) -> list[str]:
    segments: list[str] = []
    for match in re.finditer(r"\*\*([^*\n]+)\*\*|__([^_\n]+)__", markdown):
        segment = match.group(1) if match.group(1) is not None else match.group(2)
        segment = segment.strip()
        if segment:
            segments.append(segment)
    return segments


def normalized_emphasis(segment: str) -> str:
    compact = visible_density_text(segment)
    return re.sub(r"[、。，．・:：;；!！?？（）()「」『』［］\[\]【】]", "", compact)


def weak_emphasis_reason(segment: str) -> str | None:
    compact = normalized_emphasis(segment)
    if compact in WEAK_EMPHASIS_TERMS:
        return "generic label"
    if len(compact) <= 4 and any(
        term in compact for term in ("重要", "ポイント", "背景", "結論", "概要", "要点")
    ):
        return "too generic to explain the meaning by itself"
    return None


def display_emphasis_tags(layout: str, nanobanana2: bool) -> list[str]:
    rule = DENSITY_LIMITS.get(layout)
    if not rule:
        return []
    tags, _ = rule
    if nanobanana2 and layout == "plain_2col":
        return [tag for tag in tags if tag != "card-b"]
    return tags


def compact_emphasis_body(markdown: str) -> str:
    heading, body = split_heading(markdown)
    return body if heading else markdown


def bold_label_prefix_lines(markdown: str) -> list[str]:
    """Find bullet lines that use bold as a standalone label instead of inline emphasis."""
    lines: list[str] = []
    pattern = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\*\*([^*\n]+)\*\*|__([^_\n]+)__)(?P<tail>\s+\S|[：:])")
    particles = set("はがをにへとでのもやからよりまで、。")
    for line in markdown.splitlines():
        match = pattern.match(line)
        if not match:
            continue
        segment = (match.group(1) or match.group(2) or "").strip()
        compact = visible_density_text(segment)
        if not (2 <= len(compact) <= 12):
            continue
        tail = match.group("tail").strip()
        if segment.endswith((":", "：")) or not tail or tail[0] not in particles:
            lines.append(line.strip())
    return lines


def text_integrity_problem(text: str) -> str | None:
    if "\ufffd" in text:
        return "contains Unicode replacement characters"
    if re.search(r"\?{6,}", text):
        return "contains 6 or more consecutive question marks"
    visible = re.sub(r"\s+", "", text)
    if len(visible) >= 20:
        question_count = visible.count("?")
        if question_count >= 10 and question_count / len(visible) >= 0.35:
            return "has an unusually high question-mark ratio"
    return None


def iter_text_values(value: Any, path: str = "$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, child in value.items():
            yield from iter_text_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from iter_text_values(child, f"{path}[{index}]")


def validate_text_integrity(source: dict[str, Any]) -> int:
    errors = 0
    for path, text in iter_text_values(source):
        problem = text_integrity_problem(text)
        if problem:
            preview = text.replace("\n", " ")[:80]
            warn(f"Text integrity failed at {path}: {problem}. Preview: {preview!r}")
            errors += 1
    return errors


def note_with_icon(slide_def: dict[str, Any], nanobanana2: bool) -> str:
    note = as_text(slide_def.get("note")).strip()
    layout = str(slide_def.get("layout", "")).strip()
    icon_prompt = as_text(slide_def.get("icon_prompt")).strip()
    if nanobanana2 and layout in NANOBANANA_ICON_LAYOUTS:
        if icon_prompt and NANOBANANA_ICON_MARKER not in note:
            note = f"{note}\n\n---\n\n{NANOBANANA_ICON_MARKER}\n{icon_prompt}".strip()
    return note


def validate_density(
    index: int,
    title: str,
    layout: str,
    blocks: dict[str, Any],
    nanobanana2: bool,
) -> int:
    rule = DENSITY_LIMITS.get(layout)
    if not rule:
        return 0
    tags, minimum = rule
    errors = 0
    for tag in tags:
        markdown = as_text(blocks.get(tag)).strip()
        if nanobanana2 and layout == "plain_2col" and tag == "card-b":
            continue
        count = len(visible_density_text(markdown))
        if count < minimum:
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' is too thin "
                f"({count}/{minimum} chars in visible body text)."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
    return errors


def validate_markup(
    index: int,
    title: str,
    layout: str,
    blocks: dict[str, Any],
    nanobanana2: bool,
) -> int:
    rule = DENSITY_LIMITS.get(layout)
    if not rule:
        return 0
    tags, _ = rule
    errors = 0
    for tag in tags:
        markdown = as_text(blocks.get(tag)).strip()
        if nanobanana2 and layout == "plain_2col" and tag == "card-b":
            continue
        heading, body = split_heading(markdown)
        if not heading:
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' is missing a markdown heading."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
        if not has_markdown_structure(body):
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' is prose-only. "
                "Add bullets, numbering, bold, italic, code, or strikethrough markup."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
    return errors


def validate_emphasis(
    index: int,
    title: str,
    layout: str,
    blocks: dict[str, Any],
    nanobanana2: bool,
) -> int:
    tags = display_emphasis_tags(layout, nanobanana2)
    compact_tags = [tag for tag in ("section", "conclusion") if as_text(blocks.get(tag)).strip()]
    if not tags and not compact_tags:
        return 0
    errors = 0
    slide_segments: list[str] = []
    for tag in tags:
        markdown = as_text(blocks.get(tag)).strip()
        _, body = split_heading(markdown)
        raw_segments = [
            segment for segment in bold_segments(body)
            if 2 <= len(visible_density_text(segment)) <= 24
        ]
        weak_segments = [
            (segment, reason)
            for segment in raw_segments
            if (reason := weak_emphasis_reason(segment))
        ]
        segments = [segment for segment in raw_segments if not weak_emphasis_reason(segment)]
        if not raw_segments:
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' has no bold key phrase. "
                "Use **...** on one short decision point, condition, or action phrase."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
            continue
        if weak_segments:
            segment, reason = weak_segments[0]
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' uses weak bold phrase "
                f"{segment!r} ({reason}). Make the highlight explain a concrete decision, "
                "condition, action, or conclusion."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
        if not segments:
            continue
        slide_segments.extend(segments)
        label_lines = bold_label_prefix_lines(body)
        if label_lines:
            preview = label_lines[0].replace("\n", " ")[:80]
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' uses bold as a bullet label. "
                "Move emphasis into the sentence so highlighted phrases form a semantic skim path. "
                f"Example line: {preview!r}"
                + (f" Title: {title}" if title else "")
            )
            errors += 1
    for tag in compact_tags:
        markdown = compact_emphasis_body(as_text(blocks.get(tag)).strip())
        raw_segments = [
            segment for segment in bold_segments(markdown)
            if 2 <= len(visible_density_text(segment)) <= 24
        ]
        weak_segments = [
            (segment, reason)
            for segment in raw_segments
            if (reason := weak_emphasis_reason(segment))
        ]
        segments = [segment for segment in raw_segments if not weak_emphasis_reason(segment)]
        if not raw_segments:
            warn(
                f"Slide #{index} layout '{layout}' compact block '{tag}' has no skim-line bold phrase. "
                "Put one short inline emphasis in section/conclusion text."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
            continue
        if weak_segments:
            segment, reason = weak_segments[0]
            warn(
                f"Slide #{index} layout '{layout}' compact block '{tag}' uses weak bold phrase "
                f"{segment!r} ({reason})."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
        slide_segments.extend(segments)
    target_count = len(tags) + len(compact_tags)
    if nanobanana2 and layout == "plain_2col":
        minimum_segments = 2
    elif target_count >= 3:
        minimum_segments = 3
    elif target_count >= 2:
        minimum_segments = 2
    else:
        minimum_segments = 1
    if len(slide_segments) < minimum_segments:
        warn(
            f"Slide #{index} layout '{layout}' has only {len(slide_segments)} semantic bold phrase(s). "
            f"Use at least {minimum_segments} so the bold text forms a skim-line summary."
            + (f" Title: {title}" if title else "")
        )
        errors += 1
    normalized = [normalized_emphasis(segment) for segment in slide_segments]
    duplicates = sorted({item for item in normalized if item and normalized.count(item) > 1})
    if duplicates:
        warn(
            f"Slide #{index} repeats bold skim-line phrase(s): {', '.join(duplicates[:3])}. "
            "Use different highlights for role, condition, action, and conclusion."
            + (f" Title: {title}" if title else "")
        )
        errors += 1
    skim_length = len(visible_density_text("".join(slide_segments)))
    if minimum_segments >= 3 and skim_length < 12:
        warn(
            f"Slide #{index} bold skim-line is too thin ({skim_length} chars). "
            "Highlights should read like a short summary, not isolated labels."
            + (f" Title: {title}" if title else "")
        )
        errors += 1
    return errors


def validate_compact_blocks(
    index: int,
    title: str,
    layout: str,
    blocks: dict[str, Any],
) -> int:
    errors = 0
    for tag in ("section", "conclusion"):
        if tag not in blocks:
            continue
        markdown = as_text(blocks.get(tag)).strip()
        heading, _ = split_heading(markdown)
        if heading:
            warn(
                f"Slide #{index} layout '{layout}' block '{tag}' must not use markdown headings. "
                "Use a compact sentence with inline emphasis instead."
                + (f" Title: {title}" if title else "")
            )
            errors += 1
    return errors


def section_groups(body_slides: list[Any]) -> list[tuple[str, int]]:
    groups: list[tuple[str, int]] = []
    for slide in body_slides:
        if not isinstance(slide, dict):
            continue
        section = str(slide.get("section", "本編")).strip() or "本編"
        if not groups or groups[-1][0] != section:
            groups.append((section, 1))
        else:
            groups[-1] = (section, groups[-1][1] + 1)
    return groups


def validate_agenda_grouping(body_slides: list[Any]) -> int:
    groups = section_groups(body_slides)
    slide_count = sum(count for _, count in groups)
    if slide_count < 4 or len(groups) <= 1:
        return 0
    singleton_count = sum(1 for _, count in groups if count == 1)
    if singleton_count == len(groups):
        warn(
            "Agenda grouping is too fragmented: every section has only one slide. "
            "Reuse broader section names so each agenda heading contains multiple titles."
        )
        return 1
    if len(groups) > max(3, (slide_count + 1) // 2):
        warn(
            f"Agenda grouping has too many sections ({len(groups)} for {slide_count} slides). "
            "Merge adjacent sections into broader agenda headings."
        )
        return 1
    return 0


def validate_source(
    source: dict[str, Any],
    nanobanana2: bool,
    strict_blocks: bool,
    strict_density: bool,
    strict_agenda_grouping: bool,
    strict_markup: bool,
    strict_emphasis: bool,
    strict_compact_blocks: bool,
    strict_text_integrity: bool,
) -> int:
    errors = 0
    if strict_text_integrity:
        errors += validate_text_integrity(source)
    body_slides = source.get("slides", [])
    if not isinstance(body_slides, list) or not body_slides:
        warn("deck_source.json must contain a non-empty slides array.")
        return 1
    if strict_agenda_grouping:
        errors += validate_agenda_grouping(body_slides)
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
        if strict_density:
            errors += validate_density(index, title, layout, blocks, nanobanana2)
        if strict_markup:
            errors += validate_markup(index, title, layout, blocks, nanobanana2)
        if strict_emphasis:
            errors += validate_emphasis(index, title, layout, blocks, nanobanana2)
        if strict_compact_blocks:
            errors += validate_compact_blocks(index, title, layout, blocks)
        if nanobanana2:
            if index >= 3 and layout == "plain_1col":
                warn(f"Slide #{index} uses plain_1col while nanobanana2 is enabled." + (f" Title: {title}" if title else ""))
                errors += 1
            if layout == "plain_2col" and not is_nanobanana_prompt_block(as_text(blocks.get("card-b"))):
                warn(f"Slide #{index} layout 'plain_2col' card-b must contain a nanobanana prompt." + (f" Title: {title}" if title else ""))
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
    errors = validate_source(
        source,
        args.nanobanana2,
        args.strict_blocks,
        args.strict_density,
        args.strict_agenda_grouping,
        args.strict_markup,
        args.strict_emphasis,
        args.strict_compact_blocks,
        args.strict_text_integrity,
    )
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
