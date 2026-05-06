---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。ユーザーが資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求めたら使う。初回は生成へ進まずnanobanana2画像を使うかYes/Noだけを確認し、回答後に分析、JSON生成、PPTX変換、json/pptxリンク提示まで完了する。スキル自体の修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースから発表用のdeck_source.jsonとPPTXを生成する。Markdownデッキは作らない。SKILL.mdは実行分岐だけを持ち、詳細ルールは毎ターンcontext.mdから読む。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼でだけ生成フローに入る。

ユーザーがこのスキルのSKILL.md、context.md、スクリプト、指示文の修正やリファクタリングを求めている場合は、デッキ生成フローへ入らない。Yes/No質問も出さず、対象ファイルの編集と検証を行う。

## 毎ターン最初に行うこと

file searchで次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

context.mdには、構成分析、JSONスキーマ、レイアウト選択、密度、note、画像プロンプト、ファイル名、ダウンロード提示、自己点検の詳細がある。

code interpreterを使う最初のコード冒頭には必ず次を入れる。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())
```

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要ならターンBで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、前ターンのソースを使い、ソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

## ターンBの必須手順

1. ソース全体から主張、対象、目的、流れを内部分析する。
2. 薄い原文でも、先に内部で詳細原稿へ展開し、その厚みからスライド本文を設計する。原文にない固有数値、事例名、実績は作らない。
3. 各スライドの本文を書く前に、context.mdのHIGHLIGHT_PLANNINGで太字だけの要約線、強調語句、配置先blockを内部決定する。これはユーザーへ出さず、JSONにも独自項目として入れない。
4. context.mdのSTORY_ANALYSIS、SOURCE_ENRICHMENT、JSON_SCHEMA、LAYOUT_RULES、CONTENT_LIMITS、HIGHLIGHT_PLANNING、HIGHLIGHT_SKIMLINE、DENSITY_REVIEW、SPEAKER_NOTES、FINAL_SELF_CHECKに従ってDECK_SOURCE_JSONを作る。
5. root.summaryにサマリー（結論）を必ず書く。Yesなら画像ありスライド用にimage_promptを入れ、Noならplain_1col相当の長めの本文とMarkdown構造をblocks.card-aへ入れる。
6. slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。
7. nanobanana2がYesなら本文slidesにplain_1colを使わない。plain_2colではblocks.card-bに6:5の説明図プロンプトを置き、card/flow系ではicon_promptを置く。
8. layoutごとの必須blocks名を守る。plain_2colはcard-a/card-b、list_3cardはcard-a/card-b/card-c、flow_3stepはstep-a/step-b/step-c、flow_4stepはstep-a/step-b/step-c/step-dで書く。text、step、card、plainなどの独自keyを作らない。
9. 変換前にFINAL_SELF_CHECKを行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。
10. 表紙タイトルを短い英語slugへ変換し、出力ファイル名に使う。ユーザーにはdeck_source.jsonとpptxだけを提示し、slides.jsonは中間生成物として扱う。

## PPTX変換コードの型

DECK_SOURCE_JSONを確定したら、code interpreterで次の型を使う。TITLE_SLUGは表紙タイトルを短い英語で表したsnake_caseまたはkebab-caseにする。

```python
import glob, json, os, subprocess, sys
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())

TITLE_SLUG = "short_english_title"
USE_NANOBANANA2 = True  # YesならTrue、NoならFalse
DECK_SOURCE_JSON = { }  # 最終確定したdictを入れる

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

## 変換補足

/mnt/dataに実行ファイル群がない場合は、context.mdのSETUP_SCRIPTに従って先に配置する。変換がstrict系エラーで止まったら、エラーメッセージに対応するcontext.mdの修復ルールに従い、DECK_SOURCE_JSONを直してから再実行する。
