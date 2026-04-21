---
name: story-to-deck
description: 原文ソース（テキスト/URL/ファイル）をGLOBIS手法で分析し、プレゼンテーションストーリーを設計した上でスライドデッキMDを生成するスキル。nanobanana2による画像生成プロンプトの付与にも対応する。
---

# Story-to-Deck: 原文からスライドデッキ生成スキル

原文テキストを受け取り、プレゼンテーション用のストーリーに変換し、テンプレートを選択して `deck_YYYYMMDD.md` を生成するスキル。

---

## トリガー条件

- 「原文/ソースからスライドを作って」と依頼されたとき
- URLやファイルを渡して「デッキにして」「プレゼン資料にして」と依頼されたとき
- 既存の `source-to-deck` より高度なストーリー設計を求められたとき

---

## 全体ワークフロー

```
Step 0: ソーステキスト受け取り
         └ テキスト直接入力 / URL → WebFetch / ファイルパス → Read
         ↓
Step 1: nanobanana2使用確認 [必須：解析前に実施]
         └ → NANOBANANA_RULES.md 参照
         ↓
Step 2: ストーリー分析
         └ → STORY_ANALYSIS.md 参照
         └ フレームワーク選択 → 骨子設計 → スライド構成案 → ユーザー確認
         ↓
Step 3: テンプレート割り当て
         └ → TEMPLATE_WORKFLOW.md 参照
         └ 各スライドに決定木を適用 → nanobanana2置換処理
         ↓
Step 4: MDコンテンツ生成
         └ → MD_SYNTAX_REF.md 参照（記法）
         └ → NANOBANANA_RULES.md 参照（プロンプト付与）
         ↓
Step 5: MDファイル保存
         └ ファイル名: deck_YYYYMMDD.md（例: deck_20260420.md）
         ↓
Step 6: ユーザーへ変換コマンド案内
         └ python setup_deck.py  （初回のみ）
         └ python /mnt/data/md_to_json.py deck_YYYYMMDD.md --assets-dir /mnt/data
```

---

## Step 0: ソーステキスト受け取り

ユーザーがソースをまだ提示していない場合、以下のいずれかを確認する:

1. **テキスト直接貼り付け**: チャットに貼り付けてもらう
2. **URL指定**: URLを教えてもらい `WebFetch` で取得する
3. **ファイルパス指定**: ファイルパスを教えてもらい `Read` で読み込む

ソースを受け取ったら、以下を確認・推定する（未指定なら推定値を伝えて進める）:
- 発表時間・スライド枚数の目安
- 発表者名・発表日（coverスライド用）
- 対象オーディエンス

---

## Step 1: nanobanana2使用確認

**解析を始める前に必ず** ユーザーに確認する:

> 「nanobanana2による生成画像の挿入プランにしますか？  
> （YesにするとPlainスライドに画像プレースホルダーとプロンプトが追加されます）」

- **Yes** → `NANOBANANA_RULES.md` のルールに従い、Step 3・Step 4で画像置換とプロンプト生成を実施する
- **No** → plain_1col / plain_2col をそのまま使用する

---

## Step 2: ストーリー分析

`STORY_ANALYSIS.md` の手順に従い:

1. プレゼンテーション文脈を把握する
2. 目的に合ったフレームワークを選択する（SDS/PREP/DESC/序論→本論→結論/AIDMA）
3. メインメッセージを1文で定義し、骨子を設計する
4. スライド構成案（各スライドのタイトル・レイアウト候補）を箇条書きで提示する
5. **ユーザーに骨子を確認してもらう** → 承認後にStep 3へ

---

## Step 3: テンプレート割り当て

`TEMPLATE_WORKFLOW.md` の決定木を各スライドに適用する。

- 強引な当てはめは行わない
- どの特殊テンプレートにも該当しない場合は `plain_1col` または `plain_2col` を選択
- nanobanana2 Yes の場合は `TEMPLATE_WORKFLOW.md` の置換ルールを適用する

---

## Step 4: MDコンテンツ生成

`MD_SYNTAX_REF.md` の記法に従い各スライドのMarkdownを生成する。

- nanobanana2 Yes の場合: `NANOBANANA_RULES.md` に従い `image_label_1` と `note` にプロンプトを追記する

---

## Step 5 & 6: 出力

生成したMDを `deck_YYYYMMDD.md` として保存し、ユーザーに以下を案内する:

```bash
# 1. セットアップ（初回のみ）— スキルフォルダのファイルを /mnt/data にコピー
python setup_deck.py

# 2. JSON変換 → PPTX生成
python /mnt/data/md_to_json.py deck_YYYYMMDD.md --assets-dir /mnt/data
```

`setup_deck.py` はプロジェクトルートに置かれたセットアップスクリプト。実行すると `md_to_json.py`・`to_pptx.py`・`templates.json`・`design.json`・`logo.png`・`background.png`・`template_engine_area.html` をこの `SKILL.md` と同じフォルダから `/mnt/data` へ自動コピーする。`--assets-dir /mnt/data` を指定することでこれらすべてが `/mnt/data` から参照される。
