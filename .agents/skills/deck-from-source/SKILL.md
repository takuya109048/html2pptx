---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。ユーザーが資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求めたら使う。初回は生成へ進まずnanobanana2画像を使うかYes/Noだけを確認し、回答後に外部JSONコンテキストを読み切ってから分析、JSON生成、PPTX変換、json/pptxリンク提示まで完了する。スキル自体の修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースから発表用のdeck_source.jsonとPPTXを生成する。Markdownデッキは作らない。詳細ルールはcontext.mdを司令塔とし、必要に応じてcontext_data.jsonをcontext_loader.pyで1件ずつ読む。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼でだけ生成フローに入る。

ユーザーがこのスキルのSKILL.md、context.md、context_data.json、context_loader.py、変換スクリプト、指示文の修正を求めている場合は生成フローへ入らない。Yes/No質問も出さず、対象ファイルの編集と検証を行う。

## 毎ターン最初

file searchで次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

code interpreterを使う最初のコード冒頭には必ず次を入れる。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

code interpreterのログは400文字超で中間省略される前提で扱う。context_loader.pyは1回に1チャンクだけ出す。複数チャンクをループ出力しない。

## 詳細コンテキスト取得

ターンBではDECK_SOURCE_JSONを書く前に、必ずcontext_loader.pyで該当フェーズをDONEまで読み切る。

Yesの場合:

```python
import glob, subprocess, sys
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "start", "turn_b_yes"], check=True)
```

Noの場合は最後の引数をturn_b_noにする。続きは1回のcode interpreter実行ごとに次だけを実行する。

```python
import subprocess, sys
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "next"], check=True)
```

出力末尾がDONEになるまで生成へ進まない。途中でエラーが出たら、欠けたファイルやフェーズを直してから再取得する。

strict-emphasis失敗時はrepair_emphasis、strict-densityや本文不足はrepair_density、文字化け、markup、title、section、block系はrepair_text、実行ファイル配置が必要な時はsetupを同じstart/next方式で読む。

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要ならターンBで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、前ターンのソースを使う。該当フェーズの詳細コンテキストをDONEまで読み、ソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

## 生成の不変条件

root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。

slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。layoutごとの必須blocks名を守り、独自keyを作らない。nanobanana2がYesなら本文slidesにplain_1colを使わない。

本文slidesではlayout/blocksを直接固定せず、原則slide_kind/variant:auto/slotsを使う。deck_source_to_json.pyがtemplate_catalog.jsonから全候補を見て、内容に合う具体layoutへスコア展開する。

変換前にFINAL_SELF_CHECKを行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

## PPTX変換コード

DECK_SOURCE_JSONを確定したら、code interpreterで次の型を使う。TITLE_SLUGはファイル名専用であり、表紙に出るroot.titleは日本語のままにする。

```python
import glob, json, os, subprocess, sys
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())

TITLE_SLUG = "short_english_title"
USE_NANOBANANA2 = True
DECK_SOURCE_JSON = {}

source_path = os.path.join(MNT, f"{TITLE_SLUG}.json")
slides_json_path = os.path.join(MNT, f"{TITLE_SLUG}.slides.json")
pptx_path = os.path.join(MNT, f"{TITLE_SLUG}.pptx")

with open(source_path, "w", encoding="utf-8") as f:
    json.dump(DECK_SOURCE_JSON, f, ensure_ascii=False, indent=2)

cmd = [
    sys.executable,
    os.path.join(MNT, "deck_source_to_json.py"),
    source_path,
    pptx_path,
    "--json",
    slides_json_path,
    "--assets-dir",
    MNT,
    "--require-agenda",
    "--strict-blocks",
    "--strict-density",
    "--strict-agenda-grouping",
    "--strict-markup",
    "--strict-emphasis",
    "--strict-compact-blocks",
    "--strict-title-style",
    "--strict-text-integrity",
]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")

subprocess.run(cmd, check=True, cwd=MNT)
for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```
