# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。詳細ルール本文はcontext_data.jsonへ分離している。AIはこのファイルでフェーズを判定し、必要な詳細をcontext_loader.pyで1件ずつ読み切ってから作業する。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }

code interpreter初回:
resolve_uploads.pyをglobで探して実行し、assistant-任意ID-元ファイル名を元ファイル名へコピーする。以降は/mnt/data/元ファイル名で参照する。

ログ制限:
カスタムGPTsのcode interpreterログは先頭200文字と末尾200文字の合計400文字だけが安定してAIへ渡る。400文字を超えた中間は省略される前提で扱う。長いコンテキストを一括printしない。context_loader.pyは1回に1チャンクだけ出す。AIは複数チャンクを読む時、1回ずつcode interpreterを実行する。

外部JSON:
context_data.jsonは400文字以内の個別コンテキスト片を持つ。通常は本文300文字以内に分割され、loaderのヘッダーとNEXTまたはDONEを含めても400文字以内で出力される。

テンプレートカタログ:
本文slideはlayoutとblocksを直接書かず、slide_kind、variant:auto、slotsを優先してよい。deck_source_to_json.pyがtemplate_catalog.jsonを使い、全テンプレート候補からスロット充実度、表やKPIの形、結論有無、nanobanana2可否で具体layoutをスコア選択する。必要な時だけtemplate_catalog_loader.py listまたはget 種別名で短い説明を読む。

フェーズ:
turn_b_yes: nanobanana2 Yesで生成する時に読む。
turn_b_no: nanobanana2 Noで生成する時に読む。
repair_emphasis: strict-emphasis、太字不足、弱い太字、スキムライン失敗を直す時に読む。
repair_density: strict-density、本文不足、noteだけ厚い、カードが薄い時に読む。
repair_text: 文字化け、markup、title、section、block key、JSON構造エラーを直す時に読む。
setup: /mnt/dataに実行ファイル群が見つからない時に読む。

取得方法:
ターンBではDECK_SOURCE_JSONを書く前に必ず該当フェーズをstartする。Yesならturn_b_yes、Noならturn_b_noを指定する。

最初の取得:
code interpreterでresolve_uploads.pyを実行したうえで、context_loader.py start フェーズ名をsubprocessで実行する。

続きの取得:
context_loader.py nextを1回のcode interpreter実行につき1回だけ実行する。ループでまとめて実行しない。出力末尾がNEXTなら次を読む。出力末尾がDONEならそのフェーズは読み切り完了である。

停止条件:
必要フェーズがDONEになるまで、ソース分析、構成決定、DECK_SOURCE_JSON生成、PPTX変換へ進まない。読み取り途中でユーザーへ分析メモや構成案を出さない。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。該当フェーズをDONEまで読み、内部でソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

生成前の最低条件:
root.titleは日本語の表紙タイトルにする。保存名は短い英語slugにする。
root.summaryは必須である。
slides配列には本文スライドだけを書く。表紙、サマリー、目次は入れない。
slides.titleは目次小見出しであり、名詞句か体言止めにする。主張や示唆はmessageへ移す。
layout形式ではlayoutごとの必須blocks名を守る。slide_kind形式ではslotsに必要な本文を置く。独自keyは作らない。
nanobanana2 Yesでは本文slidesにplain_1colを使わない。
Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

生成時の内部順序:
1. 詳細コンテキストをDONEまで読む。
2. 原文を詳細原稿へ内部展開する。ただし原文にない固有数値、事例名、実績、専門用語は作らない。
3. スライド構成とsectionを決める。本文スライドが4枚以上なら、全sectionが1枚ずつで終わる構成にしない。
4. 各スライド本文を書く前に太字スキムラインを内部設計する。
5. DECK_SOURCE_JSONを書く。
6. FINAL_SELF_CHECK相当の目視点検を行い、必要なら本文を直す。
7. deck_source_to_json.pyをstrict系オプション付きで実行する。
8. strictエラーが出たら、該当repairフェーズをDONEまで読み、JSONを修復して再実行する。

変換出力:
ユーザーへ提示するのはdeck_source.jsonとpptxだけである。slides.jsonは中間生成物として扱い、ダウンロードリンクを出さない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとvalidate_context_json.pyで検証する。
