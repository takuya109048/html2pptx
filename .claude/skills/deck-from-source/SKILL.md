---
name: deck-from-source
description: 原文ソース（テキスト/URL/ファイル）をGLOBIS手法で分析し、プレゼンテーションストーリーを設計した上でスライドデッキMDとPPTXを生成するスキル。「スライドを作って」「デッキにして」「プレゼン資料にして」と依頼されたとき、またはURLやファイルを渡されたときに必ずこのスキルを使うこと。カスタムGPTs流用前提の設計（SKILL.md≤5000字＋context.md参照）。
---

# deck-from-source: 原文からスライドデッキ生成

**毎ターン開始時に必ず実行:**
```json
{ "queries": ["context.mdのmd全文をfile search"] }
```
context.mdに全詳細ルールが記載されている。

**アップロードファイルのパス解決（最初のcode interpreter実行の冒頭で1回）:**
カスタムGPTsでは `/mnt/data` 直下のファイルが `assistant-{id}-{name}` にリネームされる。
以下をコード冒頭で実行し、プレフィックスなしの元ファイル名でコピー配置してから本処理に進む。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())
```

このスキルではターンA/Bでcode interpreterを使わないため、ターンC冒頭でこれを実行する。

---

## ターン構造（厳守）

このスキルは以下の3ターン構造で動作する。各ターンの役割を厳守し、指定外の処理を混入させないこと。

```
【ターンA】ソース受け取り → nanobanana2質問のみ → Yes/No回答待ち
【ターンB】分析〜MDファイル保存まで実施 → PPTX変換の進行確認質問 → Yes/No回答待ち
【ターンC】コードインタープリターでMD出力・PPTX変換・ダウンロードリンク提示
```

各ターンはユーザーのYes/No回答を受け取るまで次のターンに進まない。

---

## ターンA: ソース受け取り + nanobanana2確認

ソースを受け取ったら（テキスト/URLはWebFetch/ファイルはReadで取得）、**このターンでは以下の1つの質問だけを返す。それ以外の分析・判断・質問は一切行わない。**

> 「nanobanana2による生成画像を挿入プランにしますか？（YesにするとPlainスライドに画像プレースホルダーとプロンプトが追加されます）」

スライド枚数・発表者名・対象オーディエンス等についてはユーザーに聞かない。ターンBでAIが自律判断する。

---

## ターンB: 分析・構成・MD生成・保存（1ターンで完結）

nanobanana2の返答を受け取ったら、以下をすべて1ターン内で実施する。

### B-1: 思考過程の出力（必須）

分析・判断の根拠を以下の形式で出力する。ユーザーへの確認は行わない。

```
## 思考過程

**ソース分析:**
- 発表目的: [情報共有/説得/依頼/報告] → 判断根拠
- 推定オーディエンス: [社内上司/顧客/経営層/一般]
- 推定発表時間: [X分] → スライド枚数目安: [N枚]

**フレームワーク選択:**
[SDS/PREP/DESC/序論→本論→結論/AIDMA] を選択。
理由: [ソースの性質・目的に基づく判断根拠]

**メインメッセージ:**
「[1文で定義]」

**スライド構成案:**
1. [テンプレート] タイトル・選択理由
2. [テンプレート] タイトル・選択理由
...

**nanobanana2適用方針:** [Yes/Noに応じた方針]
```

### B-2: MDコンテンツ生成

context.mdのSTORY_ANALYSIS・TEMPLATE_WORKFLOW・MD_SYNTAX・CONTENT_LIMITS・CONTENT_FORMATセクションに従い、B-1の構成案を実装する。各セルのコンテンツがCONTENT_LIMITSの上限・下限を満たすことを確認する。

**コンテンツ生成の4原則（全レイアウト共通）:**

- **ソース忠実性**: 箇条書きの各項目は原文ソースから根拠が取れるものだけを記載する。ソースにない情報の追加・推測・水増しは行わない。ソース内容が不足なら項目数を減らす（下限に合わせる）。
- **密度目標（通常時）**: 各セルをCONTENT_LIMITSの最大容量の**70〜80%**程度埋めることを目標とする。空白が目立つほど少なくしない。
- **密度目標（nanobanana使用時）**: card・flow_xstepレイアウトはアイコンを後から配置するスペースを確保するため、最大容量の**60〜70%**を目標とする。
- **表現形式の多様性**: plain系は冒頭prose（1〜2文）から箇条書きへ移行し、card系は`**キーワード**`太字+動詞句で単調な体言止め羅列を避ける。context.mdのCONTENT_FORMAT参照。

- 思考過程で決定したテンプレートをそのまま適用する
- **⚠️ 重要:** card-a等のコンテンツブロック内に `---` を書かない（パーサーがスライド区切りとして解釈する）
- nanobanana2 Yes → context.mdのNANOBANANA_RULESに従いimage_label_1・noteにプロンプトを追記

### B-3: MDファイル保存

**B-2で生成したスライドMDのみを `deck.md` として保存する。**

- ファイルの先頭は最初のスライドの `# タイトル` から始まる
- B-1の思考過程テキストはチャット出力のみ。ファイルには一切含めない
- ファイル内容は `---` 区切りのスライド群だけで構成される純粋なデッキMD

**ターンB中はコードインタープリターの使用を一切禁止する。** ファイル保存・スクリプト実行・変換処理を含むあらゆるコードインタープリター操作はターンCまで行わない。

### B-4: ターンC移行の確認（必須）

B-3のファイル保存が完了したら、**このターンの最後に以下の質問だけを返す。** それ以外の処理は一切行わない。

> 「deck.mdを保存しました。このままPPTXへの変換（ターンC）に進みますか？」

- **Yes** → 次のターンでターンCを実行する
- **No** → ユーザーの修正指示を受けてMDを修正後、再度この質問に戻る

---

## ターンC: コードインタープリターで変換・出力（1ターンで完結）

B-4に「Yes」と回答されたら、以下を **1つのコードインタープリター実行ブロック** で行う。

**設計方針:** 冒頭で `resolve_uploads.py` を exec し、`/mnt/data` 直下の `assistant-{id}-<name>` をクリーン名にコピー配置して正規化する。以降の全処理は **絶対パス + `cwd=/mnt/data`** で実行する。これでスクリプト間連携が単純化され失敗ポイントが消える。

```python
import glob, os, subprocess, sys

MNT = "/mnt/data"

# ① /mnt/data 直下のアップロードプレフィックスを一括解消
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())

# ② B-3 で作成したデッキ本文を /mnt/data/deck.md として書き出す
#    DECK_MD は同じブロック直前で DECK_MD = """..B-3のMD全文.."""  として定義しておく
deck_path = os.path.join(MNT, "deck.md")
with open(deck_path, "w", encoding="utf-8") as f:
    f.write(DECK_MD)

# ③ md_to_json.py を絶対パス・CWD固定で実行
subprocess.run(
    [sys.executable, os.path.join(MNT, "md_to_json.py"), deck_path, "--assets-dir", MNT],
    check=True,
    cwd=MNT,
)

# ④ ダウンロードリンク
for filename in ["deck.md", "deck.json", "deck.pptx"]:
    print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

**補足:**
- `DECK_MD` は同じブロックで `DECK_MD = """..."""` と定義してから使う。本文内の三重バッククオートは三重クオート文字列内でも素通りする（Pythonの特殊文字ではない）ので、B-3のMDをそのまま貼り付けて良い。
- `md_to_json.py` / `to_pptx.py` には `_find_file` / `_find_prefixed` の保険が残っており、`resolve_uploads.py` が未配置の環境でも即座には壊れない。
- `/mnt/data` にスクリプト群が存在しない環境では、context.md の SETUP_SCRIPT に従い先に `setup_deck.py` を実行してコピーする（`resolve_uploads.py` も同時にコピーされる）。
