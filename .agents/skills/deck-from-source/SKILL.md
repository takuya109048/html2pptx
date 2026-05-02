---
name: deck-from-source
description: 原文ソース（テキスト/URL/ファイル）から、安定したdeck_source.jsonとPPTXを生成するスキル。初回はPPTX生成へ進まず、必ずnanobanana2生成画像を使うかYes/No質問だけを返す。Yes/No回答後に、構成分析、JSON生成、PPTX変換、json/pptxリンク提示まで実行する。Markdownデッキ形式は廃止し、カスタムGPTs流用前提（SKILL.md≤5000字、詳細はcontext.md）。
---

# deck-from-source

原文ソースから、発表用のdeck_source.jsonとPPTXを生成する。Markdownデッキは作らない。
SKILL.mdは最小限の実行指示だけを持ち、詳細ルールは毎ターンcontext.mdから読む。

## 毎ターン最初に行うこと

file searchで次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

context.mdに、構成分析、JSONスキーマ、レイアウト選択、密度、note、画像プロンプト、ファイル名、ダウンロード提示の詳細がある。

## アップロードファイル解決

ターンBでcode interpreterを使う最初のコード冒頭に必ず入れる。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())
```

## ターン構造

このスキルは2ターンで動く。

ターンA:
ソースを受け取る。分析、判断、JSON生成、PPTX生成はしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要ならターンBで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、ソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

## ターンBの作業

1. ソース全体から主張、対象、目的、流れをGLOBIS的に内部分析する。
2. context.mdのSTORY_ANALYSIS、SOURCE_ENRICHMENT、JSON_SCHEMA、LAYOUT_RULES、CONTENT_LIMITS、HIGHLIGHT_SKIMLINE、DENSITY_REVIEW、SPEAKER_NOTESに従ってDECK_SOURCE_JSONを作る。薄い原文かどうかに関係なく、先に内部でだらだらと長文の詳細原稿へ書き直し、その厚みからスライドを設計する。
3. slides配列には本文スライドだけを書く。表紙と目次はdeck_source_to_json.pyが自動生成する。各slides[].titleが目次小見出しになるため、重複や空タイトルを作らない。
4. nanobanana2がYesなら、slidesにplain_1colを使わない。各スライドはplain_2colでblocks.card-bに説明図プロンプトを置くか、card/flow系でicon_promptを置く。
5. layoutごとの必須blocks名を守る。plain_2colはcard-a/card-b、list_3cardはcard-a/card-b/card-c、flow_3stepはstep-a/step-b/step-c、flow_4stepはstep-a/step-b/step-c/step-dで書く。text、step、card、plainなどの独自keyを作らない。
6. 生成後、FINAL_SELF_CHECKに従って目視で自己点検する。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグを出さない。
7. 表紙タイトルを短い英語のslugへ変換し、出力ファイル名に使う。詳細はcontext.mdのOUTPUT_FILESに従う。
8. deck_source.jsonとpptxだけをユーザーへ提示する。変換後slides.jsonは中間生成物として作ってよいが、ダウンロードリンクや最終報告には出さない。

## PPTX変換コードの型

DECK_SOURCE_JSONを確定したら、code interpreterで次の型を使う。TITLE_SLUGは表紙タイトルを短い英語で表したsnake_caseまたはkebab-caseにする。

```python
import glob, json, os, subprocess, sys
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())

TITLE_SLUG = "short_english_title"
USE_NANOBANANA2 = True  # ユーザー回答がYesならTrue、NoならFalse
DECK_SOURCE_JSON = { }  # 最終確定したdictを入れる
source_path = os.path.join(MNT, f"{TITLE_SLUG}.json")
slides_json_path = os.path.join(MNT, f"{TITLE_SLUG}.slides.json")
pptx_path = os.path.join(MNT, f"{TITLE_SLUG}.pptx")
with open(source_path, "w", encoding="utf-8") as f:
    json.dump(DECK_SOURCE_JSON, f, ensure_ascii=False, indent=2)
cmd = [sys.executable, os.path.join(MNT, "deck_source_to_json.py"), source_path, pptx_path, "--json", slides_json_path, "--assets-dir", MNT, "--require-agenda", "--strict-blocks", "--strict-density", "--strict-agenda-grouping", "--strict-markup", "--strict-emphasis", "--strict-compact-blocks", "--strict-text-integrity"]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")
subprocess.run(cmd, check=True, cwd=MNT)
for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```

## 変換補足

/mnt/dataにスクリプト群がない場合は、context.mdのSETUP_SCRIPTに従って先に実行ファイル群を配置する。
