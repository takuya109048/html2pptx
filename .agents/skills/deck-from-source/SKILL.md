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

code interpreterに渡すcode本文は、冒頭に日本語の一文コメントを置き、何のために何を実行するかを自然文で示す。コメントはGUIアクティビティでユーザーに見えるため、秘密情報や長い仕様説明は書かない。初回コードは次を使う。

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

code interpreterのログは800文字超で中間省略される前提で扱う。context_loader.pyは1回に1チャンクだけ出し、先頭に`[ctx フェーズ 現在/総数 chunk_id]`、末尾に`NEXT 次/総数 ACK xxxxxxxx`または`DONE 総数/総数 ACK xxxxxxxx`を出す。複数チャンクをループ出力しない。続きの取得では、直前のNEXT値とACKを次のcode冒頭コメントにも写す。

## 詳細コンテキスト取得

ターンBではDECK_SOURCE_JSONを書く前に、必ずcontext_loader.pyで該当フェーズをDONEまで読み切る。

Yesの場合:

```python
# turn_b_yes用の詳細コンテキスト読み込みを開始し、何件中何件目まで読めたかとNEXT/DONE状態を表示します。
import glob, subprocess, sys
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "init", "turn_b_yes"], check=True)
```

Noの場合は最後の引数をturn_b_noにする。続きは1回のcode interpreter実行ごとに次だけを実行する。

```python
# 前回表示されたNEXT 002/031 ACK abc12345に従い、詳細コンテキスト002/031を読み込んで次のNEXT/DONE状態を確認します。
import subprocess, sys
ACK = "abc12345"
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "advance", ACK], check=True)
```

上の`002/031`とACKは例であり、固定文のまま使い回さない。前回出力末尾が`NEXT 004/031 ACK xxxxxxxx`なら、次のcodeコメントとACK変数も書き換える。出力先頭の`[ctx フェーズ 現在/総数 chunk_id]`で読み込み進捗を確認し、末尾がDONEになるまで生成へ進まない。ACKを見失ったら`repeat`で再発行する。

strict-emphasis失敗時は`repair emphasis`、strict-densityや本文不足は`repair density`、文字化け、markup、title、section、block系は`repair text`、実行ファイル配置が必要な時は`repair setup`で開始し、以降は`advance <ACK>`で読む。

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
    "--require-context-done",
    "turn_b_yes" if USE_NANOBANANA2 else "turn_b_no",
]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")

subprocess.run(cmd, check=True, cwd=MNT)
for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```
