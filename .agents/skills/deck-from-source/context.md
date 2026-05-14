# context.md deck-from-source 司令塔兼コンテキスト保存領域

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。司令塔であると同時に、通常生成に必要な主要ルールの保存領域でもある。通常のdeck_source.json生成はこのcontext.mdだけで完結させ、context_data.jsonの読み取りは例外、修復、詳細確認が必要な時だけ使う。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }

上限:
context.mdは18000文字以内に収める。SKILL.mdは5000文字以内に収める。context.mdには、毎回必要な前提、生成判断、JSON構造、layout選択、密度、太字、自己点検を置く。context_data.jsonには、読み直しが発生しても痛みが小さい補助ルール、修復ループ、例外対応、セットアップ手順だけを置く。

code interpreter初回:
resolve_uploads.pyをglobで探して実行し、assistant-任意ID-元ファイル名を元ファイル名へコピーする。以降は/mnt/data/元ファイル名で参照する。code本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。GUIのアクティビティに表示されるため、秘密情報や長い仕様説明は書かない。

外部JSONの扱い:
context_data.jsonは通常生成で必読にしない。context.mdだけでは判断できない厳密修復、strictエラーの再発、実行ファイル配置の不足が起きた時にだけ読む。読む場合はcontext_loader.py start phase、続けてnextを1回ずつ実行し、DONEまで読む。1回のcode interpreter実行でloaderを2回以上起動しない。出力先頭の[ctx 現在/総数 chunk_id]と末尾のNEXTまたはDONEを確認する。続きのcodeコメントには直前のNEXT値を写す。

利用フェーズ:
turn_b_yes: context.mdで足りない時だけ、nanobanana2 Yes生成の補助を読む。
turn_b_no: context.mdで足りない時だけ、nanobanana2 No生成の補助を読む。
repair_emphasis: strict-emphasis、太字不足、弱い太字、スキムライン失敗を直す時に読む。
repair_density: strict-density、本文不足、noteだけ厚い、カードが薄い時に読む。
repair_text: 文字化け、markup、title、section、block key、JSON構造エラーを直す時に読む。
setup: /mnt/dataに実行ファイル群が見つからない時に読む。

ターン判定:
ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。context.mdのルールで内部的にソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、リンク提示まで完了する。思考過程、分析メモ、構成案はユーザーに出さない。context_data.jsonは、context.mdだけでは修復不能な時だけ読む。

生成対象:
AIが作るのはdeck_source.jsonだけである。Markdownデッキ、メタテーブル、フェンス、HTML改行タグは作らない。
slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。
ユーザーへ提示するリンクはdeck_source.jsonとpptxだけである。slides.jsonは中間生成物として扱い、リンクを出さない。

root:
titleは表紙タイトル。日本語で書き、英語は固有名詞や略語だけにする。20字前後を目安にし、長い説明、対象者、用途、補足条件はsubtitleへ逃がす。
subtitleは表紙サブタイトル。不要なら空文字。
affiliationは推定できなければCodex Working Deck。
presenterは推定できなければTakuya。
dateはYYYY-MM-DD。
noteは表紙の発表者ノート。
summaryは必須。目次の前に置かれるサマリー結論スライドである。
slidesは本文スライド配列。表紙、サマリー、目次は含めない。

summary:
titleは原則サマリー（結論）。
messageは結論を先に読むための短い補足。
noteは発表者読み上げ原稿。
blocks.card-aは表示本文。必ず###見出しから始め、結論、判断軸、次の行動が分かる長めの本文にする。
nanobanana2 Yesの場合だけimage_promptを必須にする。スライド全体を図解する主図用の日本語プロンプトを書き、必ず6:5を明記する。Noの場合はimage_promptを書かない。

ストーリー設計:
1. ソース全体から聴衆に最も伝えたい1文を内部で定義する。
2. 目的に応じてSDS、PREP、DESC、序論本論結論、AIDMAのいずれかを選び、セクションへ分ける。
3. 主張、根拠、データ、事例、手順、並列要素、結論を抽出する。
4. 各スライドは対象アンカーを内部で1つ決める。title、message、blocks、noteで説明対象がずれないようにする。
5. 原文にない固有数値、事例名、実績、専門用語は作らない。不足する説明は背景、理由、含意、比較、注意点、判断基準として一般化して補う。

titleとsection:
slides.titleは目次小見出しである。名詞句か体言止めにし、主張や示唆はmessageへ移す。汎用語だけにせず、固有語、数値、対比軸、判断軸、行動対象のいずれかを含める。
slides.sectionは目次の大見出しである。同じsectionを連続する2から4枚で再利用し、その下に複数の本文スライドを置く。本文スライドが4枚以上なら、全sectionが1枚ずつで終わる構成にしない。
sectionとconclusionは単なるラベルにしない。発表者がスライドを見ながら話せる短い原稿ブロックとして、対象、状況、なぜ今見るか、判断、理由、次の行動のうち必要な要素を含める。

layout選択:
layoutは見た目や収まりで先に決めない。原文を単一説明、2対象比較、同格3要素、3/4段階の時系列、背景+3論点、1起点から3方向、3根拠から1結論、表、表+示唆、2軸マトリックス、工程×観点へ分類してから選ぶ。分類が決まるまでlayout名を書かない。

使用可能layoutと必須blocks:
plain_1col: 単一説明。必須blockはcard-a。nanobanana2 Yesでは本文スライドに使わない。
plain_2col: 2概念、または本文とnanobananaプロンプト。必須blockはcard-a, card-b。
list_3card: 順序を入れ替えても壊れない同格3要素。必須blockはcard-a, card-b, card-c。
flow_3step: 前後関係を持つ3工程。必須blockはstep-a, step-b, step-c。
flow_4step: 前後関係を持つ4工程。必須blockはstep-a, step-b, step-c, step-d。
compare_2col: 2対象の比較。必須blockはleft, right。
table_basic: 表形式の整理。必須blockはtable。
table_conclusion: 表から示唆を読む。必須blockはtable, conclusion。
matrix_2x2: 2軸整理。必須blockはaxis-x, axis-y, q1, q2, q3, q4。
bg_3card: 背景と3論点。必須blockはsection, card-a, card-b, card-c。
diffuse_3card: 1つの起点から3方向へ展開。必須blockはsection, card-a, card-b, card-c。
converge_3card: 3根拠から1結論へ収束。必須blockはcard-a, card-b, card-c, conclusion。

layoutハードゲート:
flow系は順序、前後関係、完了条件、次工程への接続のうち2つ以上がある時だけ使う。3/4項目が並ぶだけなら禁止。
list_3cardは各カードが同格で、順序を入れ替えても意味が壊れない時に使う。
compare_2colは同じ観点で2対象を比べられる時だけ使う。
matrix_2x2は2軸の意味が明確で、4象限の違いを説明できる時だけ使う。
tableは項目数が多い時の逃げにしない。表から読む示唆があるならtable_conclusionにする。

nanobanana2 Yes:
slides配列の各スライドは画像生成導線を持つ。plain_2colではblocks.card-bにnanobananaプロンプトを置く。card系またはflow系では各カードやstepにicon_promptを置く。
本文スライドにplain_1colを使わない。
plain_image_col、image_label_1、画像プレースホルダーは使わない。
blocks.card-bへ「### nanobananaプロンプト」に続けて、フェンスなしで日本語プロンプトを書く。CreateやGenerateなどの英語文で始めない。
プロンプトには6:5、白背景、資料向けフラット図解、外周3から5%の安全余白だけ、キャンバス全体を密に使う、上下左右の大きな空白やレターボックスを作らない、を含める。
抽象語だけにせず、人物、画面、書類、矢印、付箋、表、グラフなど具体的な構成要素を3から6個指定する。
画像内文字は短い日本語ラベルだけにする。本文を画像内に入れない。
アイコンプロンプトは同じサイズ、同じ余白、同じ色調、同じ視点にする。

本文密度:
plain_1colはリード1文と4から5項目、本文140字以上。
plain_2colはリード1文と3から4項目、各列115字以上。片側が画像プロンプトの場合は本文側を厚めにする。
list_3cardは各カードに対象名、リード1文、2から3項目。各カード58字以上。
diffuse_3card、bg_3card、flow_3stepはsectionを80から140字の視線アンカーにし、各カードまたはstepにリード1文と2から3項目。各カード58字以上。
converge_3cardは各カードにリード1文と2項目まで。conclusionは判断、理由、次行動を含める。
flow_4stepは短いリードと1から2項目。各step40字以上。
table、matrix、compareは単語だけにしない。各セルは意味のある句にする。
箇条書きは原則20から38字程度にする。カード本文が名詞句だけで終わる場合は、判断基準、注意点、影響、次の行動を戻す。

太字スキムライン:
太字は後付け装飾ではなく、スライド本文の第二要約線として先に設計する。
1. 各スライドで、太字だけを左上から右下へ読んだ時の1文要約を内部で作る。
2. その要約をsection、card、step、plain、conclusionの本文へ分散して埋め込む。
3. 太字だけを抽出し、何が問題で、何を判断し、次に何をするかが分かるか確認する。
4. 分からない場合は太字だけを増やさず、本文そのものを判断軸、制約、行動、結論が見える文へ書き換える。
1スライド全体で3から7個程度を目安にする。plain_2colでcard-bが画像プロンプトの場合はcard-a側だけで2語句以上を確保する。
各語句は2から16字程度を基本にし、長くても24字以内にする。
太字が「重要」「ポイント」「背景」「結論」だけになるのは禁止。各blockの太字を同じ言葉にしない。

speaker notes:
noteは最終blocksを正本にして最後に同期生成する。詳細原稿から直接noteを作らない。
noteは発表者が読める自然な口語寄りの原稿にする。blocksにない新情報や固有数値を足さない。
titleとmessageで説明対象を確認し、sectionがある場合は対象、状況、なぜ見るかを1から2文で受ける。cardやstepの順に沿って、表示本文を読み上げやすい文へ変換する。最後にconclusionまたはmessageの判断を短く戻す。

自己点検:
DECK_SOURCE_JSONを書いた直後に目視で短く点検し、問題があればblocks本文を直接直してからPPTX変換へ進む。
rootにtitle、date、summary、slidesがあるか。
summary.blocks.card-aが長めの結論本文になっているか。Yesならsummary.image_promptに6:5があるか。Noなら4項目以上のMarkdown構造があるか。
slides配列に表紙、サマリー、目次を入れていないか。
各slideに対象アンカーがあり、title、message、blocks、noteで説明対象がずれていないか。
slides.titleが空、重複、主張文、長い説明文、汎用語だけでないか。
layoutごとの必須blocksがそろっているか。独自keyを作っていないか。
blocks本文が短い名詞句だけになっていないか。noteに理由、背景、注意点が入っているのに本文が薄い場合は、noteから判断材料を抜き出してblocksへ戻す。
文字化け、????、Unicode replacement character、Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグが混じっていないか。
表紙titleが日本語かつ20字前後に収まり、長い補足がsubtitleへ分離されているか。

strictエラー時:
strict-emphasisで太字不足や弱い太字のエラーが出たら、repair_emphasisをDONEまで読み、該当slideのblocks本文を直してから再変換する。
strict-densityや本文不足が出たら、repair_densityをDONEまで読む。noteではなくblocksへ判断材料を戻す。
markup、title、section、block key、JSON構造、文字化けのエラーが出たら、repair_textをDONEまで読む。
実行ファイルが/mnt/dataに見つからない時だけsetupを読む。

PPTX変換:
DECK_SOURCE_JSONを確定したら、code interpreterでJSON保存と変換を実行する。TITLE_SLUGはファイル名専用であり、表紙に出るroot.titleは日本語のままにする。変換コマンドには--require-agenda、--strict-blocks、--strict-density、--strict-agenda-grouping、--strict-markup、--strict-emphasis、--strict-compact-blocks、--strict-title-style、--strict-text-integrityを付ける。nanobanana2 Yesの場合だけ--nanobanana2を付ける。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとvalidate_context_json.pyで検証する。
