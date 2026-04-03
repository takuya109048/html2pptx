---
name: slide-deck-creator
description: >
  スライドデッキの JSON を生成するスキル。ユーザーがプレゼン資料の内容・構成を伝えると、
  このプロジェクトの templates.json フォーマットに準拠した完全な JSON を出力する。
  to_pptx.py で直接 PPTX に変換できる形式。
  「スライドを作って」「プレゼン資料の JSON が欲しい」「デッキを生成して」「〇〇についてのプレゼンを作りたい」
  「テンプレートに合わせてスライドの JSON を組み立てて」といったリクエストで必ず使うこと。
  ユーザーがスライドの内容・アウトライン・テーマのどれか一つでも伝えた段階でこのスキルを発動する。
---

# スライドデッキ JSON 生成スキル

このスキルはユーザーのプレゼン内容をヒアリングし、`templates.json` フォーマット準拠の
デッキ JSON を生成する。出力した JSON は `to_pptx.py` に渡せばすぐ PPTX になる。

テンプレートの詳細は `references/template_reference.md` を参照すること。

---

## ステップ 1: ヒアリング

まずユーザーから以下を確認する。すでに情報があれば飛ばしてよい。

1. **テーマ・目的**: 何についてのプレゼンか（例: 新製品の提案、Q4 レビュー、技術説明）
2. **スライド枚数の目安**: 何枚くらいか（「5〜7枚」「表紙を含めて6枚」など）
3. **主要コンテンツ**: 各スライドで言いたいこと（箇条書きでもOK）
4. **発表者・所属・日付**: 表紙に必要な情報（省略可）

ユーザーが「とにかく作って」と言った場合はテーマだけ聞いてデモ内容で生成してしまってよい。

---

## ステップ 2: スライド構成の提案

ヒアリング内容をもとに、各スライドにどのテンプレートを使うか提案する。

### テンプレート選択の指針

| ユーザーの意図 | 推奨テンプレート |
|--------------|--------------|
| 冒頭・表紙 | `cover` |
| 長い文章・説明・手順の詳細 | `plain_1col` |
| 目次 + 本文、または2テーマ比較 | `plain_2col`（左:目次、右:本文） |
| 図・グラフ + テキスト説明 | `plain_image` |
| 図・グラフ + 結論コメント | `image_conclusion` |
| 3つの選択肢・特徴・サービスを並べる | `list_3card` |
| 3段階のプロセス・フロー | `flow_3step` |
| 4段階のプロセス・フロー | `flow_4step` |
| 概要セクション + 3つの詳細 | `bg_3card` |
| 1つのテーマから3要素に展開 | `diffuse_3card` |
| 3つの根拠から1つの結論を導く | `converge_3card` |
| データ比較表のみ | `table` |
| データ表 + まとめ | `table_conclusion` |

提案は簡潔に。例:
```
1. 表紙 (cover) — タイトル・発表者
2. 課題の背景 (plain_1col) — 現状の問題点を説明
3. 3つの解決策 (list_3card) — 各選択肢の比較
4. 推奨案の詳細 (bg_3card) — 概要→3つの施策
5. スケジュール (flow_4step) — 4フェーズの実行計画
6. まとめ (converge_3card) — 3つの根拠→結論
```

---

## ステップ 3: JSON 生成

承認が得られたら（または自明なら確認なしで）JSON を生成する。

### 生成ルール

**ファイル全体構造**:
```json
{
  "slide_01": { "name": "スライド名", "engine": "area", "SLIDES": [{ ... }] },
  "slide_02": { ... }
}
```

- キーは `slide_01`, `slide_02` … と連番、または内容を表す短いキー（`cover`, `intro`, `summary`）
- `engine` は常に `"area"`
- `SLIDES` は1要素の配列

**ページ番号**:
- `"page": "1 / N"` の形式で各スライドに付ける（N = 総枚数、表紙は含めない慣例でもよい）

**logo と bg**:
- logo は `"logo": "logo.png"` 固定
- 表紙の bg は `"bg": "background.png"` 固定（ユーザーが別ファイル名を指定した場合は従う）

**markdown の書き方**:
- JSON の `\n` は改行、`\n\n` は段落区切り
- 太字: `**テキスト**`、斜体: `*テキスト*`
- section・conclusion はコンパクトに（2〜3行が理想）
- card の本文は箇条書き3〜4項目が読みやすい
- plain は自由にリッチなマークダウンを使える

**span の扱い**:
- `section`・`conclusion`・`arrow` は `"span": 列数` を付ける（3カラムレイアウトなら 3）

---

## ステップ 4: 出力

完成した JSON を コードブロック（` ```json `) で出力する。

その後、使い方を案内する:
```
生成した JSON を templates.json として保存し、以下で PPTX に変換できます:
  python to_pptx.py          # 全スライドを生成
  python to_pptx.py slide_01 # 特定スライドのみ
```

---

## 参考: テンプレート構造早見表

詳細は `references/template_reference.md` を参照。主要パターンの要点:

- `cover`: `layout: "cover"` + `title/affiliation/presenter/date/bg`（header/grid 不要）
- `plain_1col`: `rowHeightRatios: [1.0]` + `grid: [[plain]]`
- `plain_2col`: `rowHeightRatios: [1.0]` + `grid: [[plain, plain]]`
- `list_3card`: `rowHeightRatios: [1.0]` + `grid: [[card, card, card]]`
- `flow_3step`: `rowHeightRatios: [0.28, 0.72]` + `grid: [[step_head×3], [card×3]]`
- `flow_4step`: 同上で4列
- `bg_3card`: `rowHeightRatios: [0.25, 0.75]` + `grid: [[section(span3)], [card×3]]`
- `diffuse_3card`: `rowHeightRatios: [0.25, 0.08, 0.67]` + `grid: [[section], [arrow], [card×3]]`
- `converge_3card`: `rowHeightRatios: [0.65, 0.08, 0.27]` + `grid: [[card×3], [arrow], [conclusion]]`
- `image_conclusion`: `rowHeightRatios: [0.77, 0.23]` + `grid: [[image], [conclusion]]`
- `plain_image`: `rowHeightRatios: [1.0]` + `grid: [[plain, image]]`
- `table`: `rowHeightRatios: [1.0]` + `grid: [[table]]`
- `table_conclusion`: `rowHeightRatios: [0.75, 0.25]` + `grid: [[table], [conclusion]]`
