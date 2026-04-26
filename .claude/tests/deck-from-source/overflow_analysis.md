# Overflow Analysis — deck-from-source

> **スコープ**: 単一レベル箇条書き（bullet）のみ。
> heading / nested bullet / ordered / blockquote を含む場合は適用外。
> geometry ベースの近似値（fonttools なし）。

| layout | cell_type | w(in) | h(in) | font | max_vis | CJK/vln | ASCII/vln | Mix/vln | @15CJK | @40CJK | @25ASCII | @35ASCII |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| list_3card | card | 2.86 | 3.415 | 11 | 10 | 17 | 31 | 22 | 10 | 3 | 10 | 5 |
| plain_1col | plain | 9.14 | 3.815 | 12 | 10 | 53 | 96 | 68 | 10 | 10 | 10 | 10 |
| plain_2col | plain | 4.28 | 3.815 | 12 | 10 | 24 | 43 | 31 | 10 | 5 | 10 | 10 |
| flow_3step | step_head | 2.686 | 1.049 | 14 | 4 | 13 | 25 | 17 | 2 | 1 | 4 | 2 |
| flow_3step | card | 2.86 | 2.286 | 11 | 6 | 17 | 31 | 22 | 6 | 2 | 6 | 3 |
| flow_4step | step_head | 1.998 | 1.049 | 14 | 4 | 10 | 18 | 13 | 2 | 1 | 2 | 2 |
| flow_4step | card | 2.05 | 2.286 | 11 | 6 | 11 | 21 | 15 | 3 | 1 | 3 | 3 |
| diffuse_3card | section | 9.34 | 0.684 | 12 | 1 | 54 | 99 | 70 | 1 | 1 | 1 | 1 |
| diffuse_3card | card | 2.86 | 2.077 | 11 | 6 | 17 | 31 | 22 | 6 | 2 | 6 | 3 |

## 凡例
- `@15CJK`: 15字全角項目を何個収容できるか（= max_vis ÷ ceil(15/CJK_per_vline)）
- `@40CJK`: 40字全角項目（折り返し発生）を何個収容できるか
- `@25ASCII`: 25字半角項目を何個収容できるか
- `@35ASCII`: 35字半角項目（折り返し発生想定）を何個収容できるか
- `CJK/vln`: 1視覚行の全角文字数（文字単位折り返し）
- `ASCII/vln`: 1視覚行の半角文字数（単語境界折り返し: 近似値）
- `Mix/vln`: 1視覚行の混在文字数（全角50%/半角50% 近似）

## 注記
- `step_head` は `text()` 関数で描画、行間 ≈ 1.2×（PowerPoint デフォルト）
- `step_head` の @items 列はラベル折り返し視覚行数の参考値
- `plain_2col` は `engine: area` + `compute_cells()` 由来（`render_plain2col()` 参照なし）
- card セルはタイトルあり前提（タイトルなしは本文高さが増える）