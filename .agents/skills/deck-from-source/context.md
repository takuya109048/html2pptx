# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。詳細ルール本文はcontext_data.jsonへ分離している。AIはこのファイルでフェーズを判定し、必要な詳細をcontext_loader.pyで1件ずつ読み切ってから作業する。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }

code interpreter初回:
resolve_uploads.pyをglobで探して実行し、assistant-任意ID-元ファイル名を元ファイル名へコピーする。以降は/mnt/data/元ファイル名で参照する。
code interpreterに渡すcode本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。GUIのアクティビティに表示されるため、ユーザーが安心して確認できる粒度にし、秘密情報や長い仕様説明は書かない。

ログ制限:
カスタムGPTsのcode interpreterログは先頭400文字と末尾400文字の合計800文字だけが安定してAIへ渡る。800文字を超えた中間は省略される前提で扱う。長いコンテキストを一括printしない。context_loader.pyは1回に1チャンクだけ出す。AIは複数チャンクを読む時、1回ずつcode interpreterを実行する。
続きの取得コードの冒頭コメントは固定文にしない。前回出力末尾がNEXT 004/031なら、次のcodeコメントにも004/031を入れ、GUIアクティビティだけでも進捗が分かるようにする。

外部JSON:
context_data.jsonは800文字以内の個別コンテキスト片を持つ。code interpreter呼び出し回数を減らすため、loaderの進捗ヘッダーとNEXTまたはDONEを含めても800文字以内に収まる範囲で、できるだけ800文字に近づけて分割する。

フェーズ:
turn_b_yes: nanobanana2 Yes回答直後の読込専用ターンで読む。
turn_b_no: nanobanana2 No回答直後の読込専用ターンで読む。
repair_emphasis: strict-emphasis、太字不足、弱い太字、スキムライン失敗を直す時に読む。
repair_density: strict-density、本文不足、noteだけ厚い、カードが薄い時に読む。
repair_text: 文字化け、markup、title、section、block key、JSON構造エラーを直す時に読む。
setup: /mnt/dataに実行ファイル群が見つからない時に読む。

取得方法:
ターンBではDECK_SOURCE_JSONを書かず、必ず該当フェーズをstartする。Yesならturn_b_yes、Noならturn_b_noを指定する。

最初の取得:
code interpreterでresolve_uploads.pyを実行したうえで、context_loader.py start フェーズ名をsubprocessで実行する。

続きの取得:
context_loader.py nextを1回のcode interpreter実行につき1回だけ実行する。ループでまとめて実行しない。出力先頭の[ctx 現在/総数 chunk_id]で進捗を確認する。出力末尾がNEXTなら次を読む。次回codeコメントにはそのNEXT値を写す。出力末尾がDONEならそのフェーズは読み切り完了である。

停止条件:
必要フェーズがDONEになるまで、ソース分析、構成決定、DECK_SOURCE_JSON生成、PPTX変換へ進まない。読み取り途中でユーザーへ分析メモや構成案を出さない。DONE後も同じターンでは生成へ進まず、「詳細コンテキストを読み切ったので、次のターンで生成します」とだけ短く返す。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを保持したまま、該当フェーズの詳細コンテキスト読込だけを行う。Yesならturn_b_yes、Noならturn_b_noをDONEまで読む。DONEになったら生成へ進まず、読了した方針を会話上に残して「次のターンで生成します」と短く返す。

ターンC:
直前のアシスタント返答がturn_b_yesまたはturn_b_noのDONE読了報告なら、分割コンテキストを再読込しない。前々ターンの原文ソース、Yes/No方針、直前ターンで会話に展開済みの詳細コンテキストを使い、内部でソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで完了する。新しいソース、方針変更、読了不足、修復フェーズが必要な場合だけcontext_loader.pyを再実行する。思考過程、分析メモ、構成案はユーザーに出さない。

生成前の最低条件:
root.titleは日本語の表紙タイトルにする。保存名は短い英語slugにする。
root.summaryは必須である。
slides配列には本文スライドだけを書く。表紙、サマリー、目次は入れない。
slides.titleは目次小見出しであり、名詞句か体言止めにする。主張や示唆はmessageへ移す。
layoutごとの必須blocks名を守る。独自keyは作らない。
layoutは見た目や収まりで先に決めない。原文を単一説明、比較、同格要素、時系列、背景と論点、根拠と結論、表、マトリックス、工程と観点へ分類してから選ぶ。
原文の章順、因果順、結論位置を最優先する。発表フレームや密度補強のために、原文の主従関係やストーリー順を入れ替えない。
各スライドは対象アンカーを内部で1つ決め、title、message、blocks、noteで説明対象がずれないようにする。独自keyは作らない。
sectionとconclusionは単なるラベルにせず、発表者がスライドを見ながら話せる短い原稿ブロックとして厚めに書く。
nanobanana2 Yesでは本文slidesにplain_1colを使わない。
Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

生成時の内部順序:
1. 直前ターンで該当フェーズがDONEまで読了済みであることを確認する。未読了なら生成せず読込ターンへ戻る。
2. 原文アウトラインを内部で作り、見出し、段落、表、箇条書き、結論を出現順に並べる。
3. 原文アウトラインからスライド構成、section、各スライド候補の情報構造を決めてからlayoutを選ぶ。本文スライドが4枚以上なら、隣接項目だけを束ねてsectionを作る。
4. 各スライドの対象アンカーを決め、blocks本文に具体的な主語を残す。noteは詳細原稿から直接作らず、最終blocksを正本にして最後に同期生成する。
5. 各スライド本文を書く前に太字スキムラインを内部設計する。
6. DECK_SOURCE_JSONを書く。
7. 原文アウトラインとslidesの対応を内部照合し、順序、主従、結論位置、削除された重要論点を点検する。
8. deck_source_to_json.pyをstrict系オプション付きで実行する。
9. strictエラーが出たら、該当repairフェーズをDONEまで読み、JSONを修復して再実行する。

変換出力:
ユーザーへ提示するのはdeck_source.jsonとpptxだけである。slides.jsonは中間生成物として扱い、ダウンロードリンクを出さない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとvalidate_context_json.pyで検証する。
