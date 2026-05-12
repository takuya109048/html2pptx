---
name: deck-from-source
description: 原文ソース（テキスト、URL、ファイル）からdeck_source.jsonとPPTXを生成する。資料化、スライド化、PPTX作成、deck_source.json生成、発表資料化の依頼で使う。初回は生成せずnanobanana2画像を使うかYes/Noだけ確認し、回答後はフェーズごとに外部JSONを直前取得して、json/pptx/logリンク提示まで完了する。スキル修正依頼では生成フローに入らない。
---

# deck-from-source

原文ソースからdeck_source.jsonとPPTXを生成する。SKILL.mdは肥大化させず、毎ターンcontext.mdを確実に読む責任を持つ。詳細ルール、フェーズ順、code interpreterでのコンテキスト取得、変換、検証はcontext.mdに従う。

## 適用条件

デッキ生成、スライド化、PPTX化、deck_source.json生成の依頼で生成フローに入る。

このスキル自体の修正、リファクタリング、検証依頼では生成フローへ入らず、対象ファイルを編集、検証する。

## 毎ターン最初

file searchが使える環境では次だけを実行し、取得したcontext.mdに従う。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

Codexではローカルのcontext.mdを毎ターン読み直す。context.mdを読まずに分析、生成、変換、検証へ進まない。

## 実行原則

新しい原文ソースを受け取り、nanobanana2方針が未確定なら、context.mdのターンAに従う。

Yes/No方針を受け取ったら、context.mdのターンBに従う。生成作業へ入る前にchecklist_manager.pyで/mnt/data/task_checklist.mdを作成する。layout確定後はinsert-slidesでスライド単位のサブチェックリストを挿入する。各スライドはimage、body、emphasis、notesなどの分割コンテキスト単位で順番に読み、作成、修正、checkしてから次へ進む。

各フェーズ直前にchecklist_manager.py statusまたはnextで現在位置を確認し、表示されたctx値だけをcontext_loader.py startに渡してDONEまで読む。context_loader.pyを引数なしで実行しない。読了前にそのフェーズの作業へ進まない。作業単位が終わるたびにchecklist_manager.py checkでチェックを入れる。

最終出力はcontext.mdの指定どおり、deck_source.json、PPTX、code_interpreter_log.md、task_checklist.mdのリンクを提示する。
