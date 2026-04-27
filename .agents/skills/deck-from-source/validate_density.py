"""validate_density.py
Expects globals: MD_CONTENT or DECK_MD (str), NANOBANANA (bool).
Checks card density, visual-line fit, tone, and speaker-note substance.
"""
import math
import re

TARGETS = {
    "list_3card":     {"normal": (3, 4), "nano": (3, 3)},
    "flow_3step":     {"normal": (2, 3), "nano": (2, 2)},
    "flow_4step":     {"normal": (2, 2), "nano": (1, 2)},
    "diffuse_3card":  {"normal": (2, 3), "nano": (2, 2)},
    "converge_3card": {"normal": (2, 2), "nano": (2, 2)},
    "bg_3card":       {"normal": (2, 3), "nano": (2, 2)},
    "plain_2col":     {"normal": (3, 4), "nano": (3, 3)},
}

LINE_BUDGETS = {
    "list_3card":     {"chars": 17, "min": 6, "max": 8},
    "flow_3step":     {"chars": 17, "min": 4, "max": 5},
    "flow_4step":     {"chars": 11, "min": 3, "max": 4},
    "diffuse_3card":  {"chars": 17, "min": 4, "max": 5},
    "converge_3card": {"chars": 17, "min": 4, "max": 5},
    "bg_3card":       {"chars": 17, "min": 4, "max": 5},
    "plain_2col":     {"chars": 24, "min": 6, "max": 9},
}

CHAR_BUDGETS = {
    "list_3card": 100,
    "flow_3step": 58,
    "flow_4step": 40,
    "diffuse_3card": 58,
    "converge_3card": 58,
    "bg_3card": 58,
    "plain_2col": 115,
}

COMPACT_LAYOUTS = {
    "flow_3step",
    "flow_4step",
    "diffuse_3card",
    "converge_3card",
    "bg_3card",
}

MIN_BULLET_LEN = {
    "flow_4step": 14,
    "flow_3step": 16,
    "diffuse_3card": 16,
    "converge_3card": 16,
    "bg_3card": 16,
    "list_3card": 18,
    "plain_2col": 18,
}

STYLE_FORBIDDEN = re.compile(r"(です|ます|ください|しましょう|ましょう|しました|できます|ありません)")

mode = "nano" if bool(globals().get("NANOBANANA", False)) else "normal"
source = globals().get("MD_CONTENT") or globals().get("DECK_MD") or ""
slides = re.split(r"\n---\n", source.strip())
issues, ok = [], 0


def clean_text(text):
    text = re.sub(r"\[(.*?)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_~#>|-]", "", text)
    return text.strip()


def visible_len(text):
    return len(clean_text(text))


def visual_lines_for(text, chars_per_line):
    length = visible_len(text)
    if length == 0:
        return 0
    return max(1, math.ceil(length / chars_per_line))


def note_text(slide):
    match = re.search(r"^\|\s*note\s*\|\s*(.*?)\s*\|\s*$", slide, re.M)
    if not match:
        return ""
    note = match.group(1).strip()
    return note.split(" --- [nanobanana2", 1)[0].strip()


def visible_slide_text(slide):
    return re.sub(r"^\|\s*note\s*\|.*?\|\s*$", "", slide, flags=re.M)


def block_lines(block):
    return [line.strip() for line in block.splitlines() if line.strip()]


def body_lines(lines):
    return [line for line in lines if not line.startswith("###")]


def has_prose_lead(lines):
    body = body_lines(lines)
    if not body:
        return False
    return not body[0].startswith(("- ", "1.", "2.", "3.", "####"))


def is_label_colon_bullet(bullet):
    return bool(
        re.match(r"\*\*[^*]{1,20}[:：・]\*\*", bullet)
        or re.match(r"\*\*[^*]{1,20}\*\*\s*[:：・]", bullet)
    )


def bullet_form(bullet):
    text = clean_text(bullet)
    if "→" in bullet or "⇒" in bullet:
        return "arrow"
    if re.search(r"(従来|今後|Before|After|一方|対して|対比)", text, re.I):
        return "contrast"
    if re.search(r"(なぜ|何を|どこで|誰が|どう|どの|か$)", text):
        return "question"
    if is_label_colon_bullet(bullet):
        return "label"
    return "prose"


def has_bullet_variety(bullets):
    if not bullets:
        return False
    forms = {bullet_form(bullet) for bullet in bullets}
    return len(forms) >= 2 or forms != {"label"}


def has_structure_variety(lines, bullets):
    if not has_prose_lead(lines):
        return False
    if has_bullet_variety(bullets):
        return True
    if any(re.match(r"\d+\.\s+", line) for line in lines):
        return True
    return any(line.startswith("####") for line in lines)


def block_visual_lines(lines, chars_per_line):
    return sum(visual_lines_for(line, chars_per_line) for line in body_lines(lines))


for si, slide in enumerate(slides, 1):
    m = re.search(r"\|\s*layout\s*\|\s*(\S+)\s*\|", slide)
    if not m:
        continue

    layout = m.group(1)
    visible_text = visible_slide_text(slide)
    if STYLE_FORBIDDEN.search(visible_text):
        issues.append(f"S{si} style: use dearu tone in visible slide text")

    note = note_text(slide)
    min_note = 120 if layout == "cover" else 180
    if visible_len(note) < min_note:
        issues.append(f"S{si} note too short: {visible_len(note)}->{min_note}+")
    else:
        ok += 1

    if layout not in TARGETS:
        continue

    lo, hi = TARGETS[layout][mode]
    blocks = re.findall(r"```(?:card-[a-d]|step-[a-d])\n(.*?)```", slide, re.DOTALL)
    for bi, block in enumerate(blocks, 1):
        lines = block_lines(block)
        bullets = [line.strip()[2:].strip() for line in block.splitlines() if line.strip().startswith("- ")]
        n = len(bullets)

        if n < lo:
            issues.append(f"S{si} {layout[:8]} blk{bi} bullets: {n}->{lo}-{hi} (+{lo - n})")
        elif n > hi:
            issues.append(f"S{si} {layout[:8]} blk{bi} bullets: {n}->{lo}-{hi} (-{n - hi})")
        else:
            ok += 1

        budget = LINE_BUDGETS.get(layout)
        if budget:
            vlines = block_visual_lines(lines, budget["chars"])
            if vlines > budget["max"]:
                issues.append(f"S{si} overflow risk blk{bi}: {vlines}->{budget['min']}-{budget['max']} visual lines")
            elif vlines < budget["min"]:
                issues.append(f"S{si} whitespace risk blk{bi}: {vlines}->{budget['min']}-{budget['max']} visual lines")
            else:
                ok += 1

        min_chars = CHAR_BUDGETS.get(layout)
        if min_chars:
            chars = sum(visible_len(line) for line in body_lines(lines))
            if chars < min_chars:
                issues.append(f"S{si} low density blk{bi}: {chars}->{min_chars}+ chars")
            else:
                ok += 1

        min_bullet = MIN_BULLET_LEN.get(layout, 16)
        for bj, bullet in enumerate(bullets, 1):
            length = visible_len(bullet)
            if length < min_bullet:
                issues.append(f"S{si} short bullet blk{bi}.{bj}: {length}->{min_bullet}+")

        if not has_structure_variety(lines, bullets):
            issues.append(f"S{si} flat block blk{bi}: mix prose, arrow, contrast, or question forms")

        if len(bullets) >= 2 and all(is_label_colon_bullet(bullet) for bullet in bullets):
            issues.append(f"S{si} repetitive bullet form blk{bi}: avoid all label-colon bullets")

        if layout in COMPACT_LAYOUTS and any(line.startswith("####") for line in lines):
            issues.append(f"S{si} compact block blk{bi}: avoid subheadings in tight cards")

    if layout == "converge_3card":
        conclusions = re.findall(r"```conclusion\n(.*?)```", slide, re.DOTALL)
        for ci, conclusion in enumerate(conclusions, 1):
            lines = block_lines(conclusion)
            vlines = sum(visual_lines_for(line, 34) for line in lines)
            if vlines > 2:
                issues.append(f"S{si} conclusion overflow risk {ci}: {vlines}->2 visual lines")

for issue in issues:
    print(issue)
print(f"{'FAIL' if issues else 'PASS'}: {len(issues)} blocks need fix, {ok} OK")
