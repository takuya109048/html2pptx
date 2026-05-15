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

## 分割コンテキスト読込ゲート

このスキルでデッキ生成ターンに入る場合、分割コンテキスト読込は任意ではなく必須である。

Yes/No方針を受け取った直後、スライド構成、source_spine、DECK_SOURCE_JSON、PPTX変換を考え始めてはならない。

まずチャットに次を出す。

「分割コンテキストをcode interpreterでDONEまで読み切ってから、スライド構成とPPTX生成に進みます。」

その直後にcode interpreterでcontext_loader.pyを実行し、context.mdが指定する必須フェーズ群をすべてDONEまで読む。

DONE確認前は禁止:
- 原文分析
- スライド構成
- source_spine作成
- DECK_SOURCE_JSON作成
- PPTX変換
- 成果物リンク提示

context_loader.pyの続き取得は、前回出力末尾の `NEXT ... KEY ...` のKEYを使って `next <KEY>` で読む。無引数nextは使わない。

分割コンテキスト読込でエラーが出た場合は、生成へ進まず、setupまたはファイル配置を修正してから再度読み込む。

スキル自体の修正、リファクタリング、検証を依頼された場合は、生成フローへ入らず、context.mdと関連ファイルを編集・検証する。
