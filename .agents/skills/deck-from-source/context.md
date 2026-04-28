# context.md deck-from-source 詳細ルール

目的:
原文ソースから、分析済みのスライドデッキMDとPPTXを1ターンで生成するための詳細ルールである。SKILL.mdは短い実行指示、このファイルは毎ターンfile searchで読み込む詳細仕様として使う。

このファイルの記号方針:
- context.md自体では文字数削減のため、アスタリスクと半角バッククォートを使わない。
- ただし生成するDECK_MDでは、Markdown強調、コード、フェンスを実文字で使ってよい。
- BQ3は半角バッククォート3個の略記である。DECK_MDへ出力するときはBQ3という文字を残さず、必ず半角バッククォート3個へ置換する。
- 太字はアスタリスク2個、斜体はアスタリスク1個、コードやファイル名は半角バッククォート1個、旧情報はチルダ2個で囲む。DECK_MDではこれらを積極的に使う。

全体フロー:
1. ターンAではソースを受け取っても分析や生成を始めず、nanobanana2画像を使うかYesまたはNoで確認する。
2. ターンBではソース分析、構成決定、DECK_MD生成、自己点検、PPTX変換、ダウンロードリンク提示まで完了する。
3. ユーザーにスライド枚数、発表者名、対象者を追加質問しない。必要ならソースから推定し、不明部分は自然な汎用値で補う。
4. 2枚目は必ずplain_2colの目次にする。左カラムへカテゴリを上から積み、入りきらない範囲だけ右へ送る。
5. card-aなどのコンテンツブロック内にスライド区切りの3連ハイフンを書かない。直後のスライドがlayoutを失うためである。

## STORY_ANALYSIS

プレゼン文脈を内部で把握する。

確認観点:
| 項目 | 判断例 |
|-----|-------|
| 発表目的 | 情報共有、説得、提案、依頼、報告 |
| 対象 | 社内、上司、顧客、経営層、一般 |
| 時間 | 5分、10分、15から20分、30分以上 |

枚数目安:
| 時間 | cover込み推奨枚数 |
|-----|-----------------|
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
2. 選んだ型に沿ってセクションへ分ける。
3. 主張、根拠、データ、事例、手順、並列要素、結論を抽出する。
4. スライド構成案を内部で作り、確認質問は挟まない。
5. タイトルは単なる要約ではなく、そのスライドの示唆を短く言い切る。

目次の作り方:
- タイトルの単純羅列にしない。
- 導入、分析、提案、実行、まとめなど、内容上のカテゴリを大見出しにする。
- 各スライドタイトルをカテゴリ配下の小見出しまたは項目にする。
- 左カラムから順に積み、左に入りきらない残りだけ右カラムへ送る。

## TEMPLATE_WORKFLOW

各スライドに上から順に適用し、最初に一致したレイアウトを使う。強引な当てはめはしない。

1. 表紙ならcover。
2. 3段階の時系列、工程、変化ならflow_3step。
3. 4段階の時系列、工程、変化ならflow_4step。
4. フラットな3要素ならlist_3card。
5. 1つの共通テーマから3方向へ広がるならdiffuse_3card。
6. 3つの根拠から1結論へ収束するならconverge_3card。
7. 背景説明と3ポイントならbg_3card。
8. 表データと重要な示唆があるならtable_conclusion。
9. 表データのみならtable。
10. 2つの対象を3観点で比較するならcompare_2col_3row。
11. グリッド型なら次から選ぶ。
| 条件 | レイアウト | ブロックタグ |
|-----|------------|-------------|
| 3×3で縦方向フロー | flow_matrix_3x3 | flow_matrix |
| 3×2で横方向フロー | h_flow_matrix_3x2 | h_flow_matrix |
| 3×3で横方向フロー | h_flow_matrix_3x3 | h_flow_matrix |
| 4×2で横方向フロー | h_flow_matrix_4x2 | h_flow_matrix |
| 単純な3×3表 | matrix_3x3 | matrix |
12. 2概念の対立や比較ならplain_2col。
13. 単一コンセプト説明ならplain_1col。

nanobanana2がYesの場合:
- 目次以外のplain_1colとplain_2colを最終DECK_MDに残さない。
- plain_1col候補はplain_image_colへ置換し、image_label_1を入れる。
- plain_2col候補はplain_image_colへ置換する。2カラムが必須ならtable、compare_2col_3row、list_3cardへ再設計する。
- 画像が不自然な場合もplainへ戻さない。table、table_conclusion、list_3card、flow系へ再設計する。

レイアウト早見表:
| レイアウト | 用途 | 必要ブロック |
|-----------|------|-------------|
| cover | 表紙 | なし |
| plain_1col | 単一説明 | card-a |
| plain_2col | 2概念 | card-a、card-b |
| list_3card | 並列3要素 | card-a、card-b、card-c |
| flow_3step | 3工程 | step-a、step-b、step-c |
| flow_4step | 4工程 | step-a、step-b、step-c、step-d |
| diffuse_3card | 1から3展開 | section、card-a、card-b、card-c |
| converge_3card | 3から1収束 | card-a、card-b、card-c、conclusion |
| bg_3card | 背景と3点 | section、card-a、card-b、card-c |
| table | 表 | table |
| table_conclusion | 表と示唆 | table、conclusion |
| compare_2col_3row | 2対象3観点 | compare |
| matrix_3x3 | 3×3 | matrix |
| flow_matrix_3x3 | 縦3×3 | flow_matrix |
| h_flow_matrix_3x2 | 横3×2 | h_flow_matrix |
| h_flow_matrix_3x3 | 横3×3 | h_flow_matrix |
| h_flow_matrix_4x2 | 横4×2 | h_flow_matrix |
| plain_image_col | テキストと縦目画像 | card-a、image_label_1 |

重要:
- compare_2col_3rowのブロックタグはcompareである。matrixではない。
- 横フローマトリックスはh_flow_matrixを使う。
- BQ3なしでタグ名だけを書く形式は無効である。

## MD_SYNTAX

基本構造:
- スライドは単独行の3連ハイフンで区切る。
- 1行目は見出し1形式のタイトル。2行目に見出し2形式のサブメッセージを置ける。
- その後にkeyとvalueのMarkdownテーブルでメタ情報を書く。
- layoutは必須。noteは原則必須。coverではaffiliation、presenter、dateも入れる。
- 本文ブロックはBQ3タグ名で開き、BQ3で閉じる。生成時はBQ3を実際の半角バッククォート3個へ置換する。
- 開始フェンスはBQ3card-a、BQ3table、BQ3compareのように、BQ3の直後へタグを書く。

最小例の省略記法:
BQ3card-a
### 見出し
リード文で要点を述べる。
- 項目1
- 項目2
BQ3

DECK_MDでは上のBQ3を実際の半角バッククォート3個にする。BQ3という文字列は出力しない。

フロントマターキー:
| キー | 用途 |
|-----|------|
| layout | レイアウト名。必須 |
| note | 発表者読み上げ原稿 |
| image_label_1 | plain_image_colの画像プロンプト |
| affiliation | coverの所属 |
| presenter | coverの発表者 |
| date | coverの日付 |

ブロック別注意:
- card系とstep系は先頭に見出し3形式の短い見出しを置く。
- step系では見出し3がステップラベルとして使われる。
- tableはMarkdown表を入れる。列名、区切り行、データ行を必ず置く。
- compareは左端に観点列、右に比較対象2列を置く。
- matrix系は先頭行を列ヘッダー、以降を行として解釈する。
- conclusionは2行相当までの短い示唆にする。
- sectionは背景や共通テーマを短く置く。

表紙例の骨格:
# 主題タイトル
## 補足タイトル
| key | value |
|-----|-------|
| layout | cover |
| affiliation | 組織名 |
| presenter | 発表者名 |
| date | YYYY-MM-DD |
| note | 発表背景と目的を1から2文で述べる。 |

テーブル例の骨格:
# テーブルタイトル
## 表から読むべき示唆
| key | value |
|-----|-------|
| layout | table |
| note | 表の読み方と注目点を説明する。 |
BQ3table
| 列1 | 列2 | 列3 |
| --- | --- | --- |
| データ | データ | データ |
BQ3

## NANOBANANA_RULES

plain_image_colの画像:
- image_label_1へ書く。
- 6:5の比率、フラットデザイン、白背景、ミニマル、文字なしを必ず含める。
- スライドの主張を1枚の概念イラストとして表す。抽象語だけにせず、具体的なシンボルを2から4個指定する。

image_label_1の型:
[スライドテーマ]を表すシンプルなイラスト。フラットデザイン、ミニマルアイコン風、ビジネス向け、白背景。6:5の比率で[具体的な概念]を1枚のビジュアルで表現する。文字なし。

カードやフロー用の一括アイコン:
- 対象はlist_3card、flow_3step、flow_4step、diffuse_3card、converge_3card、bg_3card。
- note末尾に読み上げ原稿、空白、3連ハイフン、空白、[nanobanana2 icon prompt]、プロンプトの順で追記する。
- 読み上げ原稿部分だけで180字以上を確保する。
- list_3card、flow_3step、diffuse_3card、converge_3card、bg_3cardは3アイコン。flow_4stepは4アイコン。
- 各アイコンは横一列、正方形枠、統一色、白背景、文字なしにする。
- 生成後に水平等分でトリミングされる前提で、左から順番を明記する。

品質:
1. 具体性。会議、チェックリスト、グラフ、端末など見えるものに落とす。
2. スタイル統一。全スライドでフラット、白背景、ミニマルを一貫させる。
3. 画像内文字なし。ラベルや英字を入れない。
4. 図解に向かない抽象概念は、tableやflowなど画像不要レイアウトへ逃がす。

## CONTENT_LIMITS

カードは件数、視覚行数、本文文字量を同時に見る。収めるために内容を薄くしない。薄くなる場合はレイアウトを変えるか分割する。

| レイアウト | 通常目標 | 文字量目安 |
|-----------|----------|-----------|
| list_3card | リード1文と3から4項目 | 各カード100字以上 |
| diffuse_3card、bg_3card、flow_3step | リード1文と2から3項目 | 各カード58字以上 |
| converge_3card | リード1文と2項目、結論短め | 各カード58字以上 |
| flow_4step | 短いリードと1から2項目 | 各ステップ40字以上 |
| plain_2col | リード1文と3から4項目 | 各列115字以上 |
| plain_1col | 段落と箇条書き | 180字以上 |
| table、matrix、compare | 単語だけにしない | 各セルは意味のある句 |

制約:
- 箇条書きは原則20から38字程度。
- flow_4stepやconvergeの結論は短めにし、長文説明を避ける。
- converge_3cardはカード本文と結論が競合しやすいため、カード内の小見出しや長い補足段落を避ける。
- nanobanana2使用時はアイコン設置スペースとして約2行分を残す。

## CONTENT_VARIATION

単調な箇条書きを避ける。
- 各cardまたはstepは見出し直後に1文のリードを置く。
- 重要語は太字、補足や定義は斜体、コードやファイル名はコード表記、旧情報は打ち消し表記にする。実DECK_MDではMarkdown記号を使う。
- 短文項目、AからB、従来と今後、問いかけ、短い補足文を混ぜる。
- list_3cardとplain_2colでは番号リストや短い小見出しを使える。
- converge、diffuse、bg、flow系はリード文と少数項目を基本にし、小見出しを増やしすぎない。
- 同じスライド内でラベル: 説明の形を連続させない。

## SLIDE_STYLE

スライドに表示されるタイトル、本文、表、結論はである調にする。です、ます、ください、しましょう、しますを避け、である、する、となるへ直す。noteも原則である調に寄せる。

## SPEAKER_NOTES

noteはPPTX発表者ビューの読み上げ原稿である。スライド本文を見ていない人にも意味が通じる文章を書く。

必須要素:
- 1枚につき原則180から320字。coverのみ120字以上でよい。
- 冒頭でそのスライドの主張を1文で述べる。
- カード、表、フローを順番に説明し、各要素の意味や関係を補う。
- 最後に、聴衆が何を理解すべきか、次のスライドとどうつながるかを示す。
- スライド上の短い箇条書きをそのまま読み上げるだけにしない。

noteの型:
このスライドで伝えたいことは、[主張]である。まず[要素A]は[意味]を示す。次に[要素B]は[理由または対比]である。最後に[要素C]によって[結論]が分かる。つまり[聴衆が取るべき解釈]である。

nanobanana2使用時:
- note末尾に画像生成プロンプトを追記しても、読み上げ原稿部分だけで180字以上を確保する。
- 画像生成プロンプトは読み上げ原稿の字数に含めない。

## DENSITY_REVIEW

B-3ではPython検証を行わない。DECK_MDを作った直後に目視で自己点検し、問題があればDECK_MD本文を直接直してからPPTX変換へ進む。

確認観点:
| レイアウト | 自己点検 |
|-----------|----------|
| list_3card | 各カードにリード1文と3項目。文量差を小さくする |
| diffuse_3card、bg_3card、flow_3step | sectionやstepの主張を1文で置き、各カードはリードと2項目程度 |
| converge_3card | 各カードはリードと2項目まで。結論は短く強い示唆 |
| flow_4step | 1ステップは短いリードと1から2項目。長文を避ける |
| plain_2col | 各カラムにリードと3項目程度。左右密度を揃える |
| plain_1col | 段落と箇条書きで余白を埋める |

修正チェック:
- 余白が目立つカードには、判断基準、注意点、影響を1項目追加する。
- はみ出しそうなカードは例示や修飾語を削り、必要ならplain_2colやtableへ変更する。
- 装飾、番号、小見出しが少ないスライドは、重要語を強調して視線の入口を作る。
- noteは読み上げ原稿だけで意味が通るよう、主張、各要素の意味、結論を含める。
- スライド表示文はである調に統一する。
- nanobanana2使用時は目次以外のplain_1colとplain_2colを完全に消す。

## SETUP_SCRIPT

setup_deck.pyとして保存し、/mnt/dataへ実行ファイル群をコピーする。既存ファイルがあっても上書きしてよい。

python
"""deck-from-source の実行ファイル群を /mnt/data にコピーするセットアップスクリプト。
Colab / Jupyter 等の環境で初回セットアップ時に一度実行する。
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKILL_DIR = ROOT / ".agents" / "skills" / "deck-from-source"
if not (SKILL_DIR / "md_to_json.py").exists():
    SKILL_DIR = ROOT / ".claude" / "skills" / "deck-from-source"
DEST_DIR = Path("/mnt/data")

FILES = [
    "resolve_uploads.py",
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
        print(f"  スキルフォルダ: {SKILL_DIR}", file=sys.stderr)
        sys.exit(1)

    DEST_DIR.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = SKILL_DIR / name
        dst = DEST_DIR / name
        shutil.copy2(src, dst)
        print(f"  copied: {name}")

    dest = DEST_DIR.resolve()
    print(f"\nセットアップ完了 → {dest}")
    print("\nPPTX生成コマンド:")
    print(f'  python "{dest}/md_to_json.py" deck.md deck.pptx --json deck.json --assets-dir "{dest}"')


if __name__ == "__main__":
    main()

実行後の注意:
- /mnt/data が存在しない環境では失敗する場合がある。その場合はユーザーに環境制約を伝える。
- 表示されたPPTX生成コマンドをそのまま使い、パスをハードコードしない。
- WindowsではPath("/mnt/data").resolve()がC:\mnt\dataになることがあるため、出力されたパスを使って環境差異を吸収する。
- スクリプトファイル群は.agents/skills/deck-from-sourceまたは.claude/skills/deck-from-sourceに置かれている。
