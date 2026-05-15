# AGENTS.md

このファイルはCodexがこのプロジェクトで作業する際のガイダンスを定義します。
プロジェクトルートに配置し、Codexが自動的に読み込みます。

---

## SKILL 設計ルール（カスタムGPTs流用前提）

### 目的

SKILLを作成・更新する際の共通ルールを定義する。
作成するSKILLは、最終的にカスタムGPTsへ流用することを前提とする。

### 基本方針

* SKILLはカスタムGPTsへ流用できる形で設計する。
* `SKILL.md`はカスタムGPTsのシステムプロンプトとして使用する前提で書く。
* カスタムGPTsのシステムプロンプト上限に合わせ、`SKILL.md`は必ず5000文字以内に収める。
* `SKILL.md`は肥大化させず、毎ターン`context.md`を読む責任と、カスタムGPTs用アプリ共通レイヤーの安定化責任を持たせる。
* `SKILL.md`はブートローダーとして扱い、詳細な運用判断、生成方針、検証、修復、出力手順は`context.md`へ委任する。ただし、file search、code interpreter、アップロード解決、ログ制限、外部JSON読込ゲート、処理時間計測など、スキルの本質ではなく実行基盤の安定性に関わる内容は`SKILL.md`へ書く。
* `context.md`はfile searchで読む唯一のコンテキストにし、ターン判定と運用手順の司令塔にする。詳細ルール本文は必要に応じて`context_data.json`へ分離する。
* 外部JSONを使う場合、AIは`context.md`でフェーズを判定し、`context_loader.py`で必要な詳細を1件ずつ読む。
* 外部JSONコンテキストはターン冒頭で一括読み込みせず、作業へ入る直前に必須フェーズ群をすべて`DONE`まで読む。
* 初回生成の品質に関わる修正用・検証用コンテキストは、strictエラー後だけでなく、source_spine、スライド構成、本文生成を考え始める前にすべて読む必須フェーズへ含める。重複読込が多い場合は、修正用統合フェーズを作り、そこに修正用コンテキストを束ねる。

### SKILL.md と context.md の責務分離

* `SKILL.md`には、スキルの用途、毎ターン`context.md`をfile searchで読むこと、以後は`context.md`に従うことを書く。
* `SKILL.md`には、カスタムGPTs用アプリ共通レイヤーとして、file searchの実行クエリ、code interpreter冒頭コメント、resolve_uploads.pyの初回実行、ログ800字制限、外部JSONローダーの1チャンク実行、`start <phase>` / `next`方式、DONE確認前の生成禁止、処理時間計測を書く。
* `SKILL.md`には、ターンA/B判定、外部JSONフェーズ名、生成方針、JSON構造、変換コード、strict修復手順などの詳細ルールを書かない。
* 分割コンテキスト読込ゲートには、ユーザー向け所要時間の宣言、DONE確認前の生成禁止、`start <phase>` / `next`方式、空出力時の`last`復旧、エラー時に生成へ進まないことを書く。生成方針の詳細は書かない。ユーザーへは`DONE`、`NEXT`などの内部処理名を説明せず、必要な待ち時間の目安を出す。
* `SKILL.md`へ詳細ルールを追加したくなった場合は、原則として`context.md`または`context_data.json`へ移す。
* スキル自体の修正、リファクタリング、検証を依頼された場合に生成フローへ入らないことは、`SKILL.md`と`context.md`の両方で分かるようにする。
* `resolve_uploads.py`の初回実行手順は、カスタムGPTs共通レイヤーとして`SKILL.md`にも置く。ただし所要時間案内が必要な生成ターンでは、案内チャットを出した後に初回code interpreterで実行する。生成や変換の詳細コードは`context.md`に置く。

### 原文変換系SKILLの忠実性

原文ソースを資料化、スライド化、要約、再構成、読み上げ原稿化するSKILLでは、見栄えのために原文のストーリーを作り替えない。

* 生成前に、原文の論理順、主張、根拠、例、注意点、結論を内部的な`source_spine`として固定する。
* 原文に章立てや見出し立てがある場合は、章、見出し、主張、根拠、例、注意点、結論を内部的な`source_spine`として固定する。
* スライドや本文の順序は、原則として`source_spine`の順序に従う。PREP、SDSなどの型に合わせるために原文の話順、章立て、見出し立てを大きく並べ替えない。
* 原文の章見出しは、可能な限り`slides[].section`へ反映する。原文の小見出しや段落見出しは、意味を変えずに短く整えて`slides[].title`へ反映する。
* 章の統合や改名が必要な場合も、隣接する章に限り、原文の親子関係や順序を崩さない範囲で行う。
* 厚み付けは、原文から自然に導ける背景、理由、含意、注意点、判断基準に限定する。
* 原文にない固有数値、事例名、成果、専門用語、新しい主張を作らない。
* noteや話者原稿は、スライド本文と原文参照から乖離させない。noteにしかない重要情報が出た場合は、noteではなく本文側を修正する。
* noteを読み上げ原稿にする場合も、材料はスライドの`title`、`message`、`blocks`、原文参照に限定する。

### file search の利用方針

#### 毎ターン必ず再読込する

* カスタムGPTsでは、`file search`で取得したコンテキストはそのターンのみ有効である。
* 次のターンでは前ターンで読んだ内容は保持されない前提で扱う。
* 各ターン開始時に必ず`file search`を実行し、`context.md`を再読込する。

#### 読み取り対象は `context.md` のみとする

* `file search`はRAGによりアップロード済みファイル群からチャンク単位で検索・読み取りを行う。
* 読み取れるチャンク数は最大20チャンクである。
* 複数ファイルに情報を分散すると、必要なコンテキストが離散し、毎ターン安定して回収できない可能性がある。
* そのため、`file search`用のファイルは1つに絞り、名前は`context.md`とする。
* `context.md`は20000文字以内に収める。
* `context.md`は文字数削減のため、原則として`*`や`` ` ``によるマークアップを使わない。

#### file search の実行方法

* `file search`では`queries`のみを使う。
* 毎ターン、以下のクエリだけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

* SKILLは、必要な前提・ルール・参照情報が`context.md`に入っていることを前提に設計する。
* 外部JSONを使う場合も、`file search`の読み取り対象は`context.md`のみとする。JSON本体は`code interpreter`で取得する。

### code interpreter の利用方針

* `file search`のほかに`code interpreter`を利用できる。
* `code interpreter`で実行する`.py`ファイル、およびPythonが利用する入力ファイルは`/mnt/data`直下に置く。
* 必要なファイルは、アップロード、生成、またはコピーにより`/mnt/data`直下へ用意する。
* Python実行時は`/mnt/data/{ファイル名}`で安定して参照できる状態にする。

#### code interpreter 呼び出しコードの冒頭コメント

カスタムGPTsでは、code interpreterに渡す`code`本文がGUI上のアクティビティとしてユーザーに表示される。
そのため、実行されるPythonコード本文の先頭には、何のために何を実行するかが分かる日本語の一文コメントを必ず置く。

* コメントは`code`引数の外側ではなく、Pythonコード本文の先頭に書く。
* コメントは自然文で短く書き、通常は1行に収める。
* `目的:`、`実行内容:`、`出力:`のようなラベル構造にはしない。
* 秘密情報、APIキー、内部パスの不要な詳細、長い仕様説明は含めない。
* 外部JSONの続きを読むcodeでは、直前出力の`NEXT 004/031`などを反映した進捗文にし、コマンドは`context_loader.py next`にする。

初回コードの型:

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

#### 処理時間の通知と計測

カスタムGPTsで資料化、スライド化、PPTX生成など数分かかる生成処理を行うSKILLでは、ユーザーに内部の分割コンテキスト読込を意識させず、処理時間の見通しと実測結果を出す。

* 生成開始時のチャットでは、`DONE`、`NEXT`などの内部処理名ではなく、おおよその所要時間を伝える。
* `deck-from-source`の資料化処理は、おおよそ5分程度かかるものとして案内する。
* 所要時間の案内は、file searchで`context.md`を読み生成ターンだと判断した直後、最初のcode interpreterを開始する前に、独立したチャット本文として出す。code interpreter冒頭コメント、ツール実行ログ、最終報告だけで代替してはならない。
* 分割コンテキストを読む前の最初のcode interpreterで現在時刻を取得し、`/mnt/data/{skill_name}_timer.json`などの状態ファイルへ開始時刻を保存する。
* スライド修正やstrict修復が必要な生成処理では、それらの修正がすべて終わり、最終成果物を出力できる状態になった時点を終了時刻とする。
* 最終チャットでは、成果物リンクとあわせて、開始時刻や終了時刻は表示せず、所要時間だけを短くコメントする。
* 時刻計測は共通レイヤーの処理であり、各SKILLの生成方針や品質ルール本文へ埋め込まない。実装コードの詳細は`context.md`へ置いてよい。

#### code interpreter のコンソールログ制限

カスタムGPTs環境では、code interpreterのコンソールログとしてAIに安定して渡る文字数は、先頭400文字と末尾400文字の合計800文字である。
800文字を超える場合、中間部分は`...`で省略される前提で設計する。

* code interpreterで長いコンテキストを一括出力してはならない。
* `context_data.json`の個別コンテキストは、1件あたり800文字以内にする。
* ローダー出力は、ヘッダー、本文、進捗フッターを含めて800文字以内に収める。
* `context_loader.py`は1回に1チャンクだけ出力する。
* 複数チャンクを読む時は、1回のcode interpreter実行につき`context_loader.py`を1回だけ起動する。
* ループ、複数の`subprocess.run`、複数の`exec`などで、同じcode本文内からローダーを2回以上起動してはならない。
* 続きの取得コードの冒頭コメントは固定文にせず、前回の`NEXT`値を写して進捗がGUI上でも分かるようにする。

### 外部JSONコンテキストの利用方針

`context.md`だけで詳細ルールを保持できない場合は、SKILLフォルダ直下に外部JSONとローダーを置く。

```text
skill-name/
  SKILL.md
  context.md
  context_data.json
  context_loader.py
  resolve_uploads.py
  ...
```

* `context_data.json`は、800文字以内の小さなコンテキスト片の集合として設計する。
* `context_loader.py`は状態ファイルに現在フェーズと次に読む位置を保存し、次回の`next`で続きを出す。
* ローダーの通常フローは、`start <phase>`でフェーズを開始し、出力末尾が`NEXT 次/総数`なら次は`next`、`DONE 総数/総数`なら読了とする。
* 公開コマンドは、実装に合わせて`start <phase>`、`next`、`last`、`status`、`validate`に絞る。
* code interpreterの出力が空、または直前のチャンク表示を見失った場合は、同じ処理を再実行せず`last`を1回だけ実行して直前の正常出力を再表示する。
* `last`でも戻らない場合だけ、現在フェーズを`start <phase>`から読み直す。
* `get <chunk_id>`のように任意チャンクを読める通常コマンドは作らない。必要なデバッグ用途がある場合も、通常フローや`context.md`には案内しない。
* フェーズを切り替える場合は、必要な作業を終えてから新しいフェーズを`start <phase>`で開始する。
* 初回生成に必要な品質ルールや修正ルールが複数フェーズへ分かれている場合は、`context.md`に必須フェーズ群と読み込み順を書く。生成フェーズだけを読んで本作業へ進んではならない。
* ローダー出力の先頭には`[ctx 現在/総数 chunk_id]`を置く。
* ローダー出力の末尾には`NEXT 次/総数`または`DONE 総数/総数`を置く。
* 出力末尾が`NEXT`なら次回は`next`で読む。`DONE`ならそのフェーズの読み切り完了である。
* 必要フェーズが`DONE`になるまで、分析、生成、変換、修復の本作業へ進まない。
* 必須コンテキストが欠落した場合、ローダーはエラーを出し、AIは作業を進めてはならない。

最初の取得コードの型:

```python
# turn_b_yes用の詳細コンテキスト読み込みを開始する前に処理開始時刻を記録します。
import glob, json, subprocess, sys
from datetime import datetime
with open("/mnt/data/skill_timer.json", "w", encoding="utf-8") as f:
    json.dump({"started_at": datetime.now().astimezone().isoformat(timespec="seconds")}, f, ensure_ascii=False)
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "start", "turn_b_yes"], check=True)
```

続きの取得コードの型:

```python
# 前回表示されたNEXT 002/031に従い、詳細コンテキスト002/031を読み込んで次のNEXT/DONE状態を確認します。
import subprocess, sys
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "next"], check=True)
```

上の`002/031`は例であり、固定文のまま使い回さない。
前回出力末尾が`NEXT 004/031`なら、次のcodeコメントも`004/031`に書き換え、コマンドは同じ`next`を使う。

### 生成・変換スクリプトの検証方針

外部JSONコンテキストの読了が品質や安全性に直結するSKILLでは、スクリプト側に実装済みのstrict検証を使う。

* 生成・変換前に、必要な必須フェーズ群をすべて`DONE`まで読み切ったことをAIの手順として担保する。
* 修復フェーズに初回品質へ効くルールがある場合は、必要な修正用コンテキストを生成前必須フェーズへ含める。重複を避けるため、`preflight_quality`のような修正用統合フェーズへrepair系チャンクを束ねてよいが、その統合フェーズを`DONE`まで読むまでは生成へ進まない。
* 変換スクリプトには、実装済みの`--strict-*`系オプションを本番手順で使わせる。
* スクリプトに存在しない状態ゲートや未実装オプションを、AGENTS.mdの必須ルールとして書かない。
* strictエラーが出た場合は、該当する修復フェーズを`start <phase>` / `next`方式で`DONE`まで読み、修復してから再実行する。

### アップロードファイルのパス解決

カスタムGPTsのcode interpreter環境では、ユーザーがアップロードしたファイルやSKILLのKnowledgeファイルが、`assistant-{ユニークID}-{元のファイル名}`形式へ自動リネームされる。
ユニークIDは実行時まで不明なため、スクリプト内でパスをハードコードできない。

これを解消するため、初回code interpreterで`resolve_uploads.py`を1回実行する。所要時間案内が必要な生成ターンでは、案内チャットを先に出してから実行する。
このスクリプトは`/mnt/data`直下を走査し、`assistant-{ユニークID}-`プレフィックス付きファイルを、プレフィックスなしの元ファイル名でコピー配置する。
以降は`/mnt/data/{元のファイル名}`で安定してアクセスできる。

* `resolve_uploads.py`はプロジェクトルートに置く。
* 新規作成するSKILLには、必ずSKILLフォルダ直下にも`resolve_uploads.py`をコピー配置する。
* SKILL.mdには、初回code interpreterで`resolve_uploads.py`をglobで探して実行する指示を記載する。所要時間案内が必要な生成ターンでは、案内チャットより前に実行する書き方にしない。
* `resolve_uploads.py`自体も`assistant-{id}-resolve_uploads.py`にリネームされる可能性があるため、globで探してから`exec`する。
* 実行後は、個別スクリプト側で`assistant-*-{filename}`をglob検索する回避処理は不要になる。ただし互換のため残すことは許容する。

### ダウンロードリンクの貼り方

カスタムGPTsのcode interpreterでユーザーにファイルをダウンロードさせるには、以下の形式を出力する。

```python
print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

複数ファイルを提示する場合:

```python
for filename in ["deck.json", "deck.pptx"]:
    print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

* `sandbox:/mnt/data/`プレフィックスがカスタムGPTsのダウンロードリンクとして機能する。
* 中間生成物は、ユーザーに必要な場合を除いてリンク提示しない。

### SKILL のディレクトリ構成ルール

* 作成する各SKILLでは、そのSKILL用フォルダの直下にすべてのファイルを置く。
* サブディレクトリを作成して、その中に分類して格納する構成は採用しない。

```text
skill-name/
  SKILL.md
  context.md
  context_data.json
  context_loader.py
  resolve_uploads.py
  example.md
  script.py
  ...
```

* `skill-name/refs/`や`skill-name/docs/`のような下位ディレクトリは作成しない。

### SKILL フォルダに置いてはいけないもの

SKILLフォルダ（`.agents/skills/<skill-name>/`）には、カスタムGPTsにアップロードするファイルのみを置く。
以下のファイルはSKILLフォルダ内に作成してはならない。

* テストスクリプト（`test_*.py`、`*_test.py`など）
* 実験・計測スクリプト（`overflow_analysis.py`、`measure_*.py`など）
* 計画・仕様書（`*_plan.md`、`TODO.md`など）
* テスト実行結果・集計レポート（`*.csv`、`result_*.md`など）
* 上記を含む一時ファイル全般

これらはプロジェクトルート、`.agents/tests/`、`.agents/plans/`など、SKILLフォルダの外に配置する。

### 文字数とコンテキストの検証

文字数チェックには必ず`count_chars.py`を使う。
`wc -c`はバイト数を返すため、日本語文字を正確にカウントできない。

```bash
python count_chars.py .agents/skills/<skill-name>/SKILL.md
python count_chars.py .agents/skills/<skill-name>/SKILL.md .agents/skills/<skill-name>/context.md
```

`SKILL.md`は5000文字以内、`context.md`は20000文字以内にする。

外部JSONコンテキストを使うSKILLでは、設計・編集のたびにPythonで以下を確認する。

* `context_data.json`の各個別コンテキストが800文字以内であること。
* `context_loader.py`の実出力が、ヘッダーや進捗表示を含めて800文字以内であること。
* 各フェーズから参照されるコンテキストIDがすべて存在すること。
* 必須コンテキストの欠落、未参照コンテキスト、重複IDがないこと。
* `start <phase>`、`next`、`last`、`status`、`validate`の基本動作を検証すること。
* 通常フローで使わない補助コマンドがある場合は、用途を限定してSKILL.mdまたはcontext.mdへ書くこと。

検証専用スクリプトや計測結果は、SKILLフォルダ内に置かず、プロジェクトルート、`.agents/tests/`、`.agents/plans/`などSKILLフォルダ外に置く。

### SKILL 作成時の必須ルール

1. カスタムGPTsへの流用を前提にする。
2. `SKILL.md`をシステムプロンプトとして使う前提で設計する。
3. `SKILL.md`は5000文字以内に収める。
4. `SKILL.md`には最小限の指示のみを書き、`context.md`読込を担保する責任だけを持たせる。
5. `context.md`はターン判定、生成方針、検証、修復、外部JSONコンテキスト読込の司令塔にし、詳細本文は必要に応じて`context_data.json`へ分離する。
6. 各ターン開始時に必ず`file search`で`context.md`を再読込する。
7. `file search`では`queries`のみを使う。
8. `context.md`は1ファイルに絞り、20000文字以内にする。
9. `context.md`は文字数削減のため、原則として`*`や`` ` ``によるマークアップを使わない。
10. 外部JSONを使う場合、`context.md`にはローダーの公開コマンド、取得手順、停止条件、同一code本文内でローダーを複数回起動しないことを書く。
11. 外部JSONの個別コンテキストとローダー実出力は800文字以内にする。
12. `code interpreter`に渡す`code`本文の冒頭には、何のために何を実行するかが自然に分かる日本語の一文コメントを必ず入れる。
13. 数分かかる生成処理では、file searchで生成ターンだと判断した直後、最初のcode interpreterの前に、所要時間の目安を独立したチャット本文でユーザーへ伝え、code interpreterで開始時刻と終了時刻を取得し、最終チャットでは実測所要時間だけをコメントする。
14. ユーザー向け進行宣言では、`DONE`、`NEXT`などの内部処理名を説明しない。
15. 外部JSONローダーは`start <phase>` / `next`を中心にした状態機械として実装する。
16. 外部JSONローダーの出力には、`[ctx 現在/総数 chunk_id]`と`NEXT 次/総数`または`DONE 総数/総数`を必ず含める。
17. 外部JSONローダーを続けて呼ぶcodeコメントには、直前の`NEXT`値を含める。コマンドは`next`にする。
18. code interpreterの出力が空、または直前のチャンク表示を見失った場合に備え、状態を進めず直前出力を再表示する`last`を実装し、手順に明記する。
19. `last`でも復旧できない場合だけ、現在フェーズを`start <phase>`から読み直す手順を明記する。
20. 外部JSONコンテキストはターン冒頭で一括読み込みせず、作業直前に必須フェーズ群をすべて読む。
21. 初回品質に必要な修正用・検証用コンテキストは、source_spine、構成、本文、変換を考える前に読む生成前必須フェーズに含める。修正用統合フェーズを使う場合は、そのフェーズが全repair系チャンクを含むことを明記する。
22. 各作業フェーズでは、そのフェーズの必要コンテキストを`DONE`まで読み切ってから作業へ進む。
23. 後続フェーズや修復フェーズへ移る場合は、現在の作業を終えてから新しいフェーズを`start <phase>`で開始する。
24. `code interpreter`で使う`.py`および関連ファイルは`/mnt/data`直下に置く。
25. SKILLフォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。
26. 各SKILLフォルダ直下には`resolve_uploads.py`を必ずコピー配置する。
27. `resolve_uploads.py`をcode interpreterで実行する指示は、原則として`context.md`へ記載する。
28. 生成・変換スクリプトには、実装済みのstrict検証オプションを本番手順で使わせる。
29. 原文変換系SKILLでは、原文の論理順、主張、根拠、結論を固定してから厚み付けし、noteや話者原稿が本文と乖離しないように設計する。
