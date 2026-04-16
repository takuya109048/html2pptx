from __future__ import annotations

import json
import sys
from pathlib import Path

from md_to_json import convert_markdown_to_slides


ROOT = Path(__file__).resolve().parent
TEMPLATE_HTML_PATH = ROOT / "template_engine_area.html"
TEMPLATES_JSON_PATH = ROOT / "templates.json"
DESIGN_JSON_PATH = ROOT / "design.json"
OUTPUT_DIR = ROOT / "templates"
SLIDES_PLACEHOLDER = "// __SLIDES__"
DESIGN_PLACEHOLDER = "// __DESIGN__"


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def ensure_mapping(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return value


def with_page_numbers(slides: object, *, template_key: str) -> list[dict[str, object]]:
    if not isinstance(slides, list):
        raise ValueError(f"Template '{template_key}' has invalid SLIDES; expected a list.")

    numbered_slides: list[dict[str, object]] = []
    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            raise ValueError(
                f"Template '{template_key}' has invalid slide at index {index - 1}; expected an object."
            )
        slide_with_page = dict(slide)
        slide_with_page["page"] = index
        numbered_slides.append(slide_with_page)
    return numbered_slides


def build_html(template_source: str, slides: list[dict[str, object]], design: dict[str, object]) -> str:
    if SLIDES_PLACEHOLDER not in template_source:
        raise ValueError(f"Missing placeholder: {SLIDES_PLACEHOLDER}")
    if DESIGN_PLACEHOLDER not in template_source:
        raise ValueError(f"Missing placeholder: {DESIGN_PLACEHOLDER}")

    slides_js = f"const SLIDES = {json.dumps(slides, ensure_ascii=False, indent=2)};"
    design_js = f"const DESIGN = {json.dumps(design, ensure_ascii=False, indent=2)};"

    html = template_source.replace(SLIDES_PLACEHOLDER, slides_js, 1)
    html = html.replace(DESIGN_PLACEHOLDER, design_js, 1)
    return html


def write_template(
    *,
    template_key: str,
    template_definition: dict[str, object],
    template_source: str,
    design: dict[str, object],
) -> Path:
    slides = with_page_numbers(template_definition.get("SLIDES"), template_key=template_key)
    output_html = build_html(template_source, slides, design)
    output_path = OUTPUT_DIR / f"template_{template_key}.html"
    output_path.write_text(output_html, encoding="utf-8")
    return output_path


def select_templates(
    templates: dict[str, object], selected_key: str | None
) -> dict[str, dict[str, object]]:
    if selected_key is None:
        selected = templates
    else:
        if selected_key not in templates:
            available = ", ".join(sorted(templates))
            raise ValueError(f"Unknown template '{selected_key}'. Available templates: {available}")
        selected = {selected_key: templates[selected_key]}

    normalized: dict[str, dict[str, object]] = {}
    for key, value in selected.items():
        normalized[key] = ensure_mapping(value, label=f"Template '{key}'")
    return normalized


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        print("Usage: python build_html.py [template_key|input.md]", file=sys.stderr)
        return 1

    input_arg = argv[1] if len(argv) == 2 else None

    template_source = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
    templates = ensure_mapping(load_json(TEMPLATES_JSON_PATH), label="templates.json")
    design = ensure_mapping(load_json(DESIGN_JSON_PATH), label="design.json")
    OUTPUT_DIR.mkdir(exist_ok=True)

    if input_arg is not None and Path(input_arg).suffix.lower() == ".md":
        markdown_path = Path(input_arg)
        if not markdown_path.exists():
            print(f"Error: Markdown file not found: {markdown_path}", file=sys.stderr)
            return 1

        markdown_text = markdown_path.read_text(encoding="utf-8")
        slides = convert_markdown_to_slides(markdown_text, templates)
        if not slides:
            print(f"Warning: No slides generated from {markdown_path.name}.")
            return 0

        numbered_slides = with_page_numbers(slides, template_key=markdown_path.stem)
        output_html = build_html(template_source, numbered_slides, design)
        output_path = OUTPUT_DIR / f"{markdown_path.stem}.html"
        output_path.write_text(output_html, encoding="utf-8")
        print(output_path.name)
        return 0

    template_key = input_arg
    selected_templates = select_templates(templates, template_key)

    generated_files: list[Path] = []
    for key, definition in selected_templates.items():
        generated_files.append(
            write_template(
                template_key=key,
                template_definition=definition,
                template_source=template_source,
                design=design,
            )
        )

    for path in generated_files:
        print(path.name)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
