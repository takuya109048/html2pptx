# TEMPLATE_WORKFLOW.md — テンプレート選択決定木

各スライドに以下の決定木を**上から順番に**適用する。最初に一致した条件でテンプレートを決定し、それ以降のルールは確認しない。どれにも当てはまらない場合のみ `plain_1col` / `plain_2col` を使う。**強引な当てはめは行わない。**

---

## テンプレート選択決定木

```
1. タイトル/表紙スライドか？
   → cover

2. 時系列・歴史・フェーズ変遷など「流れ」があり3段階か？
   → flow_3step

3. 時系列・歴史・フェーズ変遷など「流れ」があり4段階か？
   → flow_4step

4. 並列する3つの要素・特徴・メリット・施策がフラットに並ぶか？
   → list_3card

5. 1つの共通テーマ・課題から3つのアプローチ・方向性に展開するか？
   → diffuse_3card

6. 3つの根拠・証拠・理由が1つの結論に収束するか？
   → converge_3card

7. 背景・文脈の説明＋3つのポイントという構成か？
   → bg_3card

8. 表形式のデータがあり、かつ1つの重要な結論・示唆があるか？
   → table_conclusion

9. 表形式のデータのみで結論は別スライドに分けるか？
   → table

10. 2つのものを3つの観点で対比・比較するか？
    → compare_2col_3row

11. マトリックス形式のデータか？
    - 3×3グリッドで縦方向にフロー → flow_matrix_3x3
    - 3×3グリッドで横方向にフロー → h_flow_matrix_3x3
    - 3×2グリッドで横方向にフロー → h_flow_matrix_3x2
    - 4×2グリッドで横方向にフロー → h_flow_matrix_4x2
    - 単純な3×3表 → matrix_3x3

12. 2つの対立・比較・対照する概念を並べて説明するか？
    → plain_2col

13. それ以外（単一コンセプトの説明・ナレーション・段落テキスト）
    → plain_1col
```

---

## nanobanana2使用時の置換ルール

Step 1でnanobanana2使用が確認された場合、手順 12・13 で `plain_1col` / `plain_2col` に決定したスライドを以下の基準で置換する。

| 元テンプレ | コンテンツ特性 | 置換先 | 画像比率 |
|-----------|------------|--------|---------|
| `plain_1col` | テキスト量が少ない + 広い概念図・インフォグラフィックが合う | `plain_image_row` | 16:5（横長ワイド） |
| `plain_1col` | テキスト量が中程度 + 正方形〜縦長のイラストが合う | `plain_image_col` | 6:5（ほぼ正方形） |
| `plain_2col` | 片方のカラムを図解に置き換えた方が伝わりやすい | `plain_image_col` | 6:5（ほぼ正方形） |

**置換しない条件（そのまま `plain_1col` / `plain_2col` を維持する）:**
- テキスト量が多く、画像を置くスペースが確保できない
- 図解が不自然・コンテンツに合わない
- 純粋なテキスト説明スライドとして機能する方が適切

---

## テンプレート早見表

| テンプレート | 用途 | 主要セクションタグ |
|-------------|------|----------------|
| `cover` | 表紙 | （なし） |
| `plain_1col` | 単一コンセプト説明 | `card-a` |
| `plain_2col` | 2つの概念を並べる | `card-a`, `card-b` |
| `list_3card` | 並列3要素 | `card-a`, `card-b`, `card-c` |
| `flow_3step` | 3ステップフロー | `step-a`, `step-b`, `step-c` |
| `flow_4step` | 4ステップフロー | `step-a`, `step-b`, `step-c`, `step-d` |
| `diffuse_3card` | 1→3展開 | `section`, `card-a`, `card-b`, `card-c` |
| `converge_3card` | 3→1収束 | `card-a`, `card-b`, `card-c`, `conclusion` |
| `bg_3card` | 背景+3ポイント | `section`, `card-a`, `card-b`, `card-c` |
| `table` | データ表 | `table` |
| `table_conclusion` | データ表+結論 | `table`, `conclusion` |
| `compare_2col_3row` | 2×3対比 | `matrix`（2列×3行） |
| `matrix_3x3` | 3×3マトリックス | `matrix` |
| `flow_matrix_3x3` | 縦フロー3×3 | `flow_matrix` |
| `h_flow_matrix_3x2` | 横フロー3×2 | `h_flow_matrix` |
| `h_flow_matrix_3x3` | 横フロー3×3 | `h_flow_matrix` |
| `h_flow_matrix_4x2` | 横フロー4×2 | `h_flow_matrix` |
| `plain_image_row` | テキスト+横長画像 | `card-a` + `image_label_1` |
| `plain_image_col` | テキスト+縦目画像 | `card-a` + `image_label_1` |
