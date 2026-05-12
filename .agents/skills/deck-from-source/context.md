# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。詳細本文とフェーズ順はcontext_loader.pyが管理する。context.mdだけを読んだ状態では、スライド構成、章立て、枚数、保存名、JSON骨格を決めない。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }
Codexなどfile searchがない環境では、ローカルファイルのcontext.mdを毎ターン読み直して同じ前提にする。

チャット冒頭の初期化:
Custom GPTsでは、最初のcode interpreter実行でresolve_uploads.pyを探して実行する。以後は/mnt/data/{元ファイル名}で安定して参照する。
コード本文の先頭コメントは「アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行します。」のように短く書く。

code interpreter基本:
出力先はDECK_FROM_SOURCE_OUTPUT_DIR、なければ/mnt/data、どちらもなければ現在の作業ディレクトリにする。成果物とcode_interpreter_log.mdはこの出力先に置く。code本文の先頭には、何を実行するかが分かる短い日本語コメントを置く。

ログ:
すべてのcode interpreter呼び出しで出力先のcode_interpreter_log.mdへ追記する。記録項目はタイムスタンプ、作業フェーズ、目的、入力、出力、結果、NEXT/DONEまたはエラー概要である。秘密情報、APIキー、不要な内部パス詳細は書かない。context_loader.pyは自動でログを追記する。変換コードや独自検証コードにもログ追記を含める。最終リンクにはdeck_source.json、pptx、code_interpreter_log.mdを必ず出す。

コンテキスト取得:
context_data.json本体を直接開いて読まない。ターン冒頭で全フェーズを一括読み込みしない。番号指定、chunk_id指定は禁止である。
同じターン内でcode interpreter呼び出しを複数回に分け、1チャンクずつ取得することは正しい。禁止なのは、1つのcode interpreterコード本文の中でループ、関数、複数のsubprocess.run、複数のexecなどを使ってローダーを2回以上起動することである。1つのcode interpreterコード本文には、コンテキストを出すローダーコマンドを1回だけ書く。

公開コマンドは次だけである。
init yes
init no
advance <ACK>
phase-done <ACK>
repair emphasis
repair density
repair text
setup
repeat
status
validate

read、start、next、get、フェーズ名の直接指定は旧APIであり使わない。旧APIが必要に見えても使わず、必ずinitまたはadvanceへ戻る。

取得手順:
Yes方針ならcontext_loader.py init yesを1回だけ実行する。No方針ならcontext_loader.py init noを1回だけ実行する。実行すると現在フェーズの最初の1チャンクだけが出る。
出力末尾がNEXT 002/006 ACK xxxxxxxxなら、そのcode interpreter実行を終える。次のcode interpreter実行でcontext_loader.py advance xxxxxxxxを1回だけ実行する。
出力末尾がDONE 006/006 ACK xxxxxxxxなら、そのフェーズの読み取りは完了である。すぐ次を読まず、そのフェーズの作業だけを行う。作業が終わった後、次フェーズへ入る直前にcontext_loader.py phase-done xxxxxxxxを1回だけ実行する。
phase-doneは次フェーズの最初の1チャンクだけを返す。以後はNEXTならadvance、DONEなら作業、作業後にphase-doneを繰り返す。
ROUTE_DONEが出たら全フェーズの読み取りは完了である。
ACKはstateファイルに平文保存されない。出力を見失った場合だけrepeatを使い、新しいACKを再発行する。statusは現在位置だけを確認するために使い、ACK取得には使わない。

停止条件:
その作業フェーズがDONEになるまで、当該フェーズの分析、生成、変換、検証へ進まない。特にplan相当フェーズのDONE前に、スライド構成、章立て、枚数、保存名を作らない。読み取り途中でユーザーへ分析メモや構成案を出さない。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。context_loader.pyの状態機械に従い、読み取りと作業を交互に進める。思考過程、分析メモ、構成案はユーザーに出さない。リンク提示まで1ターンで完了する。

生成時の内部順序:
1. init yesまたはinit noで開始し、plan相当フェーズをDONEまで読む。
2. plan相当フェーズの作業として、ソース分析、保存名、全体構成、密度方針を決める。
3. phase-doneで次フェーズへ進み、schema、layout、Yes時のimage、body、emphasis、notes、check_convert相当の各フェーズを、DONEまで読む、作業する、phase-doneする、の順で進める。
4. check_convert相当フェーズをDONEまで読んでから、FINAL_SELF_CHECK後にstrict変換する。
5. strictエラーが出たら、repair emphasis、repair density、repair textのうち該当するものを開始し、DONEまで読んでからJSONを修復して再実行する。

変換出力:
check_convert相当フェーズをDONEまで読んでから、deck_source_to_json.pyを--require-context-doneとstrict系オプション付きで実行する。ユーザーへ提示するのはdeck_source.json、pptx、code_interpreter_log.mdである。slides.jsonは中間生成物として扱い、ダウンロードリンクを出さない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとcontext_loader.py validateで検証する。
