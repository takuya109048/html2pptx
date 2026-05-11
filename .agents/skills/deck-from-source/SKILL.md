---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。資料化、スライド化、PPTX作成、deck_source.json生成、発表資料化の依頼で使う。初回は生成せずnanobanana2画像を使うかYes/Noだけ確認し、回答後はフェーズごとに外部JSONを直前取得して、json/pptx/logリンク提示まで完了する。スキル修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースからdeck_source.jsonとPPTXを生成する。context.mdを司令塔にし、作業直前にcontext_loader.pyで必要フェーズだけを1件ずつ読む。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼で生成フローに入る。

このスキルの修正依頼では生成フローへ入らず、対象ファイルを編集、検証する。

## 毎ターン最初

file searchが使える環境では次だけを実行する。Codexではローカルのcontext.mdを毎ターン読み直す。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

code本文は冒頭に日本語の一文コメントを置く。出力先は`DECK_FROM_SOURCE_OUTPUT_DIR`、なければ`/mnt/data`、なければ現在ディレクトリ。

```python
# アップロード済みファイル名を安定化し、後続処理で同じ出力先のファイルを参照できるようにします。
import glob, os
MNT = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or ("/mnt/data" if os.name != "nt" and os.path.exists("/mnt/data") else os.getcwd())
_m = glob.glob(os.path.join(MNT, "*resolve_uploads.py"))
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

全code実行でcode_interpreter_log.mdへ時刻、フェーズ、目的、入出力、結果、NEXT/DONEまたはエラーを追記する。秘密情報は書かない。

## 詳細コンテキスト取得

ターンBではcontext_data.jsonを直接読まない。既存生成物を叩き台にせず、原文から新規に作る。各作業直前に該当フェーズをDONEまで読む。

Yes時の順序:
yes_plan -> yes_schema -> yes_layout -> yes_image -> yes_body -> yes_emphasis -> yes_notes -> yes_check_convert

No時の順序:
no_plan -> no_schema -> no_layout -> no_body -> no_emphasis -> no_notes -> no_check_convert

取得開始:

```python
# yes_plan用の詳細コンテキスト読み込みを開始し、NEXT/DONE状態を確認します。
import os, subprocess, sys
MNT = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or ("/mnt/data" if os.name != "nt" and os.path.exists("/mnt/data") else os.getcwd())
subprocess.run([sys.executable, os.path.join(MNT, "context_loader.py"), "start", "yes_plan"], check=True)
```

続き:

```python
# 前回表示されたNEXT 002/006に従い、詳細コンテキスト002/006を読み込んでNEXT/DONE状態を確認します。
import os, subprocess, sys
MNT = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or ("/mnt/data" if os.name != "nt" and os.path.exists("/mnt/data") else os.getcwd())
subprocess.run([sys.executable, os.path.join(MNT, "context_loader.py"), "next"], check=True)
```

002/006は例。前回末尾がNEXT 004/006なら次のcodeコメントも004/006へ変える。Codexではshellで同じstart/nextを実行してよい。

strict-emphasis失敗時はrepair_emphasis、strict-densityや本文不足はrepair_density、文字化け、markup、title、section、block系はrepair_text、実行ファイル配置が必要な時はsetupを同じ方式で読む。

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

ターンB:
Yes/No方針を受け取ったら前ターンのソースを使う。直前読み込みと作業を交互に進め、JSON、PPTX、リンク提示まで完了する。思考過程や構成案は出さない。

## 生成の不変条件

root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。旧json/pptxは比較用に限り、成果物は今回ソースから再生成する。

slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。layoutごとの必須blocks名を守り、独自keyを作らない。nanobanana2がYesなら本文slidesにplain_1colを使わない。

変換前にFINAL_SELF_CHECKを行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

## PPTX変換コード

DECK_SOURCE_JSONを確定したら、次の型を使う。TITLE_SLUGはファイル名専用であり、表紙に出るroot.titleは日本語のままにする。

```python
# 確定済みDECK_SOURCE_JSONを保存してPPTXへ変換し、json/pptx/logのリンクを表示します。
import datetime, glob, json, os, subprocess, sys
MNT = os.environ.get("DECK_FROM_SOURCE_OUTPUT_DIR") or ("/mnt/data" if os.name != "nt" and os.path.exists("/mnt/data") else os.getcwd())
os.makedirs(MNT, exist_ok=True)
LOG = os.path.join(MNT, "code_interpreter_log.md")
def log(phase, purpose, result, inputs=None, outputs=None):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"\n- {ts} phase={phase} purpose={purpose} result={result} inputs={inputs or []} outputs={outputs or []}\n")

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

cmd = [sys.executable, os.path.join(MNT, "deck_source_to_json.py"), source_path, pptx_path, "--json", slides_json_path, "--assets-dir", MNT, "--require-agenda", "--strict-blocks", "--strict-density", "--strict-agenda-grouping", "--strict-markup", "--strict-emphasis", "--strict-compact-blocks", "--strict-title-style", "--strict-text-integrity"]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")

try:
    subprocess.run(cmd, check=True, cwd=MNT)
    log("check_convert", "strict変換", "DONE", [source_path], [pptx_path])
except Exception as e:
    log("check_convert", "strict変換", f"ERROR {type(e).__name__}: {e}", [source_path], [])
    raise

for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx", "code_interpreter_log.md"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```
