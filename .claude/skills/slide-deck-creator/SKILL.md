---
name: slide-deck-creator
description: >
  スライドデッキの JSON を生成し PPTX に変換するスキル。
  ユーザーがプレゼン資料の内容・構成を伝える、または原文（レポート・議事録・報告書など）を提示すると、
  このプロジェクトの templates.json フォーマットに準拠した JSON を生成し、to_pptx.py で PPTX に変換する。
  以下のいずれかで発動すること：
  - 「スライドを作って」「プレゼン資料の JSON が欲しい」「デッキを生成して」「〇〇についてのプレゼンを作りたい」
  - 「このレポートをスライドにして」「原文をもとにスライドを作って」「この文章をプレゼンに変換して」
  - 文章・レポート・議事録・報告書などを貼り付けてスライド化を依頼された場合
  ユーザーがスライドの内容・アウトライン・テーマ・原文のどれか一つでも提示した段階でこのスキルを発動する。
---

# スライドデッキ JSON 生成 → PPTX 変換スキル

このスキルはユーザーの入力（ヒアリングまたは原文）をもとにスライド構成を設計し、
`templates.json` フォーマット準拠の JSON を生成して `to_pptx.py` で PPTX に変換する。

テンプレートの詳細は `references/template_reference.md` を参照すること。

---

## ステップ 1: 入力の把握

入力には2パターンある。それぞれ異なるアプローチで進める。

### パターン A — 原文あり（レポート・議事録・報告書など）

ユーザーが文章・テキストを提示した場合:

1. **原文を読み込んで構造を把握する**
   - 全体のテーマ・目的・結論を特定する
   - 主要なセクション・論点・データ・数値を抽出する
   - 情報の論理構造（問題→原因→対策、現状→将来など）を把握する

2. **スライド化に適した情報を選別する**
   - 細かすぎる説明・注釈・参考資料は省略
   - キーメッセージ・数値・比較・フローに変換できる情報を優先
   - 原文にある箇条書き・小見出し・表はそのまま活用できる候補

3. **スライド枚数の目安を決める**
   - 原文の分量・情報密度から 5〜8 枚を基本とする
   - セクションが多い場合は 8〜12 枚も可
   - ユーザーが枚数を指定した場合はそれに従う

### パターン B — 原文なし（ヒアリングで進める）

原文がない場合は以下を確認する。すでに情報があれば飛ばしてよい。

1. **テーマ・目的**: 何についてのプレゼンか
2. **スライド枚数の目安**: 何枚くらいか
3. **主要コンテンツ**: 各スライドで言いたいこと（箇条書きでもOK）
4. **発表者・所属・日付**: 表紙に必要な情報（省略可）

ユーザーが「とにかく作って」と言った場合はテーマだけ聞いてデモ内容で生成してしまってよい。

---

## ステップ 2: スライド構成の提案

ステップ1の情報をもとに、各スライドにどのテンプレートを使うか提案する。

### テンプレート選択の指針

| ユーザーの意図 / 原文の構造 | 推奨テンプレート |
|--------------------------|--------------|
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

### 原文からの変換パターン

| 原文の構造 | 変換先 |
|-----------|--------|
| 表・数値データがある | `table` or `table_conclusion` |
| 「〜の3つの理由/要因」 | `list_3card` or `converge_3card` |
| 「Step1〜Step3/フェーズ1〜」 | `flow_3step` or `flow_4step` |
| 「背景〜課題〜対策」の論理展開 | `plain_1col` → `list_3card` |
| 結論・まとめが明示されている | `converge_3card` or `table_conclusion` |
| 箇条書き3項目 + 概要説明 | `bg_3card` |

提案は簡潔に。例:
```
1. 表紙 (cover) — タイトル・発表者
2. 課題の背景 (plain_1col) — 現状の問題点を説明
3. 3つの解決策 (list_3card) — 各選択肢の比較
4. 推奨案の詳細 (bg_3card) — 概要→3つの施策
5. スケジュール (flow_4step) — 4フェーズの実行計画
6. まとめ (converge_3card) — 3つの根拠→結論
```

承認が得られたら（または自明なら確認なしで）次へ進む。

---

## ステップ 3: JSON 生成

### 生成ルール

**ファイル全体構造**:
```json
{
  "slide_01": { "name": "スライド名", "engine": "area", "SLIDES": [{ ... }] },
  "slide_02": { ... }
}
```

- キーは `slide_01`, `slide_02` … と連番
- `engine` は常に `"area"`
- `SLIDES` は1要素の配列
- **枚数厳守**: ユーザーまたはステップ2で決めた枚数と必ず一致させる

**ページ番号**:
- `"page": "1 / N"` の形式で各スライドに付ける（表紙は除く）
- N = 表紙を除いたコンテンツスライドの総数

**logo と bg**:
- logo は `"logo": "logo.png"` 固定
- 表紙の bg は `"bg": "background.png"` 固定

**markdown の書き方**:
- JSON の `\n` は改行、`\n\n` は段落区切り
- 太字: `**テキスト**`、斜体: `*テキスト*`
- section・conclusion はコンパクトに（2〜3行が理想）
- card の本文は箇条書き3〜4項目が読みやすい
- plain は自由にリッチなマークダウンを使える
- **原文の数値・固有名詞・専門用語はそのまま使う（改変しない）**

**span の扱い**:
- `section`・`conclusion`・`arrow` は `"span": 列数` を付ける（3カラムレイアウトなら 3）

---

## ステップ 4: templates.json を更新して PPTX に変換

生成した JSON を `templates.json` に保存し、`to_pptx.py` を実行して PPTX を生成する。

```bash
# 既存の templates.json をバックアップして置き換え（または追記）
# その後 PPTX 生成
python to_pptx.py
```

**実行手順**:
1. 生成した JSON をこのスキルフォルダ内の `templates.json` に書き込む（既存内容を置き換え）
2. `to_pptx.py` を実行して `output.pptx` を生成する
3. 生成されたファイルをユーザーに案内する

```bash
SKILL=".claude/skills/slide-deck-creator"
python "$SKILL/to_pptx.py"
```

```
✅ output.pptx を生成しました（スキルフォルダ内）
スライド枚数: N枚
```

**特定スライドのみ生成したい場合**:
```bash
python "$SKILL/to_pptx.py" slide_01
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
