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

## ターンB: 分析・MD生成・密度検証・PPTX変換（1ターンで完結）

直近のユーザー返答でnanobanana2のYes/No方針を受け取ったら、以下をすべて1ターン内で実施する。

### B-1: 思考過程の出力（必須）

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
...

**nanobanana2適用方針:** [Yes/Noに応じた方針]
```

### B-2: MDコンテンツ生成

context.mdのSTORY_ANALYSIS・TEMPLATE_WORKFLOW・MD_SYNTAX・CONTENT_LIMITS・CONTENT_VARIATION・SLIDE_STYLE・SPEAKER_NOTESセクションに従い、B-1の構成案を実装する。

- 思考過程で決定したテンプレートをそのまま適用する
- **⚠️ 重要:** card-a等のコンテンツブロック内に `---` を書かない（パーサーがスライド区切りとして解釈する）
- nanobanana2 Yes → context.mdのNANOBANANA_RULESに従いimage_label_1・noteにプロンプトを追記
- **本文密度:** CONTENT_LIMITSの件数・視覚行数・本文文字量を満たし、収めるために内容を薄くしない
- **表現バリエーション:** カード/カラム内を箇条書きだけで埋めず、リード文・短文項目・対比表現・問いかけ・補足文を混ぜ、同じ型の反復を避ける
- **文体:** スライドに表示される本文はすべてである調にし、です・ます調を使わない
- **読み上げ原稿:** noteはスライド本文の単なる要約ではなく、タイトル・各カード/表/フローの意味・聴衆が取るべき解釈を読み上げだけで理解できる文章にする
- 生成したMDはコンテキスト内の変数 `DECK_MD` として保持する（ファイル保存は不要）

### B-3: 密度検証ループ（code interpreter使用、最大3回）

context.mdのDENSITY_LOOPセクションに従い実行する。

**各ループで実行するコード:**
```python
# 初回のみ: resolve_uploads.py を exec
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m: exec(open(_m[0]).read())

DECK_MD = """(コンテキスト内の現在のDECK_MD全文)"""
NANOBANANA = True  # or False
_v = glob.glob("/mnt/data/*validate_density.py")
exec(open(_v[0]).read())
```

- 出力末尾の `PASS` / `FAIL` を確認する
- **PASS** → B-4へ進む
- **FAIL** → FAIL行（件数、低密度、はみ出し、単調ブロック、note不足）を見て**コンテキスト内の DECK_MD** を修正し再実行（最大3回）
- 3回でPASSしなくてもB-4へ進む
- **重要:** 修正はコンテキスト内のDECK_MDに対して行う。ファイルへの読み書きで修正してはならない

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
