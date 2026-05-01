# context.md deck-from-source JSON詳細ルール

目的:
原文ソースから、安定したdeck_source.jsonとPPTXを1ターンで生成するための詳細ルールである。Markdownデッキ形式は廃止する。SKILL.mdは短い実行指示、このファイルは毎ターンfile searchで読み込む詳細仕様として使う。

全体フロー:
1. ターンAではソースを受け取っても分析や生成を始めず、nanobanana2画像を使うかYesまたはNoで確認する。
2. ターンBではソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、ダウンロードリンク提示まで完了する。
3. ユーザーにスライド枚数、発表者名、対象者を追加質問しない。必要ならソースから推定し、不明部分は自然な汎用値で補う。
4. slides配列には本文スライドだけを書く。表紙と目次はdeck_source_to_json.pyが自動生成する。
5. 目次はslides[].titleから自動生成される。目次用の別テキストをAIが作らない。
6. 保存名は表紙タイトルを短い英語で表したslugにする。ユーザーに提示するダウンロードはdeck_source.jsonとpptxだけにし、slides.jsonは提示しない。

## OUTPUT_FILES

保存名:
- 表紙タイトルから、内容が分かる短い英語名を作る。
- 3から6語程度に収め、snake_caseまたはkebab-caseを使う。例: CLAUDE.md設計の実務ガイドならclaude_md_design_guide。
- 英数字、ハイフン、アンダースコアだけを使う。空白、日本語、記号、絵文字は使わない。
- json、slides.json、pptxは同じベース名にする。slides.jsonは中間生成物として保存してよい。

リンク提示:
- ユーザーへ提示するダウンロードリンクはdeck_source.jsonとpptxだけである。
- slides.jsonのダウンロードリンクは出さない。最終報告でも成果物として列挙しない。

## STORY_ANALYSIS

プレゼン文脈を内部で把握する。

確認観点:
| 項目 | 判断例 |
|-----|-------|
| 発表目的 | 情報共有、説得、提案、依頼、報告 |
| 対象 | 社内、上司、顧客、経営層、一般 |
| 時間 | 5分、10分、15から20分、30分以上 |

枚数目安:
| 時間 | coverと目次込み推奨枚数 |
|-----|----------------------|
| 5分 | 5から7枚 |
| 10分 | 8から12枚 |
| 15から20分 | 12から18枚 |
| 30分以上 | 18から25枚 |

フレームワーク選択:
| 目的 | 型 | 構造 |
|-----|----|------|
| 要点を短く伝える | SDS | Summary、Details、Summary |
| 説得、提案 | PREP | Point、Reason、Example、Point |
| 依頼、交渉 | DESC | Describe、Express、Suggest、Choose |
| 汎用長尺 | 序論本論結論 | 導入、主張と根拠、まとめ |
| 営業提案 | AIDMA | Attention、Interest、Desire、Memory、Action |

ストーリー設計:
1. ソース全体から聴衆に最も伝えたい1文を定義する。
2. 選んだ型に沿ってセクションへ分け、本文スライドのslides配列を作る。
3. 主張、根拠、データ、事例、手順、並列要素、結論を抽出する。
4. タイトルは単なる要約ではなく、そのスライドの示唆を短く言い切る。
5. slides[].sectionは目次の大見出しになる。背景と前提、判断軸、設計方針、実行手順、運用改善など意味を持つ言葉にする。
6. sectionは前半、後半、Part 1、Part 2のような機械的な分割名にしない。目次の大見出しとして読んだ時に内容上のまとまりが分かる名前にする。

## SOURCE_ENRICHMENT

DECK_SOURCE_JSONを書く前に、常に内部で仮想の詳細原稿へ展開する。原文の箇条書きをそのまま短く移すだけでは、スライド本文が薄くなり、noteだけが厚くなる。これはユーザーに見せない分析作業であり、事実を捏造することではない。原文の主張を、背景、理由、含意、比較、注意点、判断基準へ言い換え、スライドに入れる素材を増やす。

特に補強が必要な原文:
- 見出しと箇条書き中心で、各項目が1文未満または名詞句だけである。
- 表やリストに整理されているが、なぜ重要か、どう使うか、何に注意するかが少ない。
- 1スライド候補あたり、根拠、例、比較、注意点のいずれかが欠けている。
- 原文の構造は明快だが、カード本文へ移すと各カードが1から2行で終わる。

手順:
1. 原文全体を、説明が長く、接続語が多く、背景や判断理由まで含む詳細原稿へ書き直す。
2. 各見出しや箇条書きを主張へ変換する。
3. 主張ごとに、背景、理由、例、比較、注意点、読者への示唆を少なくとも2種類補う。
4. 原文にない固有数値、事例名、実績、専門用語を作らない。
5. 詳細原稿から、スライド本文に載せる判断材料とnoteで話す背景を分ける。
6. 短い項目は、単語の羅列ではなく、何がどう効くかが分かる句へ変える。

展開パターン:
| 原文の形 | 内部で足す観点 | スライド化の方向 |
|---------|---------------|----------------|
| Aをする | なぜAが必要か、しないと何が起きるか | flowまたはbg_3card |
| A、B、C | 3要素の役割差、順序、使い分け | list_3card |
| AとBの違い | 判断基準、向く場面、誤用リスク | compare_2col_3row |
| 手順の箇条書き | 各手順の目的、完了条件、注意点 | flow_3stepまたはflow_4step |
| 表形式の整理 | 表から読むべき示唆、判断の結論 | table_conclusion |

密度:
- 1カードには、リード文、2から3項目、必要なら短い補足を置く。
- 箇条書きの各項目は、名詞だけで終えず、行動、理由、効果のどれかを含める。
- 1スライド内に、背景、判断基準、注意点、次の行動のうち少なくとも2つを含める。
- noteだけが厚く、表示本文が短い見出し語と名詞句だけの場合は未完成として扱い、blocks本文を書き足す。
- noteは本文不足を補う場所ではなく、本文を話すための補助である。先にblocks本文へ判断材料を置き、その後でnoteを書く。

禁止:
- 原文にない具体的な数値、会社名、製品名、成果を作らない。
- 原文をそのまま短い箇条書きへ移すだけで終わらない。
- 重要、効果的だけの抽象語で水増ししない。重要なら何に効くかまで書く。
- すべてをplain_2colに逃がさない。カード、比較、表、フローへ再設計する。

## JSON_SCHEMA

AIが作るのはdeck_source.jsonだけである。Markdownデッキ、メタテーブル、フェンスは作らない。

root:
- title: 表紙タイトル。
- subtitle: 表紙サブタイトル。不要なら空文字。
- affiliation: 所属。推定できなければCodex Working Deck。
- presenter: 発表者。推定できなければTakuya。
- date: YYYY-MM-DD。
- note: 表紙の発表者ノート。
- slides: 本文スライド配列。表紙と目次は含めない。

slide:
- section: 目次の大見出し。意味のある章名にする。
- layout: レイアウト名。
- title: スライド見出し。空にしない。目次小見出しへ自動反映される。
- message: サブメッセージ。不要なら空文字。
- note: 発表者読み上げ原稿。通常180から320字。JSON文字列なので実改行を使ってよい。
- blocks: layout別の本文ブロック。
- icon_prompt: card系とflow系の一括アイコン素材プロンプト。該当しないlayoutでは省略または空文字。

例:
{
  "title": "CLAUDE.md運用設計プレイブック",
  "subtitle": "AIの行動基準を実務のルールブックへ変える",
  "affiliation": "Codex Working Deck",
  "presenter": "Takuya",
  "date": "2026-05-01",
  "note": "本資料の目的を説明する。",
  "slides": [
    {
      "section": "背景と前提",
      "layout": "bg_3card",
      "title": "CLAUDE.mdはセッション開始時の行動基準である",
      "message": "毎回の説明を標準動作へ変える",
      "note": "読み上げ原稿を書く。",
      "blocks": {
        "section": "### ルールブックとして扱う\nCLAUDE.mdは作業開始時に読まれる常設の前提である。",
        "card-a": "### 反復説明を減らす\n毎回言う注意をルール化する。\n- 禁止操作を先に共有する\n- 必須コマンドを計画へ組み込ませる",
        "card-b": "### 判断基準をそろえる\n一般論ではなく案件基準で提案させる。\n- 技術スタックを固定する\n- 設計方針の優先順位を渡す",
        "card-c": "### 書きすぎを防ぐ\n常に守る内容だけを残す。\n- 一時的な好みを混ぜない\n- 古い前提を削る"
      },
      "icon_prompt": "Create a 3:1 horizontal icon strip with three equal square icons..."
    }
  ]
}

## LAYOUT_RULES

使用可能layoutと必須blocks:
| layout | 用途 | 必須blocks |
|-------|------|------------|
| plain_1col | 単一説明。nanobanana2 Yesでは使用禁止 | card-a |
| plain_2col | 2概念、または本文とnanobananaプロンプト | card-a, card-b |
| list_3card | 並列3要素 | card-a, card-b, card-c |
| flow_3step | 3工程 | step-a, step-b, step-c |
| flow_4step | 4工程 | step-a, step-b, step-c, step-d |
| diffuse_3card | 1から3展開 | section, card-a, card-b, card-c |
| converge_3card | 3から1収束 | card-a, card-b, card-c, conclusion |
| bg_3card | 背景と3点 | section, card-a, card-b, card-c |
| table | 表 | table |
| table_conclusion | 表と示唆 | table, conclusion |
| compare_2col_3row | 2対象3観点 | compare |
| matrix_3x3 | 3×3 | matrix |
| flow_matrix_3x3 | 縦3×3 | flow_matrix |
| h_flow_matrix_3x2 | 横3×2 | h_flow_matrix |
| h_flow_matrix_3x3 | 横3×3 | h_flow_matrix |
| h_flow_matrix_4x2 | 横4×2 | h_flow_matrix |

blocksの書き方:
- card、step、section、conclusion、plain用ブロックはMarkdown文字列で書く。見出し、箇条書き、強調は使ってよい。
- table、matrix、flow_matrix、h_flow_matrix、compareは {"head": [...], "rows": [[...], ...]} の形で書く。
- 独自block keyを作らない。text、step、card、plain、bodyは禁止。
- flow系のstep-aなどは先頭に### 見出しを置く。見出しがstepラベル、残りが本文になる。

レイアウト選択:
1. 3段階の時系列、工程、変化で、各stepに目的や完了条件を置けるならflow_3step。
2. 4段階の時系列、工程、変化で、各stepに目的や完了条件を置けるならflow_4step。
3. フラットな3要素ならlist_3card。
4. 1つの共通テーマから3方向へ広がるならdiffuse_3card。
5. 3つの根拠から1結論へ収束するならconverge_3card。
6. 背景説明と3ポイントならbg_3card。
7. 表データと重要な示唆があるならtable_conclusion。表データのみならtable。
8. 2対象3観点ならcompare_2col_3row。
9. グリッド型ならmatrixまたはflow_matrix系を使う。
10. 2概念の対立や比較ならplain_2col。
11. 単一説明ならplain_2colを優先する。nanobanana2 Yesではplain_1colを使わない。

重要:
- compare_2col_3rowのblocks keyはcompareである。matrixではない。
- 横フローマトリックスはh_flow_matrixを使う。
- flow系で各stepが名詞句だけ、または説明を入れると窮屈になる場合はflowを使わない。判断基準、理由、注意点まで見せる必要がある内容はlist_3card、bg_3card、table_conclusion、plain_2colへ変更する。
- plain_1colにtextは使わずcard-aだけを使う。flow_3stepにstepは使わずstep-a、step-b、step-cを使う。

## NANOBANANA_RULES

nanobanana2がYesの場合:
- slides配列の各スライドは画像生成導線を持つ。Aはplain_2colでblocks.card-bにnanobananaプロンプトを置く。Bはcard系またはflow系でicon_promptを置く。
- 3枚目以降にplain_1colを使わない。
- plain_image_col、image_label_1、画像プレースホルダーは使わない。

plain_2colのプロンプト欄:
- blocks.card-aへ表示本文を書く。
- blocks.card-bへ「### nanobananaプロンプト」に続けてインデント式コードブロック相当のプロンプトを書く。JSON文字列なのでフェンスは不要。
- プロンプト本文は英語で書く。ただし画像内文字は短い日本語ラベルにする。
- プロンプトには6:5の比率、白背景、資料向けのフラット図解、余白なし、キャンバス全体を使う、上下の空白やレターボックスを作らない、を含める。
- 抽象語だけにせず、人物、画面、書類、矢印、付箋、表、グラフなど具体的な構成要素を3から6個指定する。
- 単純なアイコン集合ではなく、関係、流れ、判断、前後比較が分かる1枚の説明図にする。
- 日本語の短いタグ、ラベル、名前、1行説明を少量入れてよい。例は「入力」「判断」「注意」「完了」「ルール」「メモ」などである。

card系とflow系のicon_prompt:
- 対象はlist_3card、flow_3step、flow_4step、diffuse_3card、converge_3card、bg_3card。
- icon_promptはnoteに埋め込まない。独立フィールドとして書く。deck_source_to_json.pyがnote末尾へ機械的に結合する。
- 3要素は3:1の横長キャンバスに、等幅の正方形アイコン3個を左から順に並べる。
- flow_4stepは4:1の横長キャンバスに、等幅の正方形アイコン4個を左から順に並べる。
- icon_promptに6:5を入れない。
- 各アイコンは同じサイズ、同じ余白、同じ色調、同じ視点にする。各アイコンの中心を各区画の中央に置く。
- 背景は白または透明感のある白にし、区画間には薄いガイド余白を置く。外周余白は小さくし、上下に大きな余白を作らない。
- 日本語ラベルは原則入れない。必要時のみ各アイコンの下に2から4文字の短い日本語タグを置く。
- 生成後に水平等分でトリミングされる前提で、左から順番を明記する。例: left icon, center icon, right icon。4個の場合は first, second, third, fourth。

品質:
1. 具体性。会議、チェックリスト、グラフ、端末、書類、付箋、画面など見えるものに落とす。
2. スタイル統一。plain_2col用は資料向けフラット図解、card/step用は横長アイコンストリップとして一貫させる。
3. plain_2col用の画像内文字は短い日本語だけにする。card/step用は原則文字なし、必要時のみ2から4文字タグに留める。
4. 図解に向かない抽象概念は、tableやflowなど画像不要レイアウトへ逃がす。

## CONTENT_LIMITS

カードは件数、視覚行数、本文文字量を同時に見る。収めるために内容を薄くしない。薄くなる場合はレイアウトを変えるか分割する。

| layout | 通常目標 | 文字量目安 |
|-------|----------|-----------|
| list_3card | リード1文と3から4項目 | 各カード100字以上 |
| diffuse_3card、bg_3card、flow_3step | リード1文と2から3項目 | 各カード58字以上 |
| converge_3card | リード1文と2項目、結論短め | 各カード58字以上 |
| flow_4step | 短いリードと1から2項目 | 各ステップ40字以上 |
| plain_2col | リード1文と3から4項目 | 各列115字以上 |
| table、matrix、compare | 単語だけにしない | 各セルは意味のある句 |

制約:
- 箇条書きは原則20から38字程度。
- flow_4stepやconvergeの結論は短めにし、長文説明を避ける。
- flow系は手順名を並べる装置ではない。目的、完了条件、注意点のいずれかを置けない場合は、本文量に合う別layoutへ変える。
- converge_3cardはカード本文と結論が競合しやすいため、カード内の小見出しや長い補足段落を避ける。
- nanobanana2使用時は図解設置スペースとして約2行分を残す。
- noteに理由、背景、注意点が入っているのにblocks本文が薄い場合は、noteから判断材料を戻す。
- スライド表示文はである調に統一する。

## CONTENT_VARIATION

単調な箇条書きを避ける。
- 各cardまたはstepは見出し直後に1文のリードを置く。
- 重要語は太字、補足や定義は斜体、ファイル名やコード片はコード表記、旧情報は打ち消し表記にする。JSON内のMarkdown文字列ではMarkdown記号を使ってよい。
- 短文項目、AからB、従来と今後、問いかけ、短い補足文を混ぜる。
- list_3cardとplain_2colでは番号リストや短い小見出しを使える。
- converge、diffuse、bg、flow系はリード文と少数項目を基本にし、小見出しを増やしすぎない。
- 同じスライド内で「ラベル: 説明」の形を連続させない。

## SLIDE_STYLE

スライドに表示されるタイトル、本文、表、結論はである調にする。です、ます、ください、しましょう、しますを避け、である、する、となるへ直す。noteも原則である調に寄せる。

## SPEAKER_NOTES

noteはPPTX発表者ビューの読み上げ原稿である。スライド本文を見ていない人にも意味が通じる文章を書く。JSON文字列なので実改行を使ってよい。Markdown表セルではないため、brタグやバックスラッシュnで改行を表す必要はない。

必須要素:
- 1枚につき原則180から320字。coverのみ120字以上でよい。
- 冒頭は毎回同じ固定句にしない。前スライドからの流れ、聴衆への問い、場面設定、結論の先出しを使い分ける。
- カード、表、フローを順番に説明し、各要素の意味や関係を補う。
- 最後に、聴衆が何を理解すべきか、次のスライドとどうつながるかを示す。
- スライド上の短い箇条書きをそのまま読み上げるだけにしない。

冒頭固定句の禁止:
- 全スライドで「このスライドで伝えたいことは」から始めない。
- 連続する3枚のnoteで同じ冒頭構文を使わない。
- 冒頭にスライドタイトルをそのまま読み上げない。タイトルを受けて、なぜ今その話に進むのかを述べる。

noteの作り方:
1. 前スライドの結論を受け、次に見るべき論点を示す。
2. 聴衆が抱きそうな疑問を1つ置き、その答えとして本文を説明する。
3. 表やカードの項目を読み上げるだけでなく、項目間の関係、判断基準、実務上の意味を補う。
4. 最後の一文で、次のスライドへの橋渡し、または聴衆が持ち帰る判断を示す。

冒頭バリエーション:
| 場面 | 冒頭の方向 |
|-----|------------|
| 導入直後 | まず押さえるべき前提は、の形で入口を作る |
| 比較スライド | ここで混同しやすいのは、の形で注意を引く |
| 手順スライド | 実際に進める時は、の形で行動場面へ移る |
| 表スライド | この表は数値や項目の羅列ではなく、の形で読み方を示す |
| まとめ前 | ここまでの話を判断に変えると、の形で結論へ寄せる |

聞き手を引き込むtip:
- いきなり説明せず、聴衆が困る場面や迷う判断から入る。
- 「なぜなら」「その結果」「一方で」「ここで注意したいのは」など、因果と対比の接続語を使う。
- 1枚のnote内で、前提、理由、例、注意点、次の行動のうち少なくとも2つを入れる。
- 抽象論だけで終えず、実務でどう判断が変わるかを一文入れる。
- note全体を独立した短いナレーションにし、スライド本文がなくても意味が通るようにする。

nanobanana2使用時:
- icon_promptは読み上げ原稿の字数に含めない。
- card系やflow系では、note本文だけで180字以上を確保する。
- icon_promptをnoteやblocks内に重複して貼らない。独立フィールドだけに置く。
- note本文にbrタグが出ていたら未完成として扱い、JSON文字列の実改行へ直す。

## DENSITY_REVIEW

DECK_SOURCE_JSONを書いた直後に目視で自己点検し、問題があればblocks本文を直接直してからPPTX変換へ進む。これは文字数を機械的に測る工程ではなく、スライドを見た人がその場で判断できる情報量を本文に戻す編集工程である。

確認観点:
| layout | 自己点検 |
|-------|----------|
| list_3card | 各カードにリード1文と3項目。文量差を小さくする |
| diffuse_3card、bg_3card、flow_3step | sectionやstepの主張を1文で置き、各カードはリードと2項目程度 |
| converge_3card | 各カードはリードと2項目まで。結論は短く強い示唆 |
| flow_4step | 1ステップは短いリードと1から2項目。長文を避ける |
| plain_2col | 各カラムにリードと3項目程度。左右密度を揃える |

修正チェック:
- noteに理由、背景、注意点が入っているのに本文が薄い場合は、noteから判断材料を抜き出してblocksへ戻す。
- 各カード、各step、各カラムには、背景、理由、判断基準、具体例、注意点、影響、次の行動のうち少なくとも2種類を表示本文として含める。
- flow系でstepが短いラベルだけになった場合は、flowを維持しない。list_3card、bg_3card、table_conclusion、plain_2colへ変更して本文を載せる。
- 余白が目立つカードには、判断基準、注意点、影響を1項目追加する。
- はみ出しそうなカードは例示や修飾語を削り、必要ならplain_2colやtableへ変更する。
- 装飾、番号、小見出しが少ないスライドは、重要語を強調して視線の入口を作る。
- noteは読み上げ原稿だけで意味が通るよう、主張、各要素の意味、結論を含める。
- nanobanana2使用時でも、プロンプト貼り付け用途のplain_2colは使ってよい。plain_image_colとimage_label_1は完全に消す。

## FINAL_SELF_CHECK

Python検証は最終手段である。DECK_SOURCE_JSONを書いた直後に目視で短く点検する。

点検順:
- rootにtitle、date、slidesがあるかを見る。
- slides配列に表紙や目次を入れていないかを見る。
- slides[].titleが空でないか、重複していないかを見る。
- slides[].sectionが意味のある章名になっているかを見る。
- layoutごとの必須blocksがそろっているかを見る。
- DENSITY_REVIEWに照らし、blocks本文が短い名詞句だけになっていないかを見る。
- nanobanana2がYesの場合、slidesにplain_1colがないかを見る。
- nanobanana2がYesの場合、plain_2colはblocks.card-bにプロンプト、card/flow系はicon_promptを持つかを見る。
- card/flow系のicon_promptに6:5が入っていないかを見る。
- Markdownデッキのメタテーブル、スライド区切り、フェンス、[nanobanana2 icon prompt]行が混じっていないかを見る。

## SETUP_SCRIPT

setup_deck.pyとして保存し、/mnt/dataへ実行ファイル群をコピーする。既存ファイルがあっても上書きしてよい。

python
"""deck-from-source の実行ファイル群を /mnt/data にコピーするセットアップスクリプト。"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / ".agents" / "skills" / "deck-from-source"
if not (SKILL_DIR / "deck_source_to_json.py").exists():
    SKILL_DIR = ROOT / ".claude" / "skills" / "deck-from-source"
DEST_DIR = Path("/mnt/data")

FILES = [
    "resolve_uploads.py",
    "deck_source_to_json.py",
    "md_to_json.py",
    "to_pptx.py",
    "template_engine_area.html",
    "templates.json",
    "design.json",
    "logo.png",
    "background.png",
]

def main() -> None:
    missing = [f for f in FILES if not (SKILL_DIR / f).exists()]
    if missing:
        print(f"[エラー] スキルフォルダに以下のファイルが見つかりません: {missing}", file=sys.stderr)
        sys.exit(1)
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        shutil.copy2(SKILL_DIR / name, DEST_DIR / name)
        print(f"copied: {name}")
    print(f"セットアップ完了 → {DEST_DIR.resolve()}")

if __name__ == "__main__":
    main()
