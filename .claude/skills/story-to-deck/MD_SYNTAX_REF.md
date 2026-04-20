# MD_SYNTAX_REF.md — MD記法クイックリファレンス

`md_to_json.py` が解釈するMarkdown記法のクイックリファレンス。詳細は `md_to_json_guide.md`（プロジェクトルート）を参照。

---

## 基本構造

```markdown
# スライドタイトル
## サブタイトル（メッセージ）

| key | value |
|-----|-------|
| layout | <レイアウト名> |
| note | 発表者ノート（原文から抽出した補足情報を入れる） |

\```card-a
### カード見出し
- 箇条書き1
- **強調テキスト**
- *斜体テキスト*
\```

---
```

- スライドは `---` で区切る
- `# タイトル` は必須（`## メッセージ` はオプション）
- フロントマターはMarkdownテーブル形式

---

## レイアウト別タグ早見表

| レイアウト | 使用するタグ |
|-----------|-----------|
| `cover` | タグなし（`# タイトル` + フロントマターのみ） |
| `plain_1col` | ` ```card-a ` |
| `plain_2col` | ` ```card-a `, ` ```card-b ` |
| `list_3card` | ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `flow_3step` | ` ```step-a `, ` ```step-b `, ` ```step-c ` |
| `flow_4step` | ` ```step-a `, ` ```step-b `, ` ```step-c `, ` ```step-d ` |
| `diffuse_3card` | ` ```section `, ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `converge_3card` | ` ```card-a `, ` ```card-b `, ` ```card-c `, ` ```conclusion ` |
| `bg_3card` | ` ```section `, ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `table` | ` ```table ` (Markdownテーブル必須) |
| `table_conclusion` | ` ```table `, ` ```conclusion ` |
| `plain_image_row` | ` ```card-a ` + `image_label_1` メタデータ |
| `plain_image_col` | ` ```card-a ` + `image_label_1` メタデータ |
| `compare_2col_3row` | ` ```matrix ` (Markdownテーブル形式) |
| `matrix_3x3` | ` ```matrix ` |
| `flow_matrix_3x3` | ` ```flow_matrix ` |
| `h_flow_matrix_*` | ` ```h_flow_matrix ` |

---

## フロントマターキー一覧

| キー | 必須 | 説明 |
|-----|------|------|
| `layout` | 必須 | テンプレート名 |
| `note` | 任意 | 発表者ノート（PPTX発表者ビューに表示） |
| `image_label_1` | 画像スライド | 画像プレースホルダーのラベル/nanobanana2プロンプト |
| `affiliation` | coverのみ | 組織・所属名 |
| `presenter` | coverのみ | 発表者名 |
| `date` | coverのみ | 発表日（YYYY-MM-DD） |

---

## インライン書式

| 記法 | 用途 |
|-----|------|
| `**テキスト**` | 太字・強調キーワード |
| `*テキスト*` | 斜体・補足・定義 |
| `` `テキスト` `` | 固有名詞・コード・コマンド名 |
| `~~テキスト~~` | 打ち消し・旧情報・比較元 |

---

## coverスライドのテンプレート

```markdown
# デッキタイトル

| key | value |
|-----|-------|
| layout | cover |
| affiliation | 組織名 |
| presenter | 発表者名 |
| date | YYYY-MM-DD |
| note | 発表の背景・目的を1〜2文で。 |

---
```

---

## tableスライドのテンプレート

```markdown
# テーブルタイトル
## サブメッセージ

| key | value |
|-----|-------|
| layout | table |
| note | 表の読み方・注目ポイントを記載。 |

\```table
| 列1 | 列2 | 列3 |
| --- | --- | --- |
| データ | データ | データ |
| データ | データ | データ |
\```

---
```

---

## 変換コマンド

```bash
python md_to_json.py deck_YYYYMMDD.md
```

このコマンドで `deck_YYYYMMDD.json` + `deck_YYYYMMDD.pptx` が生成される。
