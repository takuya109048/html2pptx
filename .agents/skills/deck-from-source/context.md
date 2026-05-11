# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。詳細ルール本文はcontext_data.jsonへ分離している。AIはこのファイルで作業フェーズを判定し、各作業の直前に必要な詳細だけをcontext_loader.pyで1件ずつ読み切ってから作業する。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }
Codexなどfile searchがない環境では、ローカルファイルのcontext.mdを毎ターン読み直して同じ前提にする。

code interpreter基本:
出力先はDECK_FROM_SOURCE_OUTPUT_DIR、なければ/mnt/data、どちらもなければ現在の作業ディレクトリにする。Codexではこの出力先に成果物とログを置く。resolve_uploads.pyをglobで探して実行し、assistant-任意ID-元ファイル名を元ファイル名へコピーする。
code本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。秘密情報や長い仕様説明は書かない。

実行ログ:
すべてのcode interpreter呼び出しで出力先のcode_interpreter_log.mdへ追記する。記録項目はタイムスタンプ、作業フェーズ、目的、入力、出力、結果、NEXT/DONEまたはエラー概要である。秘密情報、APIキー、不要な内部パス詳細は書かない。context_loader.pyはstart、next、status、validate時に自動でログを追記する。変換コードや独自検証コードにもログ追記を含める。最終リンクにはdeck_source.json、pptx、code_interpreter_log.mdを必ず出す。

ログ制限:
カスタムGPTsのcode interpreterログは先頭400文字と末尾400文字の合計800文字だけが安定してAIへ渡る。長いコンテキストを一括printしない。context_loader.pyは1回に1チャンクだけ出す。複数チャンクを読む時は1回ずつcode interpreterを実行する。
続きの取得コードの冒頭コメントは固定文にしない。前回出力末尾がNEXT 004/006なら、次のcodeコメントにも004/006を入れる。

外部JSON:
context_data.jsonは800文字以内の個別コンテキスト片を持つ。AIはターン冒頭で全フェーズを一括読み込みしない。context_data.json本体を直接開いて読まない。各作業フェーズの直前に、そのフェーズだけをstartし、nextを1回ずつ実行してDONEまで読む。DONE後にそのフェーズの作業だけを行い、次工程へ移る前に次工程用フェーズを読み直す。先の工程を、前工程で読んだ情報だけで先取りしない。

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
最初の取得ではcode interpreterでresolve_uploads.pyを実行したうえで、context_loader.py start フェーズ名をsubprocessで実行する。Codexではshellで同じstart/nextを実行してよい。続きはcontext_loader.py nextを1回につき1回だけ実行する。ループでまとめて実行しない。出力先頭の[ctx 現在/総数 chunk_id]で進捗を確認する。出力末尾がNEXTなら次を読む。次回codeコメントにはそのNEXT値を写す。出力末尾がDONEならそのフェーズは読み切り完了である。

停止条件:
その作業フェーズがDONEになるまで、当該フェーズの分析、生成、変換、検証へ進まない。読み取り途中でユーザーへ分析メモや構成案を出さない。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。上記の生成フェーズ順に、直前読み込みと作業を交互に進める。思考過程、分析メモ、構成案はユーザーに出さない。リンク提示まで1ターンで完了する。

生成前の最低条件:
root.titleは日本語の表紙タイトルにする。保存名は短い英語slugにする。
root.summaryは必須である。
既存のgeneratedやtmp_deckのjson/pptxを叩き台として流用しない。必要なら検証比較にだけ使い、今回の原文からdeck_source.jsonを新規生成する。
slides配列には本文スライドだけを書く。表紙、サマリー、目次は入れない。
slides.titleは目次小見出しであり、名詞句か体言止めにする。主張や示唆はmessageへ移す。
layoutごとの必須blocks名を守る。独自keyは作らない。
nanobanana2 Yesでは本文slidesにplain_1colを使わない。
Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

生成時の内部順序:
1. planフェーズをDONEまで読み、ソース分析と全体構成を決める。
2. schemaフェーズをDONEまで読み、root、summary、slides骨格を書く。
3. layoutフェーズをDONEまで読み、各スライドのlayoutとblocksを確定する。
4. Yesの場合だけimageフェーズをDONEまで読み、画像プロンプトを作る。
5. bodyフェーズをDONEまで読み、表示本文を厚くする。
6. emphasisフェーズをDONEまで読み、太字スキムラインを入れる。
7. notesフェーズをDONEまで読み、speaker noteを作る。
8. check_convertフェーズをDONEまで読み、FINAL_SELF_CHECK後にstrict変換する。
9. strictエラーが出たら、該当repairフェーズをDONEまで読み、JSONを修復して再実行する。

変換出力:
ユーザーへ提示するのはdeck_source.json、pptx、code_interpreter_log.mdである。slides.jsonは中間生成物として扱い、ダウンロードリンクを出さない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとvalidate_context_json.pyで検証する。
