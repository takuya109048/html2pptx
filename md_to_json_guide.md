# md_to_json.py ドキュメント

## 概要

`md_to_json.py` は、Markdown で書かれたスライド定義を JSON スライド配列へ変換し、必要に応じて `to_pptx.py` を呼び出して PPTX まで一括生成するスクリプトです。

関連ファイル:

- `md_to_json.py`: MD をスライド JSON に変換する本体
- `to_pptx.py`: JSON/テンプレートから PPTX を生成するスクリプト
- `templates.json`: レイアウト定義（セル構成・型）
- `design.json`: デザイン設定（色・フォント等）
- `logo.png`: 各スライドに挿入されるロゴ画像
- `background.png`: cover レイアウトの背景画像

## MDフォーマット仕様

### スライドの基本構造

1 スライドは以下の順で記述します。

1. `# タイトル`（必須推奨）
2. `## メッセージ`（任意）
3. メタデータテーブル（`layout` 必須）
4. コンテンツセクション（` ```card-a ` など）

例:

````md
# スライドタイトル
## サブメッセージ

| key | value |
|-----|-------|
| layout | list_3card |

```card-a
...
```
````

### スライド区切り

スライドは、行全体が `---` の区切り線で分割されます。

```md
# Slide 1
...
---
# Slide 2
...
```

### メタデータテーブルの書き方

ヘッダー付きの Markdown テーブルで記述します。

```md
| key | value |
|-----|-------|
| layout | flow_3step |
| note | ここに発表者原稿（ノート）を記述します。PPTXのノートに出力されます。 |
```

- 先頭列がキー、2列目以降が値として扱われます
- `layout` が未指定のブロックはスキップされます
- ページ番号は PPTX のスライド番号フィールドで自動表示されます（`page` キーは不要）
- **`note` を指定すると PPTX の発表者ノートに出力されます（任意）**

### タグ一覧と対応するセル型

- `card-a` / `card-b` / `card-c` / `card-d`: `card` または `plain` セルに順番で割り当て
- `step-a` / `step-b` / `step-c` / `step-d`: `flow_3step` / `flow_4step` のステップ見出し・カードに割り当て
- `section`: `section` セルに割り当て
- `conclusion`: `conclusion` セルに割り当て
- `table`: `table` セルに割り当て（セクション内に Markdown テーブル必須）
- `matrix`: `matrix` セルに割り当て。**1行目が列ラベル行（head）、2行目以降がデータ行**。各データ行の先頭セルが行ラベル（左列）。左上角セルは空欄 `| |` とする。

### imageセルのフィールド

`plain_image_row` / `plain_image_col` レイアウトでは、メタデータテーブルに以下のキーを指定できます。

| key | 説明 |
|-----|------|
| `image_1` | 画像ファイルパス（例: `photo.png`）。省略するとプレースホルダーを表示。 |
| `image_label_1` | 画像プレースホルダーのテキスト（画像未指定時に表示）。Markdown対応。 |

画像が複数ある場合は `image_2` / `image_label_2` と連番で指定します。

例:
```md
| key | value |
|-----|-------|
| layout | plain_image_row |
| image_1 | photos/chart.png |
| image_label_1 | **売上推移グラフ** を挿入 |
```

### coverスライドの特殊フィールド

`layout: cover` のときは、以下をメタデータから直接使用します。

- `title`
- `affiliation`
- `date`
- `note`（任意：発表者ノート）

## レイアウト一覧

| layout | 使用タグ |
|---|---|
| cover | なし（メタデータのみ） |
| table_conclusion | `table`, `conclusion` |
| table | `table` |
| list_3card | `card-a`, `card-b`, `card-c` |
| plain_1col | `card-a` |
| plain_2col | `card-a`, `card-b` |
| flow_3step | `step-a`, `step-b`, `step-c` |
| flow_4step | `step-a`, `step-b`, `step-c`, `step-d` |
| diffuse_3card | `section`, `card-a`, `card-b`, `card-c` |
| converge_3card | `card-a`, `card-b`, `card-c`, `conclusion` |
| plain_image_row | `card-a`, `card-b` |
| plain_image_col | `card-a` |
| matrix_3x3 | `matrix` |
| bg_3card | `section`, `card-a`, `card-b`, `card-c` |

## 使い方（CLIリファレンス）

### 基本的な使い方

```bash
python md_to_json.py <input_md> [output_pptx]
```

### オプション

- `output_pptx`（位置引数・任意）: 出力 PPTX パス。省略時は `<input_md と同名>.pptx`
- `--json <path>`: 中間/出力 JSON の保存先パス
- `--templates <path>`: 使用する `templates.json` のパス（省略時はスクリプトと同階層の `templates.json`）
- `--no-pptx`: PPTX 生成を行わず JSON のみ出力

### 使用例

```bash
# 1) MD -> JSON -> PPTX（出力PPTX名は自動）
python md_to_json.py sample_deck.md

# 2) 出力PPTXを明示
python md_to_json.py sample_deck.md output/result.pptx

# 3) JSON出力先を指定しつつPPTXも生成
python md_to_json.py sample_deck.md output/result.pptx --json output/result.json

# 4) JSONのみ生成
python md_to_json.py sample_deck.md --no-pptx

# 5) テンプレートファイルを差し替え
python md_to_json.py sample_deck.md --templates custom_templates.json
```

## サンプルMDの例

### cover

```md
# 業務改革プロジェクト サンプルデッキ

| key | value |
|-----|-------|
| layout | cover |
| affiliation | 経営企画部 |
| date | 2026-04-08 |
| note | 本日はお時間をいただきありがとうございます。このデッキでは業務改革プロジェクトの全体像をご説明します。 |
```

### list_3card

````md
# 重点アクション
## 並行実行する3テーマ

| key | value |
|-----|-------|
| layout | list_3card |
| note | 3つの施策は並行して進めますが、優先度は可視化→標準化→自動化の順です。 |

```card-a
### 可視化
- 経営指標を一元表示
```

```card-b
### 標準化
- 業務手順をテンプレート化
```

```card-c
### 自動化
- 手作業集計をバッチ化
```
````

### flow_3step

````md
# 3ステップ実行計画
## 段階的に展開

| key | value |
|-----|-------|
| layout | flow_3step |

```step-a
- 対象業務を選定
```

```step-b
- ダッシュボードを構築
```

```step-c
- 週次レビューを運用化
```
````

### table_conclusion

````md
# 現状分析の要点
## 指標比較と結論

| key | value |
|-----|-------|
| layout | table_conclusion |

```table
| 指標 | 現状 | 目標 | 補足 |
| --- | ---: | ---: | --- |
| 月次報告作成時間 | 16時間 | 6時間 | 自動集計導入 |
| 誤入力件数 | 22件 | 7件 | 入力ルール統一 |
```

```conclusion
- 最優先はデータ入力工程の標準化
- 並行してダッシュボード統合を進める
```
````

### matrix_3x3

1行目が列ラベル（先頭セルは空欄）、2行目以降の先頭セルが行ラベル。

````md
# 施策×軸マトリックス
## 3軸×3施策の整理

| key | value |
|-----|-------|
| layout | matrix_3x3 |

```matrix
| | コスト軸 | スピード軸 | 品質軸 |
| --- | --- | --- | --- |
| 施策A | 低コスト | 高速 | 標準 |
| 施策B | 中コスト | 標準 | 高品質 |
| 施策C | 高コスト | 低速 | 最高品質 |
```
````
