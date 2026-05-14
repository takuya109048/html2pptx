---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。ユーザーが資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求めたら使う。初回は生成へ進まずnanobanana2画像を使うかYes/Noだけを確認し、回答後はcontext.mdを読み、さらに該当context_data.jsonフェーズをDONEまで読んでから分析、JSON生成、PPTX変換、json/pptxリンク提示まで完了する。スキル自体の修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースから発表用のdeck_source.jsonとPPTXを生成する。Markdownデッキは作らない。context.mdを毎ターン読む司令塔兼コンテキスト保存領域として扱う。Turn Bの生成では、スライド構成やDECK_SOURCE_JSON作成へ進む前に、必ず該当するcontext_data.jsonフェーズをcontext_loader.pyでDONEまで読む。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼でだけ生成フローに入る。

ユーザーがこのスキルのSKILL.md、context.md、context_data.json、context_loader.py、変換スクリプト、指示文の修正を求めている場合は生成フローへ入らない。Yes/No質問も出さず、対象ファイルの編集と検証を行う。

## 毎ターン最初

file searchで次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

code interpreterに渡すcode本文は、冒頭に日本語の一文コメントを置き、何のために何を実行するかを自然文で示す。初回コードは次を使う。

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

## 外部JSONの扱い

Turn Bの通常生成では、DECK_SOURCE_JSONを書く前だけでなく、ソース分析、構成決定、スライド割り、layout選択へ進む前に、必ずcontext_loader.pyで該当フェーズをDONEまで読む。Yesならturn_b_yes、Noならturn_b_noを読む。context.mdは主要ルールの保存領域だが、context_data.json読了ゲートの代替にはしない。

strictエラー、文字化け、JSON構造エラー、実行ファイル不足が起きた時も、該当するrepair_emphasis、repair_density、repair_text、setupをDONEまで読む。

code interpreterのログは800文字超で中間省略される前提で扱う。context_loader.pyは1回に1チャンクだけ出し、最後の出力を`/mnt/data/deck_context_last_output.txt`にも保存する。呼び出しコードは標準出力をcaptureし、表示が空なら復元ファイルを読む。両方が空なら分析や生成へ進まずエラーにする。続きの取得では、直前の`NEXT 004/031`などを次のcode冒頭コメントにも写す。詳細な堅牢読み込み手順はcontext.mdに従う。

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要ならターンBで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、前ターンのソースを使う。最初に該当フェーズをDONEまで読む。DONEを確認するまでは、ソース分析、構成決定、スライド割り、layout選択、DECK_SOURCE_JSON生成へ進まない。読了後、分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

## 生成の不変条件

root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。

slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。layoutごとの必須blocks名を守り、独自keyを作らない。nanobanana2がYesなら本文slidesにplain_1colを使わない。

変換前にFINAL_SELF_CHECK相当の目視点検を行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

## PPTX変換コード

DECK_SOURCE_JSONを確定したら、code interpreterで次の型を使う。TITLE_SLUGはファイル名専用であり、表紙に出るroot.titleは日本語のままにする。

```python
# 確定済みDECK_SOURCE_JSONをJSONに保存してstrict検証付きでPPTXへ変換し、deck_source.jsonとPPTXのリンクを表示します。
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
