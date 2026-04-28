---
name: deck-from-source
description: 原文ソース（テキスト/URL/ファイル）からスライドデッキMDとPPTXを生成するスキル。初回はPPTX生成へ進まず、必ずnanobanana2生成画像を使うかYes/No質問だけを返す。Yes/No回答後にGLOBIS手法で分析し、MD・PPTX生成まで実行する。カスタムGPTs流用前提の設計（SKILL.md≤5000字＋context.md参照）。
---

# deck-from-source: 原文からスライドデッキ生成

**毎ターン開始時に必ず実行:**
```json
{ "queries": ["context.mdのmd全文をfile search"] }
```
context.mdに全詳細ルールが記載されている。

**アップロードファイルのパス解決（ターンBの最初のcode interpreter実行冒頭で1回）:**
カスタムGPTsでは `/mnt/data` 直下のファイルが `assistant-{id}-{name}` にリネームされる。
以下をコード冒頭で実行し、プレフィックスなしの元ファイル名でコピー配置してから本処理に進む。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())
```

---

## ターン構造（厳守）

## 最初の応答ゲート（最重要）

ユーザーがソースと生成依頼を同時に渡しても、同じ応答で分析・MD生成・PPTX生成を始めない。
直近のユーザー発話に `Yes` / `No` / `はい` / `いいえ` / `使う` / `使わない` などnanobanana2方針が明示されていない場合、必ずターンAの質問だけを返す。

このスキルは以下の **2ターン構造** で動作する。

```
【ターンA】ソース受け取り → nanobanana2質問のみ → Yes/No回答待ち
【ターンB】分析〜PPTX変換まですべて1ターンで完結
```

---

## ターンA: ソース受け取り + nanobanana2確認

ソースを受け取ったら（テキスト/URLはWebFetch/ファイルはReadで取得）、**このターンでは以下の1つの質問だけを返す。それ以外の分析・判断・質問・ファイル生成は一切行わない。**

> 「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（YesにするとPlainスライドに画像プレースホルダーとプロンプトを追加します。Noならテキスト中心で生成します）」

スライド枚数・発表者名・対象オーディエンス等についてはユーザーに聞かない。ターンBでAIが自律判断する。

---

## ターンB: 分析・MD生成・プロンプト自己点検・PPTX変換（1ターンで完結）

直近のユーザー返答でnanobanana2のYes/No方針を受け取ったら、以下をすべて1ターン内で実施する。

### B-1: 内部分析（出力禁止）

ソース分析、原文密度の判定、必要に応じた内部展開、フレームワーク選択、メインメッセージ、スライド構成案、nanobanana2適用方針は内部で判断する。**思考過程・分析メモ・構成案はユーザーに表示しない。** 最終出力は生成ファイルと簡潔な完了報告だけにする。

### B-2: MDコンテンツ生成

context.mdのSTORY_ANALYSIS・SOURCE_ENRICHMENT・TEMPLATE_WORKFLOW・MD_SYNTAX・CONTENT_LIMITS・CONTENT_VARIATION・SLIDE_STYLE・SPEAKER_NOTESセクションに従い、内部で決めた構成案を実装する。

- 内部分析で決定したテンプレートを適用する
- 構造化済み・簡素な原文は、そのまま短い箇条書きへ移さず、背景・理由・比較・注意点を内部展開してからスライド本文とnoteへ配分する
- **2枚目固定:** cover直後は必ず `plain_2col` の目次。大見出しでカテゴリを作り、配下に小見出しとして各スライドタイトルを置く。左カラムへ順に積み、入りきらない残りだけ右へ送る
- **⚠️ 重要:** card-a等のコンテンツブロック内に `---` を書かない（パーサーがスライド区切りとして解釈する）
- nanobanana2 Yes → context.mdのNANOBANANA_RULESに従う。**目次以外のplain候補は必ず `plain_image_col` へ置換するか、table/list/flow系へ再設計する。**
- **本文密度:** CONTENT_LIMITSの件数・視覚行数・本文文字量を満たし、収めるために内容を薄くしない
- **表現バリエーション:** カード/カラム内を箇条書きだけで埋めず、リード文・短文項目・対比表現・問いかけ・補足文を混ぜ、同じ型の反復を避ける
- **Markdown強調:** `**太字**`、*斜体*、`コード`、~~旧情報~~、番号リスト、短い小見出しを積極的に使い、構造化とハイライトで意味を読み取りやすくする
- **文体:** スライドに表示される本文はすべてである調にし、です・ます調を使わない
- **読み上げ原稿:** noteはスライド本文の単なる要約ではなく、前後スライドのつながり・タイトル・各カード/表/フローの意味・聴衆が取るべき解釈を読み上げだけで理解できる文章にする。同じ冒頭句を反復しない
- 生成したMDはコンテキスト内の変数 `DECK_MD` として保持する（ファイル保存は不要）

### B-3: プロンプト自己点検（コード実行なし）

context.mdのDENSITY_REVIEWセクションに従い、DECK_MDを目視で自己点検してから修正する。**この段階でPythonスクリプトやcode interpreterによる密度検証を行わない。**

- 各カード/カラムが「リード文＋必要件数＋補足」で埋まっているか確認する
- 3card系は余白が目立たず、converge系は結論とはみ出しが競合しない密度へ整える
- 箇条書きだけの羅列、`**ラベル**: 説明`の連続、短すぎるnote、同じ冒頭句で始まるnoteを修正する
- Markdownの強調・階層・番号付けが少ないスライドは、重要語や対比を装飾して読みやすくする
- `です/ます/ください`がスライド表示文に残っていないか確認し、である調へ直す
- nanobanana2 Yesの場合、目次以外に`plain_1col` / `plain_2col` が残っていないことを確認する
- 修正後のDECK_MDだけをB-4へ渡す

### B-4: PPTX変換・ダウンロードリンク（code interpreter）

```python
import glob, os, subprocess, sys
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m: exec(open(_m[0]).read())

DECK_MD = """(最終確定したDECK_MD全文)"""
deck_path = os.path.join(MNT, "deck.md")
json_path = os.path.join(MNT, "deck.json")
pptx_path = os.path.join(MNT, "deck.pptx")
with open(deck_path, "w", encoding="utf-8") as f:
    f.write(DECK_MD)
subprocess.run(
    [sys.executable, os.path.join(MNT, "md_to_json.py"), deck_path, pptx_path, "--json", json_path, "--assets-dir", MNT],
    check=True, cwd=MNT,
)
for fn in ["deck.md", "deck.json", "deck.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```

**補足:**
- DECK_MD 内の三重バッククオートはPythonの三重クオート文字列内でも素通りするのでそのまま貼り付けてよい
- `/mnt/data` にスクリプト群が存在しない環境では、context.md の SETUP_SCRIPT に従い先に `setup_deck.py` を実行する
