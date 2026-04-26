"""Generate overflow test PPTX for deck-from-source layouts.

Creates slides for each layout × item count × character type combination,
plus dedicated step_head label overflow tests for flow layouts.
Output: overflow_test.pptx in the same directory as this script.

Run from project root or any directory:
  python .claude/tests/deck-from-source/generate_test_slides.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "deck-from-source"
OUT_DIR = Path(__file__).resolve().parent

SAMPLES = {
    "cjk_short":   "あいうえおかきくけこさしすせそ",
    "cjk_long":    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめも",
    "ascii_short": "the quick brown fox jumps",
    "ascii_long":  "the quick brown fox jumps over the lazy",
    "symbol_zen":  "！？＠＃あいうえお！？＠＃あいうえお",
    "symbol_han":  "text!? code@#$% number:123 key=val",
    "mixed":       "テキスト text 記号!? 数字123 あいう",
}

STEP_LABEL_SAMPLES = {
    "cjk_short":   "ステップA",
    "cjk_medium":  "ステップ実行フェーズA",
    "cjk_long":    "あいうえおかきくけこさしすせそ",
    "ascii_short": "Step A",
    "ascii_medium": "Execute Phase A",
    "ascii_long":  "the quick brown fox step",
}

N_ITEMS = [3, 5, 7, 10]


def _bullets(n, text):
    return "\n".join(f"- {text}" for _ in range(n))


def _slide(title, layout, body_blocks):
    meta = f"# {title}\n\n| key | value |\n|-----|-------|\n| layout | {layout} |\n| note | overflow test |"
    return meta + "\n\n" + "\n".join(body_blocks) + "\n\n---\n"


def _fenced(tag, content):
    return f"```{tag}\n{content}\n```"


def slide_list_3card(n, kind, sample):
    body = _bullets(n, sample)
    title = f"list_3card | N={n}行 | {kind}({len(sample)}字)"
    blocks = [
        _fenced("card-a", f"### カードA\n{body}"),
        _fenced("card-b", f"### カードB\n{body}"),
        _fenced("card-c", f"### カードC\n{body}"),
    ]
    return _slide(title, "list_3card", blocks)


def slide_plain_1col(n, kind, sample):
    body = _bullets(n, sample)
    title = f"plain_1col | N={n}行 | {kind}({len(sample)}字)"
    blocks = [_fenced("card-a", f"### 見出し\n{body}")]
    return _slide(title, "plain_1col", blocks)


def slide_plain_2col(n, kind, sample):
    body = _bullets(n, sample)
    title = f"plain_2col | N={n}行 | {kind}({len(sample)}字)"
    blocks = [
        _fenced("card-a", f"### 左カラム\n{body}"),
        _fenced("card-b", f"### 右カラム\n{body}"),
    ]
    return _slide(title, "plain_2col", blocks)


def slide_flow_3step(n, kind, sample, label="ステップ"):
    body = _bullets(n, sample)
    title = f"flow_3step | N={n}行 | {kind}({len(sample)}字)"
    blocks = [
        _fenced("step-a", f"### {label}A\n{body}"),
        _fenced("step-b", f"### {label}B\n{body}"),
        _fenced("step-c", f"### {label}C\n{body}"),
    ]
    return _slide(title, "flow_3step", blocks)


def slide_flow_4step(n, kind, sample, label="ステップ"):
    body = _bullets(n, sample)
    title = f"flow_4step | N={n}行 | {kind}({len(sample)}字)"
    blocks = [
        _fenced("step-a", f"### {label}A\n{body}"),
        _fenced("step-b", f"### {label}B\n{body}"),
        _fenced("step-c", f"### {label}C\n{body}"),
        _fenced("step-d", f"### {label}D\n{body}"),
    ]
    return _slide(title, "flow_4step", blocks)


def slide_diffuse_3card(n, kind, sample):
    body = _bullets(n, sample)
    title = f"diffuse_3card | N={n}行 | {kind}({len(sample)}字)"
    blocks = [
        _fenced("section", "共通方針テキスト"),
        _fenced("card-a", f"### カードA\n{body}"),
        _fenced("card-b", f"### カードB\n{body}"),
        _fenced("card-c", f"### カードC\n{body}"),
    ]
    return _slide(title, "diffuse_3card", blocks)


def slide_flow_3step_label(kind, label):
    title = f"flow_3step | step_head | {kind}"
    blocks = [
        _fenced("step-a", f"### {label}\n- テキスト"),
        _fenced("step-b", f"### {label}\n- テキスト"),
        _fenced("step-c", f"### {label}\n- テキスト"),
    ]
    return _slide(title, "flow_3step", blocks)


def slide_flow_4step_label(kind, label):
    title = f"flow_4step | step_head | {kind}"
    blocks = [
        _fenced("step-a", f"### {label}\n- テキスト"),
        _fenced("step-b", f"### {label}\n- テキスト"),
        _fenced("step-c", f"### {label}\n- テキスト"),
        _fenced("step-d", f"### {label}\n- テキスト"),
    ]
    return _slide(title, "flow_4step", blocks)


def main():
    generators = [
        ("list_3card",    slide_list_3card),
        ("plain_1col",    slide_plain_1col),
        ("plain_2col",    slide_plain_2col),
        ("flow_3step",    slide_flow_3step),
        ("flow_4step",    slide_flow_4step),
        ("diffuse_3card", slide_diffuse_3card),
    ]

    slides_md = []
    for _layout, gen in generators:
        for n in N_ITEMS:
            for kind, sample in SAMPLES.items():
                slides_md.append(gen(n, kind, sample))

    for kind, label in STEP_LABEL_SAMPLES.items():
        slides_md.append(slide_flow_3step_label(kind, label))
        slides_md.append(slide_flow_4step_label(kind, label))

    combined = "\n".join(slides_md)

    tmp_md = OUT_DIR / "_overflow_test_tmp.md"
    tmp_md.write_text(combined, encoding="utf-8")

    output_pptx = OUT_DIR / "overflow_test.pptx"
    md_to_json = SKILL_DIR / "md_to_json.py"

    n_slides = len(slides_md)
    print(f"Generating {output_pptx.name} from {n_slides} slides...")

    cmd = [sys.executable, str(md_to_json), str(tmp_md), str(output_pptx),
           "--assets-dir", str(SKILL_DIR)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except PermissionError:
        cmd[0] = "python"
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finally:
        tmp_md.unlink(missing_ok=True)

    if result.returncode != 0:
        print("Error:", result.stderr or result.stdout, file=sys.stderr)
        sys.exit(1)

    if result.stderr.strip():
        print(result.stderr.strip())

    print(f"→ {output_pptx}")
    print(f"  {n_slides} slides total")
    print("Done.")


if __name__ == "__main__":
    main()
