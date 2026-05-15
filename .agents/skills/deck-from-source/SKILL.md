---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。原文のストーリーに忠実で、本文に厚みがあり、noteを読み上げ原稿として使える発表資料へ変換する。資料化、スライド化、PPTX作成、deck_source.json生成、発表資料への変換を求められたら使う。スキル自体の修正依頼では生成フローに入らず、対象ファイルを編集・検証する。
---

# deck-from-source

このスキルを使う各ターンの冒頭で、必ずfile searchを実行し、context.mdの全文を読み込む。

file searchではqueriesだけを使い、次のクエリだけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

以後の判断、質問、生成、変換、修復、検証、出力は、すべてcontext.mdの指示に従う。

context.mdが外部JSONコンテキストの読み込みを指示する場合は、context.mdに書かれたフェーズ、手順、停止条件に従う。

## Custom GPTs共通レイヤー

code interpreterに渡すPythonコード本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。

デッキ生成ターンの初回code interpreterでは、分割コンテキストを読む前に現在時刻を取得し、処理開始時刻として /mnt/data/deck_generation_timer.json へ保存する。あわせて、アップロード済みファイル名を安定化するためにresolve_uploads.pyをglobで探して実行する。

```python
# 処理開始時刻を記録し、アップロード済みファイル名を安定化して、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob, json
from datetime import datetime
with open("/mnt/data/deck_generation_timer.json", "w", encoding="utf-8") as f:
    json.dump({"started_at": datetime.now().astimezone().isoformat(timespec="seconds")}, f, ensure_ascii=False)
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

スライド修正まで終わり、最終版PPTXを出力できる状態になったら、code interpreterで再度現在時刻を取得し、開始時刻との差分を計算する。最終チャットでは、開始時刻や終了時刻は表示せず、所要時間だけを短くコメントする。

code interpreterログは先頭400文字と末尾400文字の合計800文字だけが安定して渡る前提で扱う。長いコンテキストを一括printしてはならない。

context_loader.pyは1回に1チャンクだけ出力する。複数チャンクを読む時は、1回のcode interpreter実行につきcontext_loader.pyを1回だけ起動する。ループ、複数のsubprocess.run、複数のexecで同じcode本文内からローダーを2回以上起動してはならない。

## 分割コンテキスト読込ゲート

このスキルでデッキ生成ターンに入る場合、分割コンテキスト読込は任意ではなく必須である。

Yes/No方針を受け取った直後、スライド構成、source_spine、DECK_SOURCE_JSON、PPTX変換を考え始めてはならない。

まず最初のcode interpreterを開始する前に、チャット本文として、内部の読込手順ではなく所要時間の見通しを必ず出す。code interpreter内の冒頭コメントだけで代替してはならない。

「資料化を開始します。スライド構成、検証、PPTX出力までおおよそ5分程度かかります。」

その直後にcode interpreterでcontext_loader.pyを実行し、context.mdが指定する必須フェーズ群をすべてDONEまで読む。

DONE確認前は禁止:
- 原文分析
- スライド構成
- source_spine作成
- DECK_SOURCE_JSON作成
- PPTX変換
- 成果物リンク提示

context_loader.pyの続き取得は、前回出力末尾の `NEXT ... KEY ...` のKEYを使って `next <KEY>` で読む。無引数nextは使わない。前回出力末尾のNEXT値とKEY値を、次回code本文の冒頭コメントとコマンドの両方に写す。

分割コンテキスト読込でエラーが出た場合は、生成へ進まず、setupまたはファイル配置を修正してから再度読み込む。

スキル自体の修正、リファクタリング、検証を依頼された場合は、生成フローへ入らず、context.mdと関連ファイルを編集・検証する。
