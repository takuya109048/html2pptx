---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。ユーザーが資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求めたら使う。初回は生成へ進まずnanobanana2画像を使うかYes/Noだけを確認し、回答後に外部JSONコンテキストを読み切ってから分析、JSON生成、PPTX変換、json/pptxリンク提示まで完了する。スキル自体の修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースから発表用のdeck_source.jsonとPPTXを生成する。Markdownデッキは作らない。詳細ルールは毎ターンcontext.mdを読み、必要フェーズをcontext_loader.pyでDONEまで読む。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼だけ生成フローに入る。

このスキル自体、context、変換スクリプト、指示文の修正依頼では生成しない。nanobanana2のYes/No質問も出さず、対象ファイルを編集し、count_chars.pyとvalidate_context_json.pyで検証する。

## 毎ターン最初

file searchではqueriesだけを使い、次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

code interpreterに渡すcode本文の先頭には、何を実行するかが分かる短い日本語コメントを必ず置く。チャット冒頭または最初のcodeではresolve_uploads.pyをglobで探して実行する。

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行します。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、構成案、JSON生成、PPTX生成をしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

ターンB:
Yesならturn_b_yes、Noならturn_b_noをcontext_loader.pyでstartし、nextを1回ずつ実行してDONEまで読む。必要フェーズをDONEまで読んでから、ソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。途中の分析メモや構成案はユーザーに出さない。

続き取得のcodeコメントには、直前出力のNEXT 004/031などを写し、GUI上でも進捗が分かるようにする。同じcode本文内でローダーを複数回起動しない。

## 構成判断

テンプレートに当てはめることより、読者が背景、理由、判断軸を追えることを優先する。レイアウト決定前に「この構造が突然出ても、前スライドまたは同スライド本文だけで意味が分かるか」を内部確認する。

少しでも無理がある場合は、カード、フロー、マトリックスへ押し込まない。plain_1col、plain_2col、画像説明用plain_2colへ逃がすか、直前に背景スライドを追加する。nanobanana2がYesでも、画像やアイコンが理解を助けないならplain_1colを使ってよい。背景がnoteにしかない状態は失敗として、表示本文または前スライドへ戻す。

## 生成条件

root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。

slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。layoutごとの必須blocks名を守り、独自keyを作らない。

変換前にFINAL_SELF_CHECKを行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。strictエラーが出たら該当repairフェーズをDONEまで読み、JSONを修復して再実行する。

## PPTX変換コード

DECK_SOURCE_JSONを確定したら、TITLE_SLUGを短い英語名にし、USE_NANOBANANA2をYes/No方針に合わせて次を使う。

```python
# 確定済みDECK_SOURCE_JSONを保存し、strict検証付きでPPTXへ変換してリンクを表示します。
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
    sys.executable, os.path.join(MNT, "deck_source_to_json.py"),
    source_path, pptx_path, "--json", slides_json_path, "--assets-dir", MNT,
    "--require-agenda", "--strict-blocks", "--strict-density",
    "--strict-agenda-grouping", "--strict-markup", "--strict-emphasis",
    "--strict-compact-blocks", "--strict-title-style", "--strict-text-integrity",
]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")
subprocess.run(cmd, check=True, cwd=MNT)
for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```
