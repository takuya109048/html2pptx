"""slide.html → PPTX (python-pptx)

slide.html 内の const D = {...} をSingle source of truthとして読み込む。
Markdownフィールドをパースしてカードタイトル・コンテンツを抽出。
座標はインチ単位で、PPTX標準16:9 (10" x 5.625") に一致。
"""
import json
import os
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.oxml.ns import qn
from lxml import etree as _etree
_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
def _el(tag, attrib=None):
    return _etree.Element(f"{{{_NS}}}{tag}", attrib=attrib or {})

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "slide.html"), encoding="utf-8") as f:
    _html = f.read()

_m = re.search(r'const D = (\{[\s\S]+?\});\s*\n\n\(D =>', _html)
if not _m:
    raise ValueError("slide.html 内に const D = {...} が見つかりません")
D = json.loads(_m.group(1))

COLORS = D["COLORS"]
FONTS = D["FONTS"]


def rgb(hex6):
    return RGBColor.from_string(hex6)


def rect(slide, x, y, w, h, fill, line_color=None, line_w=None):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line_color:
        shape.line.color.rgb = rgb(line_color)
        shape.line.width = Pt(line_w or 0.5)
    else:
        shape.line.fill.background()
    return shape


def _is_cjk(ch):
    cp = ord(ch)
    return (
        0x3000 <= cp <= 0x9FFF or   # ひらがな・カタカナ・CJK統合漢字等
        0xF900 <= cp <= 0xFAFF or   # CJK互換漢字
        0xFF00 <= cp <= 0xFFEF or   # 全角・半角形
        0x20000 <= cp <= 0x2A6DF    # CJK拡張B
    )


def _split_script(txt):
    """テキストをCJK/Latin交互のセグメントに分割して返す"""
    if not txt:
        return []
    segs, cur_jp, cur = [], _is_cjk(txt[0]), txt[0]
    for ch in txt[1:]:
        jp = _is_cjk(ch)
        if jp == cur_jp:
            cur += ch
        else:
            segs.append((cur_jp, cur))
            cur_jp, cur = jp, ch
    segs.append((cur_jp, cur))
    return segs


def _add_runs(p, txt, size, bold, color_hex):
    """テキストをCJK/Latinに分割し、各セグメントを独立したrunとして追加。
    CJK → lang=ja-JP / ea=Meiryo
    Latin → lang=en-US / latin=Segoe UI
    """
    sz_val = str(int(size * 100))
    b_val = "1" if bold else "0"
    clr = color_hex.upper()

    for is_jp, seg in _split_script(txt):
        r    = _el("r")
        rPr  = _el("rPr", {"lang": "ja-JP" if is_jp else "en-US",
                            "sz": sz_val, "b": b_val, "dirty": "0"})
        fill = _el("solidFill")
        clr_el = _el("srgbClr", {"val": clr})
        fill.append(clr_el)
        rPr.append(fill)
        font = _el("ea" if is_jp else "latin",
                   {"typeface": "Meiryo" if is_jp else "Segoe UI"})
        rPr.append(font)
        t = _el("t")
        t.text = seg
        r.append(rPr)
        r.append(t)
        p._p.append(r)


def _fix_bodyPr(tf):
    """spAutoFit → noAutofit に置換し、指定高さを維持する"""
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for old in bodyPr.findall(qn("a:spAutoFit")):
        bodyPr.remove(old)
    if not bodyPr.findall(qn("a:noAutofit")):
        bodyPr.append(bodyPr.makeelement(qn("a:noAutofit"), {}))


def _set_line_spacing(p, size_pt, mult=1.0):
    """行間を size_pt * mult の固定ポイントに設定。"""
    pPr = p._p.get_or_add_pPr()
    for old in pPr.findall(qn("a:lnSpc")):
        pPr.remove(old)
    lnSpc = _el("lnSpc")
    spcPts = _el("spcPts", {"val": str(int(size_pt * mult * 100))})
    lnSpc.append(spcPts)
    pPr.append(lnSpc)


def text(slide, txt, x, y, w, h, size, bold=False, color="333333",
         anchor=MSO_ANCHOR.MIDDLE):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    _fix_bodyPr(tf)
    p = tf.paragraphs[0]
    _add_runs(p, txt, size, bold, color)
    return box


def md_content(slide, items, x, y, w, h, size, color="333333"):
    """(type, text) のリストをテキストボックスに描画。
    type='bullet' → 箇条書き、type='para' → 通常段落
    """
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    bodyPr = tf._txBody.find(qn("a:bodyPr"))
    for old in bodyPr.findall(qn("a:spAutoFit")):
        bodyPr.remove(old)
    bodyPr.append(bodyPr.makeelement(qn("a:noAutofit"), {}))

    for idx, (item_type, item_text) in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.space_after = Pt(4)

        pPr = p._p.get_or_add_pPr()
        for tag in (qn("a:buChar"), qn("a:buNone")):
            for old in pPr.findall(tag):
                pPr.remove(old)
        if item_type == "bullet":
            # HTML の padding-left: 1.4em ≈ 0.25inch に合わせたハンギングインデント
            pPr.set("marL", "228600")
            pPr.set("indent", "-228600")
            pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "\u2022"}))
        else:
            pPr.append(pPr.makeelement(qn("a:buNone"), {}))

        _add_runs(p, item_text, size, False, color)
        _set_line_spacing(p, size, mult=1.8)

    return box


def hline(slide, x, y, w, color, width_pt=1):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Pt(width_pt))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    shape.line.fill.background()
    return shape


def parse_md(md):
    """Markdownをパースして (title, items) を返す。
    items: list of ('bullet'|'para', text)
    **bold** / *italic* などのインラインマーカーは除去。
    """
    title = ""
    items = []
    for line in md.strip().split("\n"):
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^#{1,6}\s+(.*)", s)
        if m:
            title = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", m.group(1))
        elif re.match(r"^[-*+]\s+", s):
            content = re.sub(r"^[-*+]\s+", "", s)
            content = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", content)
            items.append(("bullet", content))
        else:
            content = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", s)
            items.append(("para", content))
    return title, items


def build(prs, sd):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    H = D["HEADER"]
    FT = D["FOOTER"]
    C = COLORS
    F = FONTS

    # ── ヘッダー帯 ──
    rect(slide, H["x"], H["y"], H["w"], H["h"], C["headerBg"])
    # MIDDLE アンカーの視覚的中心を HTML の flex center に合わせるため y を下方補正
    # title(24pt): 2.5px ずれ → +0.013in, message(12pt): 8px ずれ → +0.042in
    text(slide, sd["header"]["title"],
         H["padX"], H["padY"] + 0.013, H["w"] - H["padX"] * 2, 0.45,
         F["title"]["size"], F["title"]["bold"], C["headerText"])
    text(slide, sd["header"]["message"],
         H["padX"], H["padY"] + 0.45 + 0.042, H["w"] - H["padX"] * 2, 0.3,
         F["message"]["size"], F["message"]["bold"], C["headerText"])

    # ── カード ──
    for i, cd in enumerate(sd["cards"]):
        c = D["CARDS"][i]
        cp = D["CARD_PAD"]
        doy = D["CARD_DIVIDER_OFFSET_Y"]

        card_title, items = parse_md(cd["markdown"])

        rect(slide, c["x"], c["y"], c["w"], c["h"], C["surface"], C["border"], 0.5)

        # HTML はブロックフロー（上揃え）なので TOP アンカーを使用
        text(slide, card_title,
             c["x"] + cp["x"], c["y"] + cp["y"], c["w"] - cp["x"] * 2, 0.35,
             F["cardTitle"]["size"], F["cardTitle"]["bold"], C["text"],
             anchor=MSO_ANCHOR.TOP)

        hline(slide, c["x"] + cp["x"], c["y"] + doy, c["w"] - cp["x"] * 2, C["border"], 1.5)

        if items:
            bx = c["x"] + cp["x"]
            by = c["y"] + doy + 0.12
            bw = c["w"] - cp["x"] * 2
            bh = c["h"] - doy - cp["y"] - 0.12
            md_content(slide, items, bx, by, bw, bh, F["cardBody"]["size"], C["text"])

    # ── フッター ──
    hline(slide, 0, FT["y"], FT["w"], C["border"], 0.5)

    footer_center_y = FT["y"] + FT["h"] / 2
    page_h = 0.3
    logo_h = D["LOGO_H"]

    # ページ番号：フッター帯の縦方向中心
    box = text(slide, sd["page"],
               FT["padX"], footer_center_y - page_h / 2, 2, page_h,
               F["footer"]["size"], False, C["textMuted"])
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    # ロゴ：フッター帯の縦方向中心
    logo_path = os.path.join(HERE, sd["logo"])
    if os.path.exists(logo_path):
        slide.shapes.add_picture(
            logo_path,
            Inches(D["SLIDE_W"] - FT["padX"] - 1.0),
            Inches(footer_center_y - logo_h / 2),
            height=Inches(logo_h),
        )


def main():
    prs = Presentation()
    prs.slide_width = Inches(D["SLIDE_W"])
    prs.slide_height = Inches(D["SLIDE_H"])
    for sd in D["SLIDES"]:
        build(prs, sd)
    out = os.path.join(HERE, "output.pptx")
    prs.save(out)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
