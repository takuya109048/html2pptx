---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。資料化、スライド化、PPTX作成、deck_source.json生成、発表資料化の依頼で使う。初回は生成せずnanobanana2画像を使うかYes/Noだけ確認し、回答後はフェーズごとに外部JSONを直前取得して、json/pptx/logリンク提示まで完了する。スキル修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースからdeck_source.jsonとPPTXを生成する。SKILL.mdは肥大化させず、毎ターンcontext.mdを確実に読む責任を持つ。詳細ルール、フェーズ順、code interpreterでのコンテキスト取得、変換、検証はcontext.mdとcontext_loader.pyの状態機械に従う。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼で生成フローに入る。

このスキル自体の修正、リファクタリング、検証依頼では生成フローへ入らず、対象ファイルを編集、検証する。

## 毎ターン最初

file searchが使える環境では次だけを実行し、取得したcontext.mdに従う。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

Codexではローカルのcontext.mdを毎ターン読み直す。context.mdを読まずに分析、生成、変換、検証へ進まない。context.mdだけを読んだ状態では、スライド構成、章立て、枚数、保存名、JSON骨格を作らない。

Custom GPTsではチャット冒頭でresolve_uploads.pyをcode interpreterで1回実行し、アップロード済みファイル名を安定化する。code本文の先頭には、何を実行するかが分かる短い日本語コメントを書く。

## 実行原則

新しい原文ソースを受け取り、nanobanana2方針が未確定なら、context.mdのターンAに従う。

Yes/No方針を受け取ったら、context.mdのターンBに従う。必要な外部JSONコンテキストはcontext_loader.py init yes、init no、advance <ACK>、phase-done <ACK>で1チャンクずつ読む。read、start、next、get、フェーズ名の直接指定は旧APIなので使わない。1回のcode interpreter実行では、コンテキストを出すローダーコマンドを1回だけ実行する。plan相当フェーズのDONE前にスライド構成を作らない。

最終出力はcontext.mdの指定どおり、deck_source.json、PPTX、code_interpreter_log.mdのリンクを提示する。
