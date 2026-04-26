# Overflow Test Plan — deck-from-source

このファイルは `overflow_analysis.py` と `generate_test_slides.py` の実装仕様書。
Codex はこのファイルを読み、2 本のスクリプトを `.claude/skills/deck-from-source/` に作成すること。

---

## 背景と目的

`to_pptx.py` は全テキストボックスに `tf.word_wrap = True` + `noAutofit` を設定している。
そのため文字数が多いとテキストが視覚的にはみ出すが、python-pptx はエラーを出さない。

**目的**: 各レイアウト・セルタイプ・文字種ごとの「はみ出さない最大文字量」を定量化する。

---

## 重要な前提: word_wrap による自動折り返し

1つの段落（箇条書き1項目）が幅を超えると自動的に折り返され、複数の「視覚行」になる。

```
chars_per_visual_line = floor(text_width_pt / char_width_pt)
visual_lines(item)    = ceil(item_chars / chars_per_visual_line)
total_visual_lines    = Σ visual_lines(item_i)  ← これが上限を超えるとオーバーフロー
max_visual_lines      = floor(text_height_pt / line_height_pt)
```

折り返しの挙動差:
- **CJK (Meiryo)**: 文字単位で折り返す → chars_per_visual_line が整数で決まる
- **ASCII (Segoe UI)**: 単語境界で折り返す → 実際は近似値（単語の長さに依存）
- **混在**: CJK 部分は文字単位、ASCII 単語は単語境界

---

## スライド寸法と重要パラメータ（design.json より）

```python
# LAYOUT
slideW    = 10.0   # inches
slideH    = 5.625
headerH   = 0.85
footerY   = 5.225
mainPadX  = 0.1
mainPadY  = 0.1
gridGap   = 0.08
cardPadX  = 0.15
cardPadY  = 0.12
cardDivY  = 0.4    # カードタイトル区切り線の y オフセット（cy からの距離）
headerPadX = 0.25
conclusionAccentW = 0.07

# メインコンテンツ域
mainX = mainPadX            # = 0.1
mainY = headerH + mainPadY  # = 0.95
mainW = slideW - mainPadX*2 # = 9.8
mainH = footerY - mainY - mainPadY  # = 4.175
```

フォント（design.json FONTS より）:
```python
FONTS = {
    "cardTitle": {"size": 14, "bold": True},
    "cardBody":  {"size": 11, "bold": False},  # list_3card 等のカード本文
    "bodyHead":  {"size": 12, "bold": True},   # plain レイアウトの見出し
    "bodyText":  {"size": 12, "bold": False},  # plain レイアウトの本文
    "bgTitle":   {"size": 13, "bold": True},
    "bgBody":    {"size": 12, "bold": False},
    "stepLabel": {"size": 14, "bold": True},
    "conclTitle":{"size": 13, "bold": True},
    "conclBody": {"size": 12, "bold": False},
}
```

行間（to_pptx.py の `_set_line_spacing` + `space_after` より）:
```python
# md_content() 内
line_spacing_mult = {
    "heading":    1.4,   # space_after = 3pt, space_before = 8pt (2行目以降)
    "bullet":     1.8,   # space_after = 4pt
    "bullet2":    1.8,   # space_after = 4pt (インデント増)
    "ordered":    1.8,
    "para":       1.8,
}
# 1視覚行の高さ = font_size * mult + space_after

# 箇条書きインデント (EMU)
BULLET_INDENT_EMU  = 228600  # ≈ 0.25 inches
BULLET2_INDENT_EMU = 457200  # ≈ 0.5 inches
```

文字幅近似値:
```python
# CJK (Meiryo, 全角): 1em = font_size pt
# ASCII (Segoe UI, 半角): 平均 0.55em = font_size * 0.55 pt
# 全角記号 (！？＠等): CJK扱い = font_size pt
# 半角記号 (!?@ 等): ASCII扱い = font_size * 0.5 pt
```

---

## セルタイプ別テキスト領域の計算方法

### compute_cells() の再現（to_pptx.py 参照）

```python
def compute_cells(grid, rowHeightRatios):
    mainX = 0.1; mainY = 0.95; mainW = 9.8; mainH = 4.175; gap = 0.08
    numRows = len(grid)
    numCols = max(sum(c.get("span",1) for c in row) for row in grid)
    rowHeights = [mainH * r for r in rowHeightRatios]

    def rowTop(r): return mainY + sum(rowHeights[:r])
    unitW = (mainW - gap * (numCols + 1)) / numCols

    cells = []
    for ri, row in enumerate(grid):
        col = 0
        for cell in row:
            span = cell.get("span", 1)
            cx = mainX + gap + col * (unitW + gap)
            cy = rowTop(ri) + (gap if ri == 0 else gap / 2)
            cw = unitW * span + gap * (span - 1)
            ch = rowHeights[ri] - (gap if ri==0 else gap/2) - (gap if ri==numRows-1 else gap/2)
            cells.append({"cell": cell, "x": cx, "y": cy, "w": cw, "h": ch})
            col += span
    return cells
```

### セルタイプ別テキスト領域

```python
def text_area(cell_type, cx, cy, cw, ch):
    """Returns (text_x, text_y, text_w, text_h) in inches"""
    if cell_type == "card":
        # タイトルあり前提: 本文は divider 以降
        divY_abs = cy + 0.4          # cardDivY = 0.4
        body_x = cx + 0.15           # cardPadX
        body_y = divY_abs + 0.08
        body_w = cw - 0.15*2
        body_h = (cy + ch) - divY_abs - 0.08 - 0.12  # - cardPadY
        return (body_x, body_y, body_w, body_h)

    elif cell_type == "plain":
        # render_cell type="plain" は headerPadX / mainPadY を使用
        return (cx + 0.25, cy + 0.1, cw - 0.25*2, ch - 0.1*2)

    elif cell_type == "section":
        return (cx + 0.15, cy + 0.12, cw - 0.15*2, ch - 0.12*2)

    elif cell_type == "conclusion":
        accentW = 0.07
        return (cx + accentW + 0.15, cy + 0.12,
                cw - accentW - 0.15*2, ch - 0.12*2)
```

### plain_2col の寸法（compute_cells() 由来）

`plain_2col` は `templates.json` で `"engine": "area"` / `plain` × 2セルの通常グリッドとして定義されており、
`render_plain2col()` ではなく `compute_cells()` + `render_cell(type="plain")` で描画される。
`render_plain2col()` はデッドコードであるため参照してはならない。

```python
# plain_2col: numCols=2, numRows=1, rowHeightRatios=[1.0]
# compute_cells() から導出:
unitW = (9.8 - 0.08 * (2+1)) / 2  # = (9.8 - 0.24) / 2 = 4.78 inches
cy    = 0.95 + 0.08                # = 1.03 inches
ch    = 4.175 - 0.08 - 0.08       # = 4.015 inches  (ri=0 かつ最終行)

# plain セルのテキスト領域 (render_cell type="plain"):
#   padX = headerPadX = 0.25, padY = mainPadY = 0.1
text_w = unitW - 0.25*2   # = 4.28 inches = 308 pt
text_h = ch - 0.1*2       # = 3.815 inches = 275 pt
```

---

## Script 1: `overflow_analysis.py`

**出力**: コンソール表示 + `overflow_analysis.csv` + `overflow_analysis.md`

### 処理手順

1. `design.json` と `templates.json` を読み込む（スクリプトと同じディレクトリから）
2. 各レイアウトの `grid` と `rowHeightRatios` を取得
3. `compute_cells()` でセル座標を計算
4. セルタイプごとにテキスト領域を算出（上記の関数を使用）
5. 各セルに適用するフォントとその行間を決定（セルタイプ別）:

   | cell_type  | font key   | size | spacing | space_after | renderer    |
   |-----------|-----------|------|---------|------------|------------|
   | `card`     | cardBody   | 11pt | 1.8×    | 4pt        | md_content |
   | `plain`    | bodyText   | 12pt | 1.8×    | 4pt        | md_content |
   | `section`  | bgBody     | 12pt | 1.8×    | 4pt        | md_content |
   | `conclusion`| conclBody | 12pt | 1.8×    | 4pt        | md_content |
   | `step_head`| stepLabel  | 14pt | 1.0×(※)| 0pt        | text()     |

   ※ `step_head` は `text()` 関数で描画し `_set_line_spacing` を呼ばないため、
   PowerPoint デフォルトの単一行間（≒ 1.2×）を適用する。

6. 計算:
   ```python
   # md_content セル（bullet 前提）
   line_height_pt = font_size * line_spacing + space_after  # e.g. 11*1.8+4 = 23.8
   max_visual_lines = math.floor(text_h_inches * 72 / line_height_pt)

   # step_head セル（text() 関数: 行間≒1.2×、space_after=0）
   step_line_height_pt = step_font_size * 1.2  # = 14*1.2 = 16.8
   step_max_visual_lines = math.floor(step_text_h_inches * 72 / step_line_height_pt)

   text_w_pt = text_w_inches * 72

   # 箇条書き（bullet）の場合は marL 分だけ幅を減らす
   BULLET_MARGIN_PT = 228600 / 914400 * 72  # ≈ 18pt
   bullet_w_pt = text_w_pt - BULLET_MARGIN_PT

   chars_cjk   = math.floor(bullet_w_pt / font_size)
   chars_ascii = math.floor(bullet_w_pt / (font_size * 0.55))
   chars_mixed = math.floor(bullet_w_pt / (font_size * 0.775))
   ```

   **スコープの明示**: `simulate_fit()` は**単一レベルの箇条書き（bullet）のみ**を対象とする。
   heading・nested bullet・ordered list・blockquote は段落タイプ別に行間・インデントが異なるため、
   このスクリプトの推定値は「箇条書きのみで構成されたカード」にのみ有効である。
   出力テーブルにはこの旨を明記すること。

7. simulate_fit 関数で「N項目 × M文字ならいくつ入るか」を計算（bullet 専用）:
   ```python
   def simulate_fit_bullets(max_vis, chars_per_line, item_char_counts):
       """
       単一レベルの箇条書き（bullet）のみ有効。
       heading/nested/ordered/blockquote は含めないこと。
       item_char_counts: 各箇条書き項目の文字数リスト
       returns: (total_visual_lines, overflows: bool)
       """
       total = 0
       for n in item_char_counts:
           total += math.ceil(n / chars_per_line)
       return total, total > max_vis
   ```

8. 出力テーブルの列:
   - layout, cell_type, text_w_in, text_h_in, font_size, max_visual_lines
   - CJK_chars_per_visual_line, ASCII_chars_per_visual_line, Mixed_chars_per_visual_line
   - max_items_at_15CJK, max_items_at_40CJK, max_items_at_25ASCII, max_items_at_35ASCII
   - (**step_head 行のみ**) step_label_text_w_in, step_label_text_h_in, step_max_visual_lines, step_CJK_per_line, step_ASCII_per_line

9. (optional) fonttools による実測補正:
   ```python
   try:
       from fonttools.ttLib import TTFont
       import os
       meiryo_path = r"C:\Windows\Fonts\meiryo.ttc"
       segoe_path  = r"C:\Windows\Fonts\segoeui.ttf"
       # ... advance width を取得して char_width_pt を補正
   except ImportError:
       pass  # 近似値のまま
   ```

### 出力例
```
※ bullet-only スコープ（heading/nested/ordered 非対応）

layout       | cell      | w(in) | h(in) | font | max_vis | CJK/ln | ASCII/ln | items@15CJK | items@40CJK | items@25ASCII
-------------|-----------|-------|-------|------|---------|--------|----------|-------------|-------------|---------------
list_3card   | card      | 2.86  | 3.42  | 11pt | 10      | 18     | 33       | 10          | 4           | 10
plain_1col   | plain     | 9.14  | 3.82  | 12pt | 10      | 54     | 98       | 10          | 10          | 10
plain_2col   | plain     | 4.28  | 3.82  | 12pt | 10      | 25     | 46       | 10          | 5           | 10
flow_3step   | card      | 2.86  | 2.29  | 11pt |  7      | 18     | 33       |  7          | 3           |  7
flow_3step   | step_head | 2.69  | 1.05  | 14pt |  4      | 13     | 25       | (label: max ~13 CJK / ~25 ASCII per visual line)
flow_4step   | card      | 2.05  | 2.29  | 11pt |  7      | 11     | 20       |  7          | 3           |  7
flow_4step   | step_head | 2.00  | 1.05  | 14pt |  4      | 10     | 18       | (label: max ~10 CJK / ~18 ASCII per visual line)
diffuse_3card| card      | 2.86  | 2.08  | 11pt |  6      | 18     | 33       |  6          | 3           |  6
```

---

## Script 2: `generate_test_slides.py`

**出力**: `overflow_test.pptx`（全テストスライドを1ファイルに格納）

### テスト軸

**対象レイアウト**: `list_3card`, `plain_1col`, `plain_2col`, `flow_3step`, `flow_4step`, `diffuse_3card`

`flow_3step` / `flow_4step` はカード本文テストに加え、**step_head ラベルテストを別途生成する**（後述）。

**軸A: 項目数 N**: `[3, 5, 7, 10]`

**軸B: 文字種 × 折り返しパターン**:

| 種別ID | 内容 | 文字数 |
|--------|------|------|
| `cjk_short` | 全角日本語（≤1視覚行想定） | 15字 |
| `cjk_long`  | 全角日本語（折り返し発生想定） | 40字 |
| `ascii_short` | 半角英語（単語区切りあり） | 25字 |
| `ascii_long`  | 半角英語（折り返し発生想定） | 35字 |
| `symbol_zen`  | 全角記号混在 `！？＠＃` | 20字 |
| `symbol_han`  | 半角記号混在 `!? @#$%` | 30字 |
| `mixed`       | 全角+半角+記号混在 | 25字 |

### テキストサンプル（各種別の1項目の文字列）

```python
SAMPLES = {
    "cjk_short":   "あいうえおかきくけこさしすせそ",         # 15字
    "cjk_long":    "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめも",  # 40字
    "ascii_short": "the quick brown fox jumps",              # 25字
    "ascii_long":  "the quick brown fox jumps over the lazy",  # 40字(折り返し確認)
    "symbol_zen":  "！？＠＃あいうえお！？＠＃あいうえお",    # 20字
    "symbol_han":  "text!? code@#$% number:123 key=val",     # 35字
    "mixed":       "テキスト text 記号!? 数字123 あいう",     # 25字相当
}
```

### 生成方法

一時的な deck.md を生成して md_to_json.py に渡す。

```python
import subprocess, sys, tempfile, os
from pathlib import Path

def make_list_3card_slide(title, n_items, sample_text):
    items = "\n".join(f"- {sample_text}" for _ in range(n_items))
    return f"""# {title}

| key | value |
|-----|-------|
| layout | list_3card |
| note | test |

```card-a
### カードA
{items}
```
```card-b
### カードB
{items}
```
```card-c
### カードC
{items}
```

---
"""

# 全スライド分の MD を結合して一時ファイルに書き出し
# md_to_json.py を subprocess で呼び出して PPTX 生成
```

### step_head ラベルテストの追加生成

`flow_3step` / `flow_4step` に対して、カード本文テストとは別にラベル長テストを生成する。
ラベルは `step-a/b/c/d` ブロックの `### ...` 行に記載する。

```python
STEP_LABEL_SAMPLES = {
    "cjk_short":  "ステップA",                  # 短い（5字）
    "cjk_medium": "ステップ実行フェーズA",        # 中（11字）
    "cjk_long":   "あいうえおかきくけこさしすせそ", # 長（15字・折り返し確認）
    "ascii_short": "Step A",
    "ascii_medium": "Execute Phase A",
    "ascii_long":  "the quick brown fox step",    # 折り返し確認
}
```

スライドタイトル: `"{layout} | step_head | {種別}"`

---

### スライドタイトル命名規則

- カード本文テスト: `"{layout} | N={n}行 | {種別}({文字数}字)"`
- step_head テスト: `"{layout} | step_head | {種別}"`

例:
- `"list_3card | N=7行 | cjk_long(40字)"`
- `"flow_3step | step_head | cjk_long"`

---

## ファイル配置

両スクリプトは以下の場所に配置:

```
.claude/skills/deck-from-source/
  overflow_analysis.py       ← 新規作成
  generate_test_slides.py    ← 新規作成
  overflow_analysis.csv      ← overflow_analysis.py が出力
  overflow_analysis.md       ← overflow_analysis.py が出力
  overflow_test.pptx         ← generate_test_slides.py が出力
```

スクリプトは同ディレクトリにある `design.json` と `templates.json` を相対パスで読む。
`generate_test_slides.py` は同ディレクトリの `md_to_json.py` を subprocess で呼ぶ。

---

## 実行手順

```bash
cd .claude/skills/deck-from-source

# Step 1: 計算による上限推定
python overflow_analysis.py
# → コンソールにテーブル表示
# → overflow_analysis.csv, overflow_analysis.md を出力

# Step 2: 視覚確認用 PPTX 生成
python generate_test_slides.py
# → overflow_test.pptx を出力
# → PowerPoint または LibreOffice で開いて目視確認
```

---

## 注意事項

- `overflow_analysis.py` は `fonttools` がなくても動作する（近似値モード）
- `generate_test_slides.py` は `python-pptx` が必要（to_pptx.py と同じ依存関係）
- Windows の場合: `meiryo.ttc` は `C:\Windows\Fonts\` にある
- `plain_2col` は `"engine": "area"` の通常グリッド（`plain` 型セル × 2）なので、
  `compute_cells()` で導出した値 (text_w=4.28", text_h=3.815") を使う。
  `render_plain2col()` はデッドコードのため参照してはならない。
- `flow_3step` / `flow_4step` の `step_head` セルは `text()` 関数で描画され、
  行間は `_set_line_spacing` を経由しない（デフォルト ≒ 1.2×）。
  セル高さは `rowHeightRatios` から `compute_cells()` で動的に計算すること。
- `simulate_fit_bullets()` は **bullet 専用**。heading / nested / ordered / blockquote を
  含むコンテンツには適用しない。出力 CSV/MD にこの旨を必ず注記すること。
