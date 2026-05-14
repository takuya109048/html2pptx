---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。ユーザーが資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求めたら使う。初回は生成へ進まずnanobanana2画像を使うかYes/Noだけを確認し、Yes/No回答ターンでは外部JSONコンテキスト読込だけを完了する。次ターンで読込済みコンテキストを使い、分析、JSON生成、PPTX変換、json/pptxリンク提示まで行う。スキル自体の修正依頼では生成フローに入らない。
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

code interpreterに渡すcode本文は、冒頭に日本語の一文コメントを置き、何のために何を実行するかを自然文で示す。コメントはGUIアクティビティでユーザーに見えるため、秘密情報や長い仕様説明は書かない。初回コードは次を使う。

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

code interpreterのログは800文字超で中間省略される前提で扱う。context_loader.pyは1回に1チャンクだけ出し、先頭に`[ctx 現在/総数 chunk_id]`、末尾に`NEXT 次/総数`または`DONE 総数/総数`を出して進捗を見せる。複数チャンクをループ出力しない。続きの取得では、直前の`NEXT 004/031`を次のcode冒頭コメントにも写し、GUIアクティビティ上でも進捗が変わるようにする。

## 詳細コンテキスト取得

ターンBではDECK_SOURCE_JSONを書かず、context_loader.pyで該当フェーズをDONEまで読み切ることだけを行う。DONE後は生成へ進まず、次ターンで生成できる状態として止める。

Yesの場合:

```python
# turn_b_yes用の詳細コンテキスト読み込みを開始し、何件中何件目まで読めたかとNEXT/DONE状態を表示します。
import glob, subprocess, sys
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "start", "turn_b_yes"], check=True)
```

Noの場合は最後の引数をturn_b_noにする。続きは1回のcode interpreter実行ごとに次だけを実行する。

```python
# 前回表示されたNEXT 002/031に従い、詳細コンテキスト002/031を読み込んで次のNEXT/DONE状態を確認します。
import subprocess, sys
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "next"], check=True)
```

上の`002/031`は例であり、固定文のまま使い回さない。前回出力末尾が`NEXT 004/031`なら、次のcodeコメントも`004/031`に書き換える。出力先頭の`[ctx 現在/総数 chunk_id]`で読み込み進捗を確認し、末尾がDONEになるまで止まらない。DONE後は「詳細コンテキストを読み切ったので、次のターンで生成します」とだけ返し、分析、構成案、DECK_SOURCE_JSON、PPTX生成へ進まない。途中でエラーが出たら、欠けたファイルやフェーズを直してから再取得する。

strict-emphasis失敗時はrepair_emphasis、strict-densityや本文不足はrepair_density、文字化け、markup、title、section、block系はrepair_text、実行ファイル配置が必要な時はsetupを同じstart/next方式で読む。

## ターン判定

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要なら生成ターンで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、前ターンのソースを保持したまま、該当フェーズの詳細コンテキスト読込だけを行う。Yesならturn_b_yes、Noならturn_b_noをDONEまで読む。DONEになったら生成へ進まず、読了した方針を会話上に残して「次のターンで生成します」と短く返す。

ターンC:
直前のアシスタント返答がturn_b_yesまたはturn_b_noのDONE読了報告なら、分割コンテキストを再読込しない。前々ターンの原文ソース、Yes/No方針、直前ターンで会話に展開済みの詳細コンテキストを使い、ソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで完了する。新しいソース、方針変更、読了不足、修復フェーズが必要な場合だけcontext_loader.pyを再実行する。思考過程、分析メモ、構成案はユーザーに出さない。

## 生成の不変条件

root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。

slides[].titleは目次小見出しなので名詞句か体言止めにし、主張や示唆はmessageへ移す。layoutごとの必須blocks名を守り、独自keyを作らない。nanobanana2がYesなら本文slidesにplain_1colを使わない。

原文の章順、因果順、結論位置を最優先する。発表フレームや密度補強のために、原文の主従関係やストーリー順を入れ替えない。

変換前にFINAL_SELF_CHECKを行う。Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

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
