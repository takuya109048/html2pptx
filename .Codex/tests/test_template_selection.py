from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / ".agents" / "skills" / "deck-from-source"
sys.path.insert(0, str(SKILL_DIR))

import deck_source_to_json as deck  # noqa: E402


CATALOG = json.loads((SKILL_DIR / "template_catalog.json").read_text(encoding="utf-8"))


def md(label: str) -> str:
    return f"### {label}\n- **{label}の要点** を具体化する\n- 補足条件を短く示す"


def chosen(slide: dict, nanobanana2: bool = False) -> tuple[str, str]:
    expanded = deck.expand_slide_kind(slide, CATALOG, nanobanana2)
    return expanded.get("layout", ""), expanded.get("variant", "")


def main() -> int:
    cases = [
        (
            "generic_kind_can_escape_to_problem_solution",
            {
                "slide_kind": "narrative",
                "variant": "auto",
                "slots": {
                    "lead": "課題の背景と影響をまとめる",
                    "problem": md("課題"),
                    "cause": md("原因"),
                    "solution": md("対応"),
                },
            },
            "bg_3card",
        ),
        (
            "generic_kind_can_escape_to_kpi",
            {
                "slide_kind": "narrative",
                "variant": "auto",
                "slots": {
                    "kpi": {
                        "items": [
                            {"label": "売上", "value": "120", "caption": "+10%"},
                            {"label": "継続率", "value": "95%", "caption": "+3pt"},
                            {"label": "費用", "value": "80", "caption": "-5%"},
                        ]
                    },
                    "conclusion": "主要指標は改善傾向で、次は継続率を重点管理する。",
                },
            },
            "kpi_conclusion",
        ),
        (
            "table_slots_choose_table",
            {
                "slide_kind": "three_points",
                "variant": "auto",
                "slots": {
                    "table": {
                        "head": ["項目", "現状", "次の対応"],
                        "rows": [["運用", "属人化", "手順化"], ["品質", "ばらつき", "検証追加"]],
                    },
                    "conclusion": "表の差分から、まず運用手順と検証を固定する。",
                },
            },
            "table_conclusion",
        ),
        (
            "regular_three_points_stays_cards",
            {
                "slide_kind": "three_points",
                "variant": "auto",
                "slots": {"a": md("A"), "b": md("B"), "c": md("C")},
            },
            "list_3card",
        ),
        (
            "nanobanana_prefers_plain_2col",
            {
                "slide_kind": "narrative",
                "variant": "auto",
                "slots": {"a": md("要点A"), "b": md("要点B")},
            },
            "plain_2col",
        ),
    ]

    failures = []
    for name, slide, expected_layout in cases:
        layout, variant = chosen(slide, nanobanana2=name.startswith("nanobanana"))
        if layout != expected_layout:
            failures.append(f"{name}: expected {expected_layout}, got {layout}/{variant}")
        else:
            print(f"OK {name}: {layout}/{variant}")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
