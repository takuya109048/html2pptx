# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。詳細本文はcontext_data.jsonへ分離し、このファイルは作業フェーズ判定とcode interpreterでの詳細コンテキスト取得に責任を持つ。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }
Codexなどfile searchがない環境では、ローカルファイルのcontext.mdを毎ターン読み直して同じ前提にする。

code interpreter基本:
出力先はDECK_FROM_SOURCE_OUTPUT_DIR、なければ/mnt/data、どちらもなければ現在の作業ディレクトリにする。Codexではこの出力先に成果物とログを置く。code本文の先頭には、何を実行するかが分かる短い日本語コメントを置く。

作業計画チェックリスト:
ターンBで生成作業に入る前に、checklist_manager.py init yesまたはinit noを実行し、出力先にtask_checklist.mdを作成する。チェックリストには作業項目ID、対応フェーズ、読むべきcontext_loader.pyフェーズ、完了条件を入れる。チェックリストは手編集しない。進捗確認、次項目取得、完了チェック、検証はchecklist_manager.pyで行う。
layout確定後は、slides配列を保存したdeck_source.jsonを指定してchecklist_manager.py insert-slidesを実行し、P03-T01直後へ各スライドのサブチェックリストを挿入する。サブ項目は、スライドごとにimage、body、emphasis、notesのような分割コンテキスト単位で並べる。サブ項目も手編集せず、status、next、check、verifyの対象にする。

進捗確認:
各フェーズ直前にchecklist_manager.py statusまたはnextを実行し、現在位置と次に読むコンテキストIDを確認する。statusとnextの出力は800文字以内で、完了数、次の1件、ctx、DONE/NEXTだけを短く表示する。表示されたctxをcontext_loader.py start ctxで開始し、nextを1回ずつ実行してDONEまで読む。DONE前に作業へ進まない。迷った場合、後続フェーズへ移る場合、修復ループに入る場合も必ずstatusを確認する。

チェック更新:
各作業単位の完了後にchecklist_manager.py check 項目IDを実行する。checkはtask_checklist.mdの該当行を[x]にし、code_interpreter_log.mdへフェーズ、項目ID、結果を追記する。最終変換後にchecklist_manager.py verifyを実行し、未完了、重複ID、ctx欠落、出力800文字超過がないことを確認する。

実行ログ:
すべてのcode interpreter呼び出しで出力先のcode_interpreter_log.mdへ追記する。記録項目はタイムスタンプ、作業フェーズ、目的、入力、出力、結果、NEXT/DONEまたはエラー概要である。秘密情報、APIキー、不要な内部パス詳細は書かない。context_loader.pyはstart、next、status、validate時に自動でログを追記する。変換コードや独自検証コードにもログ追記を含める。最終リンクにはdeck_source.json、pptx、code_interpreter_log.md、task_checklist.mdを必ず出す。

ログ制限:
長いコンテキストを一括printしない。context_loader.pyは1回に1チャンクだけ出す。複数チャンクを読む時は1回ずつcode interpreterを実行する。続きの取得コードの冒頭コメントには、前回NEXT値を含む短い進捗文を書く。

外部JSON:
context_data.json本体を直接開いて読まない。ターン冒頭で全フェーズを一括読み込みしない。各作業フェーズの直前に、そのフェーズだけをstartし、nextを1回ずつ実行してDONEまで読む。DONE後にそのフェーズの作業だけを行う。

生成フェーズ:
Yesの場合は次の順で読む。
yes_plan: ソース分析、保存名、構成フレーム、密度方針を決める直前。
yes_schema: root、summary、slides、JSON骨格を書く直前。
yes_layout: layoutと必須blocksを選ぶ直前。
yes_image: nanobanana2用のimage_prompt、icon_promptを作る直前。
yes_body: blocks本文の密度と表現を作る直前。
yes_emphasis: 太字スキムラインと強調表現を入れる直前。
yes_notes: speaker noteを書く直前。
yes_check_convert: FINAL_SELF_CHECKとPPTX変換の直前。

Noの場合は次の順で読む。
no_plan: ソース分析、保存名、構成フレーム、密度方針を決める直前。
no_schema: root、summary、slides、JSON骨格を書く直前。
no_layout: layoutと必須blocksを選ぶ直前。
no_body: blocks本文の密度と表現を作る直前。
no_emphasis: 太字スキムラインと強調表現を入れる直前。
no_notes: speaker noteと文字化け確認を書く直前。
no_check_convert: FINAL_SELF_CHECKとPPTX変換の直前。

修復フェーズ:
repair_emphasis: strict-emphasis、太字不足、弱い太字、スキムライン失敗を直す直前。
repair_density: strict-density、本文不足、noteだけ厚い、カードが薄い時に直す直前。
repair_text: 文字化け、markup、title、section、block key、JSON構造エラーを直す直前。
setup: /mnt/dataに実行ファイル群が見つからない時に読む。

取得方法:
最初の取得ではcode interpreterでresolve_uploads.pyを実行したうえで、必要に応じてchecklist_manager.pyとcontext_loader.pyを/mnt/dataへコピーし、context_loader.py start フェーズ名をsubprocessで実行する。Codexではshellで同じstart/nextを実行してよい。続きはcontext_loader.py nextを1回につき1回だけ実行する。ループでまとめて実行しない。出力先頭の[ctx 現在/総数 chunk_id]で進捗を確認する。出力末尾がNEXTなら次を読む。次回codeコメントにはそのNEXT値を写し、短い進捗文にする。出力末尾がDONEならそのフェーズは読み切り完了である。

停止条件:
その作業フェーズがDONEになるまで、当該フェーズの分析、生成、変換、検証へ進まない。読み取り途中でユーザーへ分析メモや構成案を出さない。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。生成作業の前にchecklist_manager.py init yesまたはinit noでtask_checklist.mdを作る。layout確定後にinsert-slidesでスライド単位のサブチェックリストを挿入する。以後は1枚ずつ、チェックリスト確認、直前読み込み、対象スライドだけの作業、チェック更新を交互に進める。思考過程、分析メモ、構成案はユーザーに出さない。リンク提示まで1ターンで完了する。

生成時の内部順序:
1. checklist_manager.py initでtask_checklist.mdを作り、statusで先頭項目を確認する。
2. planフェーズをDONEまで読み、ソース分析と全体構成を決め、該当項目をcheckする。
3. schemaフェーズをDONEまで読み、root、summary、slides骨格を書き、該当項目をcheckする。
4. layoutフェーズをDONEまで読み、各スライドのlayoutとblocksを確定し、該当項目をcheckする。
5. slides配列を一時保存し、checklist_manager.py insert-slides deck_source.jsonを実行して、分割コンテキスト単位のサブ項目をP03-T01直後に挿入する。
6. statusで次のS001-I01、S001-B01、S001-E01、S001-N01などを確認する。表示されたctxだけをDONEまで読み、対象スライドの該当作業だけを行い、該当S項目をcheckする。
7. 同じスライドの最後のS項目をcheckするまで次のスライドへ進まない。すべてのS項目が完了するまで、1枚ずつ、かつコンテキスト単位ごとに同じ手順を繰り返す。
8. check_convertフェーズをDONEまで読み、FINAL_SELF_CHECK後にstrict変換し、verifyする。
9. strictエラーが出たら、status確認後に該当repairフェーズをDONEまで読み、JSONを修復して再実行し、修復項目をcheckする。

変換出力:
check_convertフェーズをDONEまで読んでから、deck_source_to_json.pyをstrict系オプション付きで実行する。ユーザーへ提示するのはdeck_source.json、pptx、code_interpreter_log.md、task_checklist.mdである。slides.jsonは中間生成物として扱い、ダウンロードリンクを出さない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとcontext_loader.py validateで検証する。
