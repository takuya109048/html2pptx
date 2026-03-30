"""すべての template_*.html → 一つのPPTX (python-pptx)

プロジェクト内のすべての template_*.html ファイルを一つの PPTX ファイルに統合。
各テンプレートの const D {...} から SLIDES データを読み込んで処理。

使い方:
  python to_pptx.py              # すべてのテンプレート → all_templates.pptx
  python to_pptx.py template_bg  # 特定テンプレートのみ → template_bg.pptx
"""
import json
import os
import re
import sys
import glob
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

# コマンドライン引数で特定テンプレートのみ処理するか、すべて処理するか判定
_arg = sys.argv[1] if len(sys.argv) > 1 else None
if _arg and not _arg.endswith(".html"):
    _arg = _arg + ".html"

def find_template_files():
    """template_*.html ファイルをすべて検出"""
    pattern = os.path.join(HERE, "template_*.html")
    files = sorted(glob.glob(pattern))

    # token-monitor.html は除外
    files = [f for f in files if not f.endswith("token-monitor.html")]

    return files

def extract_design_and_slides(html_content, filename):
    """HTML から D（デザイン・スライドデータ）を抽出"""
    D = {}

    # const D = {...} を抽出
    _m = re.search(r'const D = (\{[\s\S]+?\});\s*\n\nD\.COLORS', html_content)
    if not _m:
        raise ValueError(f"{filename} 内に const D = {{...}} が見つかりません")
    D = json.loads(_m.group(1))

    # SLIDES: テンプレートリテラル (`...`) を JSON 文字列に変換
    _s = re.search(r'const SLIDES = (\[[\s\S]+?\]); // END_SLIDES', html_content)
    if not _s:
        raise ValueError(f"{filename} 内に const SLIDES が見つかりません")
    _slides_js = re.sub(r'`([\s\S]*?)`', lambda m: json.dumps(m.group(1)), _s.group(1))
    D["SLIDES"] = json.loads(_slides_js)

    # DESIGN: COLORS・FONTS を D にマージ
    _d = re.search(r'const DESIGN = (\{[\s\S]+?\}); // END_DESIGN', html_content)
    if not _d:
        raise ValueError(f"{filename} 内に const DESIGN が見つかりません")
    _design_json = re.sub(r'\s*//[^\n]*', '', _d.group(1))
    D.update(json.loads(_design_json))

    return D


def rgb(hex6):
    return RGBColor.from_string(hex6)


def _no_shadow(shape):
    """シェイプのシャドウ・エフェクトをクリアする"""
    spPr = shape._element.spPr
    for old in spPr.findall(qn("a:effectLst")):
        spPr.remove(old)
    spPr.append(spPr.makeelement(qn("a:effectLst"), {}))


def rect(slide, x, y, w, h, fill, line_color=None, line_w=None):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    if line_color:
        shape.line.color.rgb = rgb(line_color)
        shape.line.width = Pt(line_w or 0.75)
    else:
        shape.line.fill.background()
    _no_shadow(shape)
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
         anchor=MSO_ANCHOR.MIDDLE, align=None):
    from pptx.enum.text import PP_ALIGN
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    _fix_bodyPr(tf)
    p = tf.paragraphs[0]
    if align:
        p.alignment = align
    _add_runs(p, txt, size, bold, color)
    _no_shadow(box)
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

        bold = item_type == "heading"
        _add_runs(p, item_text, size, bold, color)
        _set_line_spacing(p, size, mult=1.8)

    _no_shadow(box)
    return box


def hline(slide, x, y, w, color, width_pt=1):
    shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Pt(width_pt))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(color)
    shape.line.fill.background()
    _no_shadow(shape)
    return shape


def arrow_shape(slide, x, y, w, h, fill_hex, border_hex="CCCCCC", border_w=0.75):
    """右向き五角形矢印シェイプ（カスタムジオメトリ）を描画する - 枠線付き"""
    from pptx.oxml import parse_xml
    x_emu = int(Inches(x))
    y_emu = int(Inches(y))
    w_emu = int(Inches(w))
    h_emu = int(Inches(h))
    fill = fill_hex.upper()
    border = border_hex.upper()
    border_emu = int(border_w * 12700)  # a:ln w 属性の単位: 1/12700 EMU = 1/100 pt

    # 既存シェイプの最大IDを取得して衝突を避ける
    ids = [int(e.get("id")) for e in slide.shapes._spTree.iter()
           if e.get("id") and e.get("id").isdigit()]
    shape_id = (max(ids) + 1) if ids else 100

    NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
    NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    sp_xml = (
        f'<p:sp xmlns:p="{NS_P}" xmlns:a="{NS_A}">'
        f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="Step{shape_id}"/>'
        '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
        '<p:spPr>'
        f'<a:xfrm><a:off x="{x_emu}" y="{y_emu}"/>'
        f'<a:ext cx="{w_emu}" cy="{h_emu}"/></a:xfrm>'
        '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
        '<a:rect l="0" t="0" r="r" b="b"/>'
        '<a:pathLst><a:path w="100000" h="100000">'
        '<a:moveTo><a:pt x="0" y="0"/></a:moveTo>'
        '<a:lnTo><a:pt x="88000" y="0"/></a:lnTo>'
        '<a:lnTo><a:pt x="100000" y="50000"/></a:lnTo>'
        '<a:lnTo><a:pt x="88000" y="100000"/></a:lnTo>'
        '<a:lnTo><a:pt x="0" y="100000"/></a:lnTo>'
        '<a:close/></a:path></a:pathLst></a:custGeom>'
        f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        f'<a:ln w="{border_emu}"><a:solidFill><a:srgbClr val="{border}"/></a:solidFill></a:ln>'
        '<a:effectLst/>'
        '</p:spPr>'
        '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>'
        '</p:sp>'
    )
    slide.shapes._spTree.append(parse_xml(sp_xml))


def parse_md(md):
    """Markdownをパースしてセクションのリストを返す。
    戻り値: [(title, items), ...]
      items: list of ('bullet'|'para', text)
    **bold** / *italic* などのインラインマーカーは除去。
    """
    sections = []
    cur_title = ""
    cur_items = []
    for line in md.strip().split("\n"):
        s = line.strip()
        if not s:
            continue
        m = re.match(r"^#{1,6}\s+(.*)", s)
        if m:
            if cur_title or cur_items:
                sections.append((cur_title, cur_items))
                cur_items = []
            cur_title = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", m.group(1))
        elif re.match(r"^[-*+]\s+", s):
            content = re.sub(r"^[-*+]\s+", "", s)
            content = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", content)
            cur_items.append(("bullet", content))
        else:
            content = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", s)
            cur_items.append(("para", content))
    if cur_title or cur_items:
        sections.append((cur_title, cur_items))
    return sections


def build(prs, sd, D, COLORS, FONTS):
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

    # ── 背景ボックス（bg テンプレートのみ） ──
    if "BG_BOX" in D and "bg" in sd:
        B = D["BG_BOX"]
        bp = {"x": B.get("padX", 0.2), "y": B.get("padY", 0.15)}
        doy = D["CARD_DIVIDER_OFFSET_Y"]
        bg_sections = parse_md(sd["bg"]["markdown"])
        bg_title, bg_items = bg_sections[0] if bg_sections else ("", [])
        rect(slide, B["x"], B["y"], B["w"], B["h"], C.get("bgBox", "E8EDF2"), C["border"], 0.75)
        text(slide, bg_title,
             B["x"] + bp["x"], B["y"] + bp["y"], B["w"] - bp["x"] * 2, 0.35,
             F.get("bgTitle", F["cardTitle"])["size"],
             F.get("bgTitle", F["cardTitle"])["bold"], C["text"],
             anchor=MSO_ANCHOR.TOP)
        hline(slide, B["x"] + bp["x"], B["y"] + doy, B["w"] - bp["x"] * 2, C["border"], 1.0)
        if bg_items:
            md_content(slide, bg_items,
                       B["x"] + bp["x"], B["y"] + doy + 0.12,
                       B["w"] - bp["x"] * 2,
                       B["h"] - doy - bp["y"] - 0.12,
                       F.get("bgBody", F["cardBody"])["size"], C["text"])

    # ── 下矢印（diffuse テンプレートのみ） ──
    if "ARROW" in D:
        A = D["ARROW"]
        arrow_color = C.get("arrow", "6B7A99")
        shape = slide.shapes.add_shape(1, Inches(A["x"]), Inches(A["y"]), Inches(A["w"]), Inches(A["h"]))
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(arrow_color)
        shape.line.fill.background()
        _no_shadow(shape)
        # カスタム三角形（下向き）に差し替え
        from pptx.oxml import parse_xml
        spPr = shape._element.spPr
        # custGeom で下向き三角形を定義
        x_emu = int(Inches(A["x"]))
        y_emu = int(Inches(A["y"]))
        w_emu = int(Inches(A["w"]))
        h_emu = int(Inches(A["h"]))
        NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
        NS_P = "http://schemas.openxmlformats.org/presentationml/2006/main"
        ids = [int(e.get("id")) for e in slide.shapes._spTree.iter()
               if e.get("id") and e.get("id").isdigit()]
        shape_id = (max(ids) + 1) if ids else 200
        fill_hex = arrow_color.upper()
        tri_xml = (
            f'<p:sp xmlns:p="{NS_P}" xmlns:a="{NS_A}">'
            f'<p:nvSpPr><p:cNvPr id="{shape_id}" name="Arrow{shape_id}"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr>'
            f'<a:xfrm><a:off x="{x_emu}" y="{y_emu}"/>'
            f'<a:ext cx="{w_emu}" cy="{h_emu}"/></a:xfrm>'
            '<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
            '<a:rect l="0" t="0" r="r" b="b"/>'
            '<a:pathLst><a:path w="100000" h="100000">'
            '<a:moveTo><a:pt x="0" y="0"/></a:moveTo>'
            '<a:lnTo><a:pt x="100000" y="0"/></a:lnTo>'
            '<a:lnTo><a:pt x="50000" y="100000"/></a:lnTo>'
            '<a:close/></a:path></a:pathLst></a:custGeom>'
            f'<a:solidFill><a:srgbClr val="{fill_hex}"/></a:solidFill>'
            '<a:ln><a:noFill/></a:ln>'
            '<a:effectLst/>'
            '</p:spPr>'
            '<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>'
            '</p:sp>'
        )
        slide.shapes._spTree.append(parse_xml(tri_xml))
        # 元の矩形シェイプを削除
        sp_elem = shape._element
        sp_elem.getparent().remove(sp_elem)

    # ── プレーン2カラム ──
    if "PLAIN_COLS" in D and "columns" in sd:
        for i, col in enumerate(sd["columns"]):
            if i >= len(D["PLAIN_COLS"]):
                break
            B = D["PLAIN_COLS"][i]
            bp = {"x": B.get("padX", 0.25), "y": B.get("padY", 0.15)}
            sections = parse_md(col["markdown"])
            all_items = []
            for sec_title, sec_items in sections:
                if sec_title:
                    all_items.append(("heading", sec_title))
                all_items.extend(sec_items)
            if all_items:
                md_content(slide, all_items,
                           B["x"] + bp["x"], B["y"] + bp["y"],
                           B["w"] - bp["x"] * 2, B["h"] - bp["y"] * 2,
                           F["bodyText"]["size"] if "bodyText" in F else F["cardBody"]["size"],
                           C["text"])

    # ── プレーンボディ ──
    if "PLAIN_BOX" in D and "body" in sd:
        B = D["PLAIN_BOX"]
        bp = {"x": B.get("padX", 0.25), "y": B.get("padY", 0.15)}
        sections = parse_md(sd["body"]["markdown"])
        all_items = []
        for sec_title, sec_items in sections:
            if sec_title:
                all_items.append(("heading", sec_title))
            all_items.extend(sec_items)
        if all_items:
            md_content(slide, all_items,
                       B["x"] + bp["x"], B["y"] + bp["y"],
                       B["w"] - bp["x"] * 2, B["h"] - bp["y"] * 2,
                       F["bodyText"]["size"] if "bodyText" in F else F["cardBody"]["size"],
                       C["text"])

    # ── カード ──
    for i, cd in enumerate(sd.get("cards", [])):
        c = D["CARDS"][i]
        cp = D["CARD_PAD"]
        doy = D["CARD_DIVIDER_OFFSET_Y"]

        sections = parse_md(cd["markdown"])

        rect(slide, c["x"], c["y"], c["w"], c["h"], C["surface"], C["border"], 0.75)

        if len(sections) <= 1:
            # 単一セクション（従来通り）
            card_title, items = sections[0] if sections else ("", [])
            text(slide, card_title,
                 c["x"] + cp["x"], c["y"] + cp["y"], c["w"] - cp["x"] * 2, 0.35,
                 F["cardTitle"]["size"], F["cardTitle"]["bold"], C["text"],
                 anchor=MSO_ANCHOR.TOP)
            hline(slide, c["x"] + cp["x"], c["y"] + doy, c["w"] - cp["x"] * 2, C["border"], 1.0)
            if items:
                bx = c["x"] + cp["x"]
                by = c["y"] + doy + 0.12
                bw = c["w"] - cp["x"] * 2
                bh = c["h"] - doy - cp["y"] - 0.12
                md_content(slide, items, bx, by, bw, bh, F["cardBody"]["size"], C["text"])
        else:
            # 複数セクション：コンテンツ量から自然な高さを計算して積み上げ
            item_h_in = (F["cardBody"]["size"] * 1.8 + 4) / 72  # 行間1.8 + space_after 4pt → inch
            cur_y = c["y"]
            for j, (sec_title, sec_items) in enumerate(sections):
                # 1つ目はカード上余白、以降は小さい隙間のみ
                pre_pad = cp["y"] if j == 0 else 0.09
                sec_doy = pre_pad + 0.35  # タイトル高さ0.35の直後に区切り線
                text(slide, sec_title,
                     c["x"] + cp["x"], cur_y + pre_pad, c["w"] - cp["x"] * 2, 0.35,
                     F["cardTitle"]["size"], F["cardTitle"]["bold"], C["text"],
                     anchor=MSO_ANCHOR.TOP)
                hline(slide, c["x"] + cp["x"], cur_y + sec_doy, c["w"] - cp["x"] * 2, C["border"], 1.0)
                if sec_items:
                    bx = c["x"] + cp["x"]
                    by = cur_y + sec_doy + 0.12
                    bw = c["w"] - cp["x"] * 2
                    bh = len(sec_items) * item_h_in
                    md_content(slide, sec_items, bx, by, bw, bh, F["cardBody"]["size"], C["text"])
                cur_y += sec_doy + 0.12 + len(sec_items) * item_h_in

    # ── フッター ──
    hline(slide, 0, FT["y"], FT["w"], C["border"], 0.75)

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
        pic = slide.shapes.add_picture(
            logo_path,
            Inches(D["SLIDE_W"] - FT["padX"] - 1.0),
            Inches(footer_center_y - logo_h / 2),
            height=Inches(logo_h),
        )
        _no_shadow(pic)


def build_flow(prs, sd, D, COLORS, FONTS):
    """フロー図テンプレート（STEPS）用のビルド関数"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    H = D["HEADER"]
    FT = D["FOOTER"]
    C = COLORS
    F = FONTS

    # ── スライド背景を白に設定 ──
    from pptx.oxml.ns import qn as _qn
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = rgb(C.get("bg", "FFFFFF"))

    # ── ヘッダー帯 ──
    rect(slide, H["x"], H["y"], H["w"], H["h"], C["headerBg"])
    text(slide, sd["header"]["title"],
         H["padX"], H["padY"] + 0.013, H["w"] - H["padX"] * 2, 0.45,
         F["title"]["size"], F["title"]["bold"], C["headerText"])
    text(slide, sd["header"]["message"],
         H["padX"], H["padY"] + 0.45 + 0.042, H["w"] - H["padX"] * 2, 0.3,
         F["message"]["size"], F["message"]["bold"], C["headerText"])

    # ── ステップ矢印 ──
    for i, step in enumerate(sd["steps"]):
        if i >= len(D["STEPS"]):
            break
        s = D["STEPS"][i]

        # 矢印シェイプ
        arrow_shape(slide, s["x"], s["y"], s["w"], s["h"], C["stepFill"])

        # ラベル（矢印の先端部分を除いた88%幅に左揃え）
        text(slide, step["label"],
             s["x"] + 0.15, s["y"], s["w"] * 0.88 - 0.15, s["h"],
             F["stepLabel"]["size"], F["stepLabel"]["bold"], C["stepText"])

        # 箇条書きボックス（HTMLと同じ高さ: FOOTER.y - BULLETS_Y - 0.1）
        bullets_y = D["BULLETS_Y"]
        bh = D["FOOTER"]["y"] - bullets_y - 0.1
        cp = 0.1  # カードパディング
        rect(slide, s["x"], bullets_y, s["w"], bh,
             C.get("surface", "F5F5F5"), C["border"], 0.75)

        # 箇条書きテキスト（md_contentでHTML同様のline-height:1.8）
        items = [("bullet", b) for b in step["bullets"]]
        md_content(slide, items,
                   s["x"] + cp, bullets_y + cp,
                   s["w"] - cp * 2, bh - cp * 2,
                   F["bullet"]["size"], C["text"])

    # ── フッター ──
    hline(slide, 0, FT["y"], FT["w"], C["border"], 0.75)
    footer_center_y = FT["y"] + FT["h"] / 2
    page_h = 0.3
    logo_h = D["LOGO_H"]
    box = text(slide, sd["page"],
               FT["padX"], footer_center_y - page_h / 2, 2, page_h,
               F["footer"]["size"], False, C["textMuted"])
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    logo_path = os.path.join(HERE, sd["logo"])
    if os.path.exists(logo_path):
        pic = slide.shapes.add_picture(
            logo_path,
            Inches(D["SLIDE_W"] - FT["padX"] - 1.0),
            Inches(footer_center_y - logo_h / 2),
            height=Inches(logo_h),
        )
        _no_shadow(pic)


def _set_table_cell(cell, cell_text, size, bold, text_color, bg_color, border_color):
    """テーブルセルのテキスト・背景色・罫線を設定"""
    from pptx.oxml import parse_xml as _px
    NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"

    tf = cell.text_frame
    tf.margin_left = tf.margin_right = Pt(7)
    tf.margin_top = tf.margin_bottom = Pt(3)
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    _add_runs(tf.paragraphs[0], cell_text, size, bold, text_color)

    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for old in tcPr.findall(qn("a:solidFill")):
        tcPr.remove(old)
    tcPr.insert(0, _px(
        f'<a:solidFill xmlns:a="{NS_A}"><a:srgbClr val="{bg_color.upper()}"/></a:solidFill>'
    ))
    border_emu = str(int(0.75 * 12700))
    for edge in ("lnL", "lnR", "lnT", "lnB"):
        for old in tcPr.findall(qn(f"a:{edge}")):
            tcPr.remove(old)
        tcPr.append(_px(
            f'<a:{edge} xmlns:a="{NS_A}" w="{border_emu}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{border_color.upper()}"/></a:solidFill>'
            f'<a:prstDash val="solid"/></{edge.replace("a:", "a:")}>'
            .replace(f'</{edge.replace("a:", "a:")}>', f'</a:{edge}>')
        ))


def build_table_slide(prs, sd, D, COLORS, FONTS):
    """テーブルテンプレート用のビルド関数"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    H = D["HEADER"]
    FT = D["FOOTER"]
    C = COLORS
    F = FONTS

    # ── ヘッダー帯 ──
    rect(slide, H["x"], H["y"], H["w"], H["h"], C["headerBg"])
    text(slide, sd["header"]["title"],
         H["padX"], H["padY"] + 0.013, H["w"] - H["padX"] * 2, 0.45,
         F["title"]["size"], F["title"]["bold"], C["headerText"])
    text(slide, sd["header"]["message"],
         H["padX"], H["padY"] + 0.45 + 0.042, H["w"] - H["padX"] * 2, 0.3,
         F["message"]["size"], F["message"]["bold"], C["headerText"])

    # ── テーブル ──
    BOX = D["TABLE_BOX"]
    t = sd["table"]
    head = t.get("head", [])
    rows = t.get("rows", [])
    has_head = bool(head)
    num_cols = max(len(head) if head else 0, max((len(r) for r in rows), default=0))
    num_rows = len(rows) + (1 if has_head else 0)

    if num_rows > 0 and num_cols > 0:
        tbl_shape = slide.shapes.add_table(
            num_rows, num_cols,
            Inches(BOX["x"]), Inches(BOX["y"]),
            Inches(BOX["w"]), Inches(BOX["h"])
        )
        tbl = tbl_shape.table

        # firstRow/bandRow スタイルフラグを除去（組み込みスタイルの干渉防止）
        tbl_pr = tbl._tbl.find(qn("a:tblPr"))
        if tbl_pr is not None:
            tbl_pr.attrib.pop("firstRow", None)
            tbl_pr.attrib.pop("bandRow", None)
            tbl_pr.attrib.pop("firstCol", None)

        # 列幅・行高を均等に明示設定（HTML の table-layout:fixed と一致させる）
        col_w = Inches(BOX["w"] / num_cols)
        row_h = Inches(BOX["h"] / num_rows)
        for j in range(num_cols):
            tbl.columns[j].width = col_w
        for i in range(num_rows):
            tbl.rows[i].height = row_h

        if has_head:
            for j, ct in enumerate(head[:num_cols]):
                _set_table_cell(tbl.cell(0, j), ct,
                                F["tableHead"]["size"], True,
                                C["tableHeadText"], C["tableHead"], C["tableBorder"])

        row_offset = 1 if has_head else 0
        for i, row in enumerate(rows):
            bg = C["tableRowAlt"] if i % 2 == 1 else C["tableRow"]
            for j, ct in enumerate(row[:num_cols]):
                if j == 0:
                    _set_table_cell(tbl.cell(i + row_offset, j), ct,
                                    F["tableHead"]["size"], True,
                                    C["tableHeadText"], C["tableHead"], C["tableBorder"])
                else:
                    _set_table_cell(tbl.cell(i + row_offset, j), ct,
                                    F["tableBody"]["size"], False,
                                    C["tableText"], bg, C["tableBorder"])

    # ── フッター ──
    hline(slide, 0, FT["y"], FT["w"], C["border"], 0.75)
    footer_center_y = FT["y"] + FT["h"] / 2
    page_h = 0.3
    logo_h = D["LOGO_H"]
    box = text(slide, sd["page"],
               FT["padX"], footer_center_y - page_h / 2, 2, page_h,
               F["footer"]["size"], False, C["textMuted"])
    box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    logo_path = os.path.join(HERE, sd["logo"])
    if os.path.exists(logo_path):
        pic = slide.shapes.add_picture(
            logo_path,
            Inches(D["SLIDE_W"] - FT["padX"] - 1.0),
            Inches(footer_center_y - logo_h / 2),
            height=Inches(logo_h),
        )
        _no_shadow(pic)


def build_cover(prs, sd, D, COLORS, FONTS):
    """表紙テンプレート用のビルド関数"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    # ── 背景画像（最初に追加してz順を最背面に） ──
    bg_path = os.path.join(HERE, sd["bg"])
    if os.path.exists(bg_path):
        slide.shapes.add_picture(
            bg_path, Inches(0), Inches(0),
            width=Inches(D["SLIDE_W"]), height=Inches(D["SLIDE_H"])
        )

    cx = D["CONTENT_X"]
    cw = D["CONTENT_W"]

    # ── タイトル（\n で明示改行） ──
    title_lines = sd["title"].split("\n")
    box = slide.shapes.add_textbox(
        Inches(cx), Inches(D["TITLE_Y"]),
        Inches(cw), Inches(D["TITLE_H"])
    )
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    _fix_bodyPr(tf)
    for i, line in enumerate(title_lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        _add_runs(p, line, FONTS["title"]["size"], FONTS["title"]["bold"], COLORS["title"])
        _set_line_spacing(p, FONTS["title"]["size"], mult=1.4)
    _no_shadow(box)

    # ── 区切り線 ──
    hline(slide, D["DIVIDER_X"], D["DIVIDER_Y"], D["DIVIDER_W"], COLORS["divider"], 0.75)

    # ── 所属・発表者・日付 ──
    for item in D["META_ITEMS"]:
        text(slide, sd[item["key"]],
             cx, item["y"], cw, 0.35,
             FONTS["meta"]["size"], FONTS["meta"]["bold"], COLORS["meta"])


def main():
    """すべてのテンプレートを一つの PPTX に統合"""
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)

    # テンプレートファイルを検出
    if _arg:
        # 特定テンプレート
        template_files = [os.path.join(HERE, _arg)]
        out_name = os.path.splitext(_arg)[0] + ".pptx"
    else:
        # すべてのテンプレート
        template_files = find_template_files()
        out_name = "all_templates.pptx"

    total_slides = 0

    print(f"[Info] Processing templates: {len(template_files)} files")
    print("=" * 60)

    for template_path in template_files:
        template_name = os.path.basename(template_path)
        print(f"[*] {template_name}...", end=" ")

        try:
            with open(template_path, encoding="utf-8") as f:
                html_content = f.read()

            # D（デザイン・スライドデータ）を抽出
            D = extract_design_and_slides(html_content, template_name)

            # ビルド関数を選択
            if "STEPS" in D:
                builder = build_flow
            elif "META_ITEMS" in D:
                builder = build_cover
            elif "TABLE_BOX" in D:
                builder = build_table_slide
            else:
                builder = build

            # スライドを追加
            slides_count = len(D.get("SLIDES", []))
            for sd in D["SLIDES"]:
                builder(prs, sd, D, D["COLORS"], D["FONTS"])

            total_slides += slides_count
            print(f"OK ({slides_count} slides)")

        except Exception as e:
            print(f"ERROR: {e}")
            continue

    print("=" * 60)
    print(f"[Done] Total slides: {total_slides}")

    # PPTX ファイルを保存
    out_path = os.path.join(HERE, out_name)
    prs.save(out_path)
    print(f"[Save] {out_path}")
    print(f"[Size] {os.path.getsize(out_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
