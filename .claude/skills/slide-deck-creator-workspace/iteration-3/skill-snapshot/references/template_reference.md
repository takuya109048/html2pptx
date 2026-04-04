# スライドテンプレート リファレンス

このシステムは `templates.json` → `to_pptx.py` → PPTX という変換パイプラインで動作する。
スキルの出力は `templates.json` と同じ形式の JSON ファイル。

---

## テンプレートカタログ（13種）

| キー | 日本語名 | 用途 | セル構成 |
|------|---------|------|---------|
| `cover` | 表紙 | プレゼン冒頭の表紙 | 特殊（cover レイアウト） |
| `plain_1col` | 1カラムテキスト | 詳細説明・本文・箇条書き | plain×1 |
| `plain_2col` | 2カラムテキスト | 目次+本文、比較、2テーマ並置 | plain×2 |
| `plain_image` | テキスト＋画像 | テキストと図表を左右に配置 | plain + image |
| `image_conclusion` | 画像＋結論 | グラフ・図表に結論コメント | image + conclusion |
| `list_3card` | 横並び3カード | 3項目の並列比較・特徴紹介 | card×3 |
| `flow_3step` | フロー（3ステップ） | 3段階のプロセス・手順 | step_head×3 + card×3 |
| `flow_4step` | フロー（4ステップ） | 4段階のプロセス・手順 | step_head×4 + card×4 |
| `bg_3card` | 背景ボックス＋3カード | 概要セクション + 詳細3項目 | section(span3) + card×3 |
| `diffuse_3card` | 拡散（背景→3カード） | 1テーマが3要素に展開（矢印付き） | section + arrow + card×3 |
| `converge_3card` | 収束（3カード→結論） | 3要素が1結論に集約（矢印付き） | card×3 + arrow + conclusion |
| `table` | テーブル | データ比較表・一覧 | table |
| `table_conclusion` | テーブル＋結論 | データ表 + まとめコメント | table + conclusion |

---

## デッキ JSON の全体構造

```json
{
  "スライドキー1": {
    "name": "スライド名（管理用）",
    "engine": "area",
    "SLIDES": [ { /* スライドデータ */ } ]
  },
  "スライドキー2": { ... }
}
```

- **キー**は一意な識別子（`slide_01`、`intro`、`summary` など任意）
- `to_pptx.py` はキーの並び順にスライドを生成する
- 各キーの `SLIDES` 配列には基本的に1要素だけ入れる

---

## スライドデータの構造

### 通常スライド（ほぼすべてのテンプレート）

```json
{
  "header": {
    "title": "スライドタイトル",
    "message": "サブタイトル・補足"
  },
  "rowHeightRatios": [1.0],
  "grid": [
    [ /* 1行目のセル配列 */ ],
    [ /* 2行目のセル配列（複数行の場合）*/ ]
  ],
  "page": "2 / 5",
  "logo": "logo.png"
}
```

- `rowHeightRatios`: 各行の高さの比率（合計は1.0）
  - 1行: `[1.0]`
  - 上段25%+下段75%: `[0.25, 0.75]`
  - ステップフロー: `[0.28, 0.72]`
  - テーブル+結論: `[0.75, 0.25]`
  - 拡散3カード: `[0.25, 0.08, 0.67]`（section + arrow + cards）
  - 収束3カード: `[0.65, 0.08, 0.27]`（cards + arrow + conclusion）
  - 画像+結論: `[0.77, 0.23]`

### 表紙スライド（cover のみ）

```json
{
  "layout": "cover",
  "title": "プレゼンテーションタイトル",
  "affiliation": "所属・部署名",
  "presenter": "発表者名",
  "date": "2026-04-03",
  "bg": "background.png"
}
```

---

## セルタイプ リファレンス

### `plain` — マークダウンテキストエリア
自由なテキスト。見出し・箇条書き・番号リスト・引用・コード等が使える。

```json
{ "type": "plain", "markdown": "## 見出し\n\nテキスト。**太字**、*斜体*。\n\n- 箇条書き\n  - ネスト\n\n1. 番号リスト" }
```

マークダウン記法:
- `**太字**`、`*斜体*`、`~~取り消し線~~`、`` `コード` ``
- `> 引用ブロック`
- `- 箇条書き`（ネストは `  -` 2スペースインデント）
- `1. 番号リスト`（ネストは `   1.` 3スペースインデント）
- `## 見出し`（H1〜H3、サイズは本文と同じ）

### `card` — タイトル付きカード
見出し(## で始まる1行)と箇条書き本文で構成。カード背景色あり。

```json
{ "type": "card", "markdown": "## カードタイトル\n\n- **項目1** 説明\n- *項目2* 説明（`コード`）\n- ~~旧情報~~ → 新情報" }
```

- `## タイトル` は必須ではないが、あると見出し+区切り線が描画される
- 見出しなしの場合は箇条書きのみのカードになる

### `section` — 背景ボックス（背景色付きテキスト）
セクション見出しや概要テキスト用。通常 `"span": 3` でグリッド幅全体に張る。

```json
{ "type": "section", "span": 3, "markdown": "**要点**。*補足*、`キーワード`。\n> 引用・根拠を添える。" }
```

- テキストは2〜3行程度に収める
- `span` で複数カラムにまたがる幅を指定（3カラムレイアウトなら `span: 3`）

### `conclusion` — 結論ボックス
左辺にアクセントライン付きの強調ボックス。

```json
{ "type": "conclusion", "span": 3, "markdown": "**結論テキスト**。*補足*、~~旧情報~~ → 更新。`参照ID`。\n> 根拠・引用。" }
```

- テキストは1〜2行程度に収める
- `span` で幅を指定

### `image` — 画像プレースホルダー
画像ファイルを表示、または空のプレースホルダーとして描画。

```json
{ "type": "image", "label": "グラフ / Chart", "src": "chart.png" }
```

- `src` を省略するとラベル入りの空枠が表示される
- `gridN`: `plain_image` テンプレートで画像の横幅比率を調整（デフォルト3）

### `table` — データテーブル
ヘッダー行 + データ行で構成。

```json
{
  "type": "table",
  "head": ["項目", "2023年", "2024年", "増減"],
  "rows": [
    ["売上", "100M", "120M", "+20%"],
    ["コスト", "80M", "90M", "+12.5%"],
    ["利益", "20M", "30M", "+50%"]
  ]
}
```

- 1行目は太字のヘッダーとして描画
- 各行の先頭セルも太字
- 列数は head と rows で揃える

### `arrow` — 矢印（▼）
拡散・収束レイアウトの中間に挟む下向き三角矢印。`span` 必須。

```json
{ "type": "arrow", "span": 3 }
```

### `step_head` — ステップヘッダー（矢印型）
フローテンプレートで工程名を表示する矢印型ヘッダー。

```json
{ "type": "step_head", "label": "ステップ1 / 調査" }
```

---

## テンプレート別 grid 構造パターン

### `plain_1col`
```json
"rowHeightRatios": [1.0],
"grid": [[ { "type": "plain", "markdown": "..." } ]]
```

### `plain_2col`
```json
"rowHeightRatios": [1.0],
"grid": [[ { "type": "plain", "markdown": "左カラム" }, { "type": "plain", "markdown": "右カラム" } ]]
```

### `plain_image`
```json
"rowHeightRatios": [1.0],
"grid": [[ { "type": "plain", "markdown": "..." }, { "type": "image", "label": "図1", "gridN": 3 } ]]
```

### `image_conclusion`
```json
"rowHeightRatios": [0.77, 0.23],
"grid": [
  [ { "type": "image", "label": "グラフ" } ],
  [ { "type": "conclusion", "markdown": "**結論**。補足。" } ]
]
```

### `list_3card`
```json
"rowHeightRatios": [1.0],
"grid": [[
  { "type": "card", "markdown": "## タイトル1\n\n- 項目1\n- 項目2" },
  { "type": "card", "markdown": "## タイトル2\n\n- 項目1\n- 項目2" },
  { "type": "card", "markdown": "## タイトル3\n\n- 項目1\n- 項目2" }
]]
```

### `flow_3step`
```json
"rowHeightRatios": [0.28, 0.72],
"grid": [
  [ { "type": "step_head", "label": "Step 1" }, { "type": "step_head", "label": "Step 2" }, { "type": "step_head", "label": "Step 3" } ],
  [ { "type": "card", "markdown": "- 説明1\n- 説明2" }, { "type": "card", "markdown": "- 説明1" }, { "type": "card", "markdown": "- 説明1" } ]
]
```

### `flow_4step` — flow_3step と同じ構造でカラム数が4

### `bg_3card`
```json
"rowHeightRatios": [0.25, 0.75],
"grid": [
  [ { "type": "section", "span": 3, "markdown": "概要テキスト" } ],
  [ { "type": "card", "markdown": "## A\n\n- ..." }, { "type": "card", "markdown": "## B\n\n- ..." }, { "type": "card", "markdown": "## C\n\n- ..." } ]
]
```

### `diffuse_3card`
```json
"rowHeightRatios": [0.25, 0.08, 0.67],
"grid": [
  [ { "type": "section", "span": 3, "markdown": "テーマ概要" } ],
  [ { "type": "arrow", "span": 3 } ],
  [ { "type": "card", "markdown": "## A" }, { "type": "card", "markdown": "## B" }, { "type": "card", "markdown": "## C" } ]
]
```

### `converge_3card`
```json
"rowHeightRatios": [0.65, 0.08, 0.27],
"grid": [
  [ { "type": "card", "markdown": "## A" }, { "type": "card", "markdown": "## B" }, { "type": "card", "markdown": "## C" } ],
  [ { "type": "arrow", "span": 3 } ],
  [ { "type": "conclusion", "span": 3, "markdown": "**結論テキスト**。補足。" } ]
]
```

### `table`
```json
"rowHeightRatios": [1.0],
"grid": [[ { "type": "table", "head": ["列1","列2","列3"], "rows": [["A","B","C"],["D","E","F"]] } ]]
```

### `table_conclusion`
```json
"rowHeightRatios": [0.75, 0.25],
"grid": [
  [ { "type": "table", "head": ["列1","列2"], "rows": [["A","B"]] } ],
  [ { "type": "conclusion", "markdown": "**まとめ**。補足。" } ]
]
```
