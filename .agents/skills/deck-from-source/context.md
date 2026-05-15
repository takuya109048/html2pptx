# context.md deck-from-source 司令塔

目的:
このファイルは毎ターンfile searchで読む唯一のコンテキストである。SKILL.mdはこのファイルを読む入口だけを担い、以後の判断、質問、生成、変換、修復、検証、出力はすべてこのファイルに従う。詳細ルール本文はcontext_data.jsonへ分離している。

毎ターン最初:
file searchではqueriesだけを使い、次を実行する。
{ "queries": ["context.mdのmd全文をfile search"] }

code interpreter初回:
resolve_uploads.pyをglobで探して実行し、assistant-任意ID-元ファイル名を元ファイル名へコピーする。以降は/mnt/data/元ファイル名で参照する。
code interpreterに渡すcode本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。長い仕様説明や秘密情報は書かない。
デッキ生成ターンでは、file searchでcontext.mdを読んでターンBと判断した直後、最初のcode interpreterを開始する前に、必ず独立したチャット本文で「資料化を開始します。スライド構成、検証、PPTX出力までおおよそ5分程度かかります。」と出す。code interpreter内の冒頭コメント、ツール実行ログ、最終報告だけで代替しない。その後、分割コンテキストを読む前の最初のcode interpreterで現在時刻を取得し、/mnt/data/deck_generation_timer.jsonへstarted_atとして保存する。スライド修正まで終わり、最終版PPTXを出力できる状態になったら再度現在時刻を取得し、finished_atとelapsed_secondsを計算する。最終チャットでは開始時刻や終了時刻は表示せず、所要時間だけを短くコメントする。

ログ制限:
code interpreterログは先頭400文字と末尾400文字の合計800文字だけが安定してAIへ渡る前提で扱う。長いコンテキストを一括printしない。context_loader.pyは1回に1チャンクだけ出す。複数チャンクを読む時は、1回ずつcode interpreterを実行する。

フェーズ:
turn_b_yes: nanobanana2 Yesで生成する時に読む。
turn_b_no: nanobanana2 Noで生成する時に読む。
repair_emphasis: strict-emphasis、太字不足、弱い太字、スキムライン失敗を直す時に読む。
repair_density: strict-density、本文不足、noteだけ厚い、カードが薄い時に読む。
repair_text: 文字化け、markup、title、section、block key、JSON構造エラーを直す時に読む。
preflight_quality: 初回生成前に必ず読む修正用統合フェーズ。repair_emphasis、repair_density、repair_textの全チャンクを含むため、preflight_qualityをDONEまで読むことで修正用コンテキストをすべて先読みした扱いにする。
setup: /mnt/dataに実行ファイル群が見つからない時に読む。

取得方法:
ターンBではDECK_SOURCE_JSONを書く前、source_spineやスライド構成を考える前に、必ず必須フェーズ群を順番にstartする。Yesならturn_b_yes、Noならturn_b_noをDONEまで読み、その後preflight_qualityをDONEまで読む。preflight_qualityはrepair_emphasis、repair_density、repair_textを束ねた修正用統合フェーズであり、strictエラー後だけに読むものではなく、初回生成前の必須先読みである。
ターンB開始時は、構成やsource_spineを考え始める前、かつ最初のcode interpreterを開始する前に、必ずチャットへ所要時間の見通しだけを独立して出す。「資料化を開始します。スライド構成、検証、PPTX出力までおおよそ5分程度かかります。」これは分析メモではなく、処理開始の合図である。ユーザーに分割コンテキスト、DONE、NEXTなどの内部処理名を説明しない。code interpreter内の冒頭コメントだけで、このチャット通知を省略してはならない。
最初の取得は、処理開始時刻をdeck_generation_timer.jsonへ保存し、resolve_uploads.pyを実行したうえで context_loader.py start フェーズ名 をsubprocessで実行する。
続きは context_loader.py next を実行する。1回のcode interpreter実行につき1回だけ実行する。出力末尾がNEXTなら次回もnext、DONEならそのフェーズは読了である。
code interpreterの出力が空、または直前のチャンク表示を見失った場合は、同じ処理を再実行せず context_loader.py last を1回実行して直前の正常出力を再表示する。lastでも戻らない場合だけ、現在フェーズをstart フェーズ名から読み直す。
生成フェーズとpreflight_qualityの両方がDONEになるまで、ソース分析、source_spine作成、スライド構成決定、DECK_SOURCE_JSON生成、PPTX変換へ進まない。読み取り途中でユーザーへ分析メモや構成案を出さない。

ターンA:
新しい原文ソースを受け取り、nanobanana2方針が未確定なら、分析、判断、JSON生成、PPTX生成をしない。次の質問だけを返す。
「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（Yesにすると説明図プロンプトやカード/フロー用アイコンプロンプトをdeck_source.jsonに追加します。Noなら画像プロンプトなしで生成します）」
スライド枚数、発表者名、対象者は追加質問しない。

ターンB:
直近の返答でYesまたはNo方針を受け取ったら、前ターンのソースを使う。最初のcode interpreterより前に所要時間の見通しをチャットへ出し、その後code interpreterで必須フェーズのstartへ進む。生成フェーズとpreflight_qualityをすべてDONEまで読み、内部でソース分析、構成決定、DECK_SOURCE_JSON生成、自己点検、PPTX変換、必要なスライド修正、リンク提示まで完了する。思考過程、分析メモ、構成案、分割コンテキストの読込状況はユーザーに出さない。最終チャットには成果物リンクと所要時間だけを出す。

生成の最優先方針:
原文のストーリーに忠実であることを最優先する。発表資料として見栄えを整えるために、原文の論理順、章立て、見出し立て、主張、根拠、結論を別ストーリーへ作り替えない。厚みは、原文から自然に導ける背景、理由、含意、注意点、判断基準だけで足す。

SOURCE_FIDELITY_LOCK:
DECK_SOURCE_JSONを書く前に、内部でsource_spineを作る。source_spineは原文順の、章、見出し、主張、根拠、例、注意点、結論の並びである。各本文スライドはsource_spineの連続範囲に対応させる。原文に明示された章や見出しがある場合は、原則としてその順序と親子関係をslides[].sectionとslides[].titleへ反映する。PREP、SDSなどの型に合わせるために原文順や章立てを大きく並べ替えない。原文にない固有数値、事例名、実績、専門用語、新しい主張を作らない。

SOURCE_ENRICHMENT:
原文を詳細原稿へ自由に書き直さない。原文の短い記述を、同じ意味の範囲で読者が理解できる粒度へ展開する。見出しや短い箇条書きには、原文から自然に導ける理由、背景、使い分け、注意点を足してよい。足した内容が原文のどこから導けるか説明できない場合は入れない。

source_refs:
各本文スライドは、対応するsource_spineのIDを内部的に持つ。可能ならDECK_SOURCE_JSONへ _source_refs として入れてよい。PPTX変換で不要な場合も、自己点検では各スライドが原文のどこに対応するか説明できる状態にする。

note方針:
noteはそのまま読み上げてもプレゼンテーションとして成立する台本である。ただし、noteはスライド本文と原文参照を説明するためのものであり、noteだけに新しい論点、例、数値、判断、結論を初出ししない。重要情報がnoteにしかない場合は、先にmessageまたはblocksへ戻してからnoteを書き直す。

NOTE_PRESENTATION_SCRIPT:
noteは、入口文、要点文、本文解説、意味づけ、次スライドへの接続文の順に書く。要点文はそのスライドのmessageまたはconclusionと同じ結論にする。本文解説はblocksの見出し、箇条書き、表、フロー、結論枠を画面上の順番でたどる。意味づけはblocksとsource_refsから自然に導ける範囲に限定する。

生成時の内部順序:
1. 最初のcode interpreterより前に所要時間の見通しをチャットへ出し、処理開始時刻を保存してから生成フェーズとpreflight_qualityをすべてDONEまで読む。
2. 原文をsource_spineへ分解し、話順、章立て、見出し立て、主張、根拠、結論を固定する。
3. source_spineの順にスライド構成とsectionを決める。原文の章や見出しがある場合は、表現を短く整える範囲に留め、章の分割・統合・改名を必要最小限にする。本文スライドが4枚以上なら、全sectionが1枚ずつで終わる構成にしない。
4. 各スライドのsource_refsを内部設計する。
5. blocks本文を原文忠実かつ十分な厚みで書く。
6. 各スライド本文を書く前に太字スキムラインを内部設計する。
7. noteをスライド本文に沿った読み上げ台本として書く。
8. DECK_SOURCE_JSONを書く。
9. FINAL_SELF_CHECK相当の目視点検を行い、必要なら本文とnoteを直す。
10. deck_source_to_json.pyをstrict系オプション付きで実行する。
11. strictエラーが出たら、読了済みのpreflight_quality内のrepair_emphasis、repair_density、repair_textのルールを使ってJSONを修復して再実行する。別ターンで修復する場合のみ、該当repairフェーズをDONEまで読み直す。
12. strictエラーや自己点検で必要になったスライド修正をすべて終え、最終版PPTXを出力できる状態になった時点で完了時刻を取得し、開始時刻との差分を計算する。最終チャットでは開始時刻や終了時刻を出さず、所要時間だけをコメントする。

生成の不変条件:
root.titleは日本語の表紙タイトルにする。保存名は短い英語slugにする。
root.summaryを必ず書く。slides配列には本文スライドだけを書く。表紙、サマリー、目次はdeck_source_to_json.pyが自動生成する。
slides[].titleは目次小見出しであり、名詞句か体言止めにする。主張や示唆はmessageへ移す。
layoutごとの必須blocks名を守る。独自keyは作らない。
compare_2col_3rowはblocks.compareにhead 3列、rows 3行、各row 3列を必ず入れる。各rowは[観点ラベル, 左側内容, 右側内容]であり、右側内容を空欄にしない。matrix、flow_matrix、h_flow_matrixもテンプレートの列数と行数を崩さず、空セルを作らない。
nanobanana2 Yesでは本文slidesにplain_1colを使わない。
Markdownデッキ記法、メタテーブル、フェンス、HTML改行タグ、文字化けを入れない。

FINAL_SELF_CHECK:
原文順序を壊していないか。原文の章立てや見出し立てを不必要に組み替えていないか。各スライドがsource_spineのどこに対応するか説明できるか。原文にない主張を足していないか。blocks本文が短い名詞句だけになっていないか。noteにしかない重要情報がないか。noteの結論がmessageまたはconclusionと一致するか。noteだけを連続して読んでもプレゼンとして自然につながるか。strict変換前に必ず見る。

PPTX変換コード:
DECK_SOURCE_JSONを確定したら、code interpreterで次の型を使う。TITLE_SLUG、USE_NANOBANANA2、DECK_SOURCE_JSONは実内容に置き換える。

```python
# 確定済みDECK_SOURCE_JSONをPPTXへ変換し、修正完了後の所要時間と成果物リンクを表示します。
import glob, json, os, subprocess, sys
from datetime import datetime
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())

TITLE_SLUG = "short_english_title"
USE_NANOBANANA2 = True
DECK_SOURCE_JSON = {}

source_path = os.path.join(MNT, f"{TITLE_SLUG}.json")
slides_json_path = os.path.join(MNT, f"{TITLE_SLUG}.slides.json")
pptx_path = os.path.join(MNT, f"{TITLE_SLUG}.pptx")
timer_path = os.path.join(MNT, "deck_generation_timer.json")

with open(source_path, "w", encoding="utf-8") as f:
    json.dump(DECK_SOURCE_JSON, f, ensure_ascii=False, indent=2)

cmd = [
    sys.executable,
    os.path.join(MNT, "deck_source_to_json.py"),
    source_path,
    pptx_path,
    "--json",
    slides_json_path,
    "--assets-dir",
    MNT,
    "--require-agenda",
    "--strict-blocks",
    "--strict-density",
    "--strict-agenda-grouping",
    "--strict-markup",
    "--strict-emphasis",
    "--strict-compact-blocks",
    "--strict-title-style",
    "--strict-text-integrity",
]
if USE_NANOBANANA2:
    cmd.append("--nanobanana2")

subprocess.run(cmd, check=True, cwd=MNT)
finished_at = datetime.now().astimezone()
timer = {}
if os.path.exists(timer_path):
    with open(timer_path, encoding="utf-8") as f:
        timer = json.load(f)
started_at = datetime.fromisoformat(timer["started_at"]) if timer.get("started_at") else finished_at
elapsed_seconds = int((finished_at - started_at).total_seconds())
timer.update({
    "finished_at": finished_at.isoformat(timespec="seconds"),
    "elapsed_seconds": elapsed_seconds,
})
with open(timer_path, "w", encoding="utf-8") as f:
    json.dump(timer, f, ensure_ascii=False, indent=2)
mins, secs = divmod(max(elapsed_seconds, 0), 60)
for fn in [f"{TITLE_SLUG}.json", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
print(f"所要時間: {mins}分{secs}秒")
```

変換出力:
ユーザーへ提示するのはdeck_source.jsonとpptxだけである。slides.jsonは中間生成物として扱い、リンク提示しない。

スキル修正依頼:
ユーザーがこのスキル自体の修正、リファクタリング、検証を求めた場合は、デッキ生成フローへ入らない。nanobanana2のYes/No質問も出さない。対象ファイルを編集し、count_chars.pyとcontext_loader.py validateで検証する。
