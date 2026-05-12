# AGENTS.md

このファイルはCodexがこのプロジェクトで作業する際のガイダンスを定義します。
プロジェクトルートに配置し、Codexが自動的に読み込みます。

---

## SKILL 設計ルール（カスタムGPTs流用前提）

### 目的

SKILL を作成する際の共通ルールを定義する。
作成する SKILL は、最終的にカスタムGPTsへ流用することを前提とする。

### 基本方針

* SKILL は最終的にカスタムGPTsへ流用する前提で設計する。
* `SKILL.md` はカスタムGPTsの**システムプロンプトとして使用する**。
* カスタムGPTsではシステムプロンプトに使える文字数が **5000文字** までである。
* そのため、`SKILL.md` は **必ず5000文字以内** に収める。
* `SKILL.md` は肥大化させず、各ターンで `context.md` を確実に読む責任を持たせる。
* `context.md` も肥大化させず、code interpreter で必要な外部JSONコンテキストを正しいタイミングで読み込ませる司令塔にする。
* 詳細ルール・参照情報・補足仕様は、必要に応じて外部JSONへ分離する。
* 外部JSONコンテキストはターン冒頭で一括読み込みせず、各作業フェーズの直前に必要分だけ取得する。
* Codexにスキル関係の修正指示（新規作成、既存SKILLの編集、改善、検証、運用ルール変更など）が出た場合は、必ず `C:\Users\takuy\.codex\skills\.system\skill-creator\SKILL.md` の `skill-creator` を用いる。

### file search の利用方針

#### 毎ターン必ず再読込する

* カスタムGPTsの仕様として、`file search` により取得したコンテキストは **そのターンのみ有効** である。
* 次のターンでは前ターンで読んだ内容は保持されない前提で扱う。
* したがって、**各ターンの開始時に必ず `file search` を実行してコンテキストを再読込する。**

#### 読み取り対象は `context.md` のみとする

* `file search` は RAG によりアップロード済みファイル群からチャンク単位で検索・読み取りを行う。
* 読み取れるチャンク数は **最大20チャンク** である。
* 複数ファイルに情報を分散すると、必要なコンテキストが離散し、毎ターン安定して回収できない可能性がある。
* そのため、`file search` 用のファイルは **1つに絞る**。
* この単一ファイルの名前は **`context.md`** とする。
* `context.md` は **20000文字以内** に収める。
* `context.md` は文字数削減のため、原則として `*` や `` ` `` によるマークアップを使わない。

#### file search の実行方法

* `file search` では **`queries` のみ利用可能** とする。
* 毎ターン、以下のクエリで必ず `file search` を実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

* SKILL は、必要な前提・ルール・参照情報が `context.md` に入っていることを前提に設計する。
* 毎ターン最初に `context.md` を読むことを、省略してはならない。
* 外部JSONを使う場合も、`file search` の読み取り対象は `context.md` のみとする。JSON本体は `code interpreter` で取得する。

### code interpreter の利用方針

* `file search` のほかに `code interpreter` が利用できる。
* `code interpreter` で実行可能な Python ファイルは **`/mnt/data` 直下にある `.py` ファイルのみ** とする。
* Python が利用する入力ファイルも、必ず **`/mnt/data` 直下** に置く。
* 必要なファイルは以下のいずれかの方法で用意する。
  * `/mnt/data` 直下にアップロードする
  * `/mnt/data` 直下に生成する
  * `/mnt/data` 直下にコピー配置する
* Python 実行時は、必ず `/mnt/data` 直下のファイルを利用する。

#### code interpreter 呼び出しコードの冒頭コメント

カスタムGPTsでは、code interpreter を呼び出す際に `{"code": "（コードの内容）"}` という引数形式を使う。
この `code` の内容は、カスタムGPTsのGUI上でアクティビティとしてユーザーに表示される。
そのため、code interpreter に渡すコード文字列の冒頭には、ユーザーが実行意図を確認できるように短いコメントを必ず入れる。

* コメントは `code` 引数の外側ではなく、実行されるPythonコード本文の先頭に書く。
* コメントは「何のために何を実行するか」を一文で自然に書く。
* コメントは日本語で、ユーザーが読んで安心できる粒度にする。
* `目的:`、`実行内容:`、`出力:` のようにラベルで構造化せず、GUI上でそのまま読める短い説明文にする。
* 長く書きすぎず、通常は1行に収める。
* 秘密情報、APIキー、内部パスの不要な詳細、長い仕様説明はコメントに含めない。
* 1行だけの短い処理でも、少なくとも目的が分かるコメントを付ける。
* 外部JSONの続きを読むcodeでは、直前出力の`NEXT 004/031`などを反映した短い進捗文にする。

例:

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
matches = glob.glob("/mnt/data/*resolve_uploads.py")
if matches:
    exec(open(matches[0]).read())
```

#### code interpreter のコンソールログ制限

カスタムGPTs環境では、code interpreter のコンソールログとしてAIに渡される文字数にも制限がある。
1回の code interpreter 実行でAIが安定して読めるコンソールログは、
**先頭400文字と末尾400文字の合計800文字** である。
800文字を超える場合、中間部分は `...` で省略される前提で設計する。

* code interpreter で長いコンテキストを一括出力してはならない。
* `context_data.json` の個別コンテキストは、**1件あたり800文字以内** にする。
* code interpreter で出力する個別コンテキストは、ログ制限に合わせて必要部分を800文字以内に要約・分割する。
* 実運用では、ヘッダーや進捗表示も含めて800文字以内に収まるよう、本文は720〜760文字程度を目安にする。
* 1回の code interpreter 実行では、原則として個別コンテキストを1件だけ出力する。
* 複数のコンテキストが必要な場合でも、ターン冒頭で全件を読み切ってから作業してはならない。
* 各作業フェーズの直前に、そのフェーズに必要なコンテキストだけを1件ずつ取得し、`DONE` が出てから作業へ進む。
* コンテキストローダーは、現在位置、コンテキストID、NEXT/DONE状態を短く出力する。

#### code interpreter 実行ログ

カスタムGPTsで code interpreter を使うSKILLでは、すべての code interpreter 呼び出しを1つのログファイルに記録する。

* ログファイルは `/mnt/data` 直下に作成する。ファイル名は原則として `code_interpreter_log.md` とする。
* 各 code interpreter 実行ごとに、タイムスタンプ、作業フェーズ、実行目的、実行した処理の要約、入力ファイル、出力ファイル、結果、NEXT/DONE状態を追記する。
* タイムスタンプはISO形式など、後から順序を追える形式にする。
* 外部JSONローダーを呼び出す場合は、読み込んだコンテキストID、何件中何件目か、NEXT/DONE状態を必ずログに残す。
* 生成・変換・検証を行う場合は、対象ファイル、生成物、検証結果の要約をログに残す。
* エラーが発生した場合も、失敗したフェーズ、エラー概要、次に必要な対応をログに残す。
* 秘密情報、APIキー、個人情報、不要な内部パスの詳細はログに書かない。
* ログ追記のための処理も code interpreter の実行コード内に含める。共通ヘルパーを使う場合は、そのSKILLフォルダ直下に置き、実行時は `/mnt/data` 直下へコピー配置して使う。
* 最終回答前には、生成物のダウンロードリンクと一緒に、このログファイルのダウンロードリンクも必ず提示する。

#### 作業計画チェックリストの運用

カスタムGPTs用SKILLでは、スキルを発揮する作業に入る前に、必ず作業計画を細かいMarkdownチェックリストとして `/mnt/data` 直下に作成する。

* チェックリストファイル名は原則として `/mnt/data/task_checklist.md` とする。
* チェックリストは、そのターンの作業フェーズ、各フェーズで読むべきコンテキストID、完了条件、検証項目を含める。
* チェックリストは作業者が直接手編集せず、必ず code interpreter のPythonコードで作成・更新する。
* チェックを入れる処理、進捗確認、次タスク取得、整合性検証はPythonで実行する。
* SKILLフォルダ直下に `checklist_manager.py` を置き、実行時に `/mnt/data` 直下へコピー配置して使う。
* `checklist_manager.py` は、少なくとも `init`、`status`、`next`、`check`、`verify` 相当の操作を提供する。
* `status` と `next` のコンソール出力は、800文字制限に収まるよう、現在フェーズ、完了数、次の1件、必要コンテキストID、NEXT/DONE状態を短く出す。迷走防止に必要な場合は、次に実行する短い `load`、`repeat`、`check` コマンドも出してよい。
* 作業フェーズを始める直前に `next` または `status` で現在位置を確認し、そのフェーズに必要な外部JSONコンテキストを読み、DONEを確認してから実作業へ進む。
* 各作業単位が終わるたびに `check` で対象項目を完了済みにし、`code_interpreter_log.md` にも同じフェーズ、項目ID、結果を追記する。
* 後続フェーズに移る前、または迷子になった場合は、必ず `status` を実行して現在位置と次に読むコンテキストを確認する。
* 作業途中で成果物の単位（例: スライド、章、ファイル、シート）が確定する場合は、親項目の直後にサブチェックリストを挿入できるようにする。
* サブチェックリストの挿入、更新、検証も必ずPythonコードで行い、手編集しない。
* サブ項目も通常項目と同じく `status`、`next`、`check`、`verify` の対象にし、先頭の未完了サブ項目から順番に進める。
* サブ項目を使う場合、1つのサブ項目が完了して `check` されるまで、次の同階層サブ項目や親の後続フェーズへ進まない。
* `check` または `verify` は、未完了項目、重複ID、存在しないコンテキストID、DONE前に進んだフェーズがないかを検査する。
* チェックリストファイルは実行時の一時状態ファイルなので、SKILLフォルダ内には作成しない。必要に応じて最終回答のダウンロードリンクに含める。

チェックリスト作成時のcode interpreter冒頭コメント例:

```python
# 作業の迷子を防ぐため、今回の作業計画をMarkdownチェックリストとして作成し、次に読むコンテキストを確認できるようにします。
from checklist_manager import init_checklist
init_checklist("/mnt/data/task_checklist.md", items)
```

進捗確認時のcode interpreter冒頭コメント例:

```python
# 現在の進捗と次に読むべきコンテキストを800文字以内で確認します。
from checklist_manager import show_status
show_status("/mnt/data/task_checklist.md")
```

チェック更新時のcode interpreter冒頭コメント例:

```python
# 完了した作業項目にチェックを入れ、次に進む前の状態を確認します。
from checklist_manager import check_item
check_item("/mnt/data/task_checklist.md", "P02-T03")
```

#### 外部JSONコンテキストの利用方針

`context.md` だけで詳細ルールを保持できない場合は、SKILLフォルダ直下に外部JSONとローダーを置く。

```text
skill-name/
  SKILL.md
  context.md
  context_data.json
  context_loader.py
  resolve_uploads.py
  ...
```

* `context_data.json` は、800文字以内の小さなコンテキスト片の集合として設計する。
* `context_loader.py` は、フェーズ名またはコンテキストIDを指定して、必要なコンテキスト片を1件ずつ出力する。
* `context.md` には、作業フェーズごとの取得対象、取得順、完了条件だけを書く。
* `context.md` には、フェーズ直前に必要コンテキストを読み、`DONE` 前に生成・変換・検証へ進まないことを明記する。
* 後続フェーズへ移る場合は、その直前に後続フェーズ用のコンテキストを読み込む。
* ローダー出力には、現在位置、コンテキストID、NEXT/DONE状態を短く含める。
* 必須コンテキストが欠落した場合、ローダーはエラーを出し、AIは作業を進めてはならない。

#### アップロードファイルのパス解決

カスタムGPTsのcode interpreter環境では、ユーザーがアップロードしたファイル
（SKILL の Knowledge ファイルを含む）は
**`assistant-{ユニークID}-{元のファイル名}`** という形式に自動リネームされる。
ユニークIDは実行時まで不明なため、スクリプト内でパスをハードコードできない。

これを解消するため、**チャットの一番初めに `resolve_uploads.py` を
code interpreter で1回だけ実行する**。
このスクリプトは `/mnt/data` 直下を走査し、`assistant-{ユニークID}-` プレフィックス付き
ファイルを、プレフィックスなしの元ファイル名で **コピー配置** する。
以降は `/mnt/data/{元のファイル名}` で安定してファイルにアクセスできる。

* `resolve_uploads.py` はプロジェクトルート（`count_chars.py` と同じ場所）に置く。
* **新規作成する SKILL には、必ず SKILL フォルダ直下にこのファイルをコピー配置する。**
* SKILL.md には、チャット冒頭で以下を実行するよう指示を記載する:

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
matches = glob.glob("/mnt/data/*resolve_uploads.py")
if matches:
    exec(open(matches[0]).read())
```

  （`resolve_uploads.py` 自体もカスタムGPTs環境では
  `assistant-{id}-resolve_uploads.py` にリネームされる可能性があるため、
  glob で探してから `exec` する。）

* 実行後は、個別スクリプト側で `assistant-*-{filename}` を glob 検索する
  従来の回避処理は不要になる（ただし互換のため残しておいても害はない）。

#### ダウンロードリンクの貼り方

カスタムGPTs（code interpreter）でユーザーにファイルをダウンロードさせるには、以下のコードを code interpreter で実行する。

```python
print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

* `filename` にはファイル名（例: `deck.pptx`）を入れる。
* 複数ファイルをまとめて提示する場合はループで出力する:

```python
for filename in ["deck.md", "deck.json", "deck.pptx", "code_interpreter_log.md"]:
    print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

* `sandbox:/mnt/data/` プレフィックスがカスタムGPTsのダウンロードリンクとして機能する。このプレフィックスなしでは通常のリンクとして扱われダウンロードできない。
* code interpreter を使ったSKILLでは、最終的なダウンロードリンク一覧に `code_interpreter_log.md` を必ず含める。

### SKILL のディレクトリ構成ルール

* 作成する各 SKILL では、**その SKILL 用フォルダの直下にすべてのファイルを置く**。
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

* `skill-name/refs/` や `skill-name/docs/` のような下位ディレクトリは作成しない。

### SKILL フォルダに置いてはいけないもの

SKILL フォルダ（`.Codex/skills/<skill-name>/`）には、カスタムGPTsにアップロードする
ファイルのみを置く。以下のファイルは SKILL フォルダ内に作成してはならない。

* テストスクリプト（`test_*.py`、`*_test.py` など）
* 実験・計測スクリプト（`overflow_analysis.py`、`measure_*.py` など）
* 計画・仕様書（`*_plan.md`、`TODO.md` など）
* テスト実行結果・集計レポート（`*.csv`、`result_*.md` など）
* 上記を含む一時ファイル全般

これらは `.Codex/plans/` または `.Codex/tests/` など、
**SKILL フォルダの外** に配置する。

### 文字数の計測方法

**文字数チェックには必ず `count_chars.py` を使う。**  
`wc -c` はバイト数を返すため日本語文字を正確にカウントできない。

```bash
python count_chars.py .Codex/skills/<skill-name>/SKILL.md
python count_chars.py .Codex/skills/<skill-name>/SKILL.md .Codex/skills/<skill-name>/context.md
```

`SKILL.md`（上限 5,000文字）と `context.md`（上限 20,000文字）については上限に対する OK / OVER を自動判定して表示する。

外部JSONコンテキストを使うSKILLでは、設計・編集のたびにPythonで以下も確認する。

* `context_data.json` の各個別コンテキストが800文字以内であること。
* `context_loader.py` の実出力が、ヘッダーや進捗表示を含めて800文字以内であること。
* フェーズ定義から参照されるコンテキストIDがすべて存在すること。
* 必須コンテキストの欠落、未参照コンテキスト、重複IDがないこと。

検証専用スクリプトや計測結果は、SKILLフォルダ内に置かず、プロジェクトルート、`.Codex/tests/`、または `.Codex/plans/` などSKILLフォルダ外に置く。

### SKILL 作成時の必須ルール

1. カスタムGPTsへの流用を前提にする。
2. `SKILL.md` をシステムプロンプトとして使う前提で設計する。
3. `SKILL.md` は 5000 文字以内に収める（計測は `python count_chars.py` を使う）。
4. `SKILL.md` には最小限の指示のみを書き、`context.md` 読込を担保する責任を持たせる。
5. `context.md` は外部JSONコンテキスト読込の司令塔にし、詳細本文は収まり切らない場合だけ外部JSONへ分離する。
6. 各ターン開始時に必ず `file search` で `context.md` を再読込する。
7. `file search` では `queries` のみを使う。
8. `context.md` は1ファイルに絞り、20000文字以内にする（計測は `python count_chars.py` を使う）。
9. `context.md` は文字数削減のため、原則として `*` や `` ` `` によるマークアップを使わない。
10. 外部JSONを使う場合、`context.md` には作業フェーズごとの取得対象、取得順、完了条件を必ず書く。
11. 外部JSONの個別コンテキストは各800文字以内にする。
12. 外部JSONの個別コンテキスト文字数とローダー実出力文字数は、設計・編集のたびにPythonで確認する。
13. `code interpreter` に渡す `code` 文字列の冒頭には、何のために何を実行するかが自然に分かる一文コメントを必ず入れる。
14. 外部JSONローダーの出力には、現在のID、何件中何件目か、NEXT/DONE状態を必ず含める。
15. 外部JSONローダーを続けて呼ぶcodeコメントには、直前の`NEXT`値を含めた短い進捗文を書く。
16. 外部JSONコンテキストはターン冒頭で一括読み込みせず、各作業フェーズの直前に必要分だけ読む。
17. 各作業フェーズでは、そのフェーズの必要コンテキストをDONEまで読み切ってから作業へ進む。
18. 後続フェーズへ移る前には、後続フェーズ用のコンテキストをあらためて読み込む。
19. `code interpreter` 呼び出しごとに、`/mnt/data/code_interpreter_log.md` へタイムスタンプ付きで実行ログを追記する。
20. 実行ログには、作業フェーズ、実行目的、入力、出力、結果、NEXT/DONE状態、エラー概要を必要に応じて記録する。
21. 最終回答前には、生成物と一緒に `code_interpreter_log.md` のダウンロードリンクも必ず提示する。
22. `code interpreter` で使う `.py` および関連ファイルは `/mnt/data` 直下に置く。
23. SKILL フォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。
24. 各 SKILL フォルダ直下には `resolve_uploads.py` を必ずコピー配置する。
25. SKILL.md には「チャット冒頭で `resolve_uploads.py` を code interpreter で実行する」指示を必ず記載する。
26. スキルを発揮する作業に入る前に、必ず `/mnt/data/task_checklist.md` をMarkdownチェックリストとして作成する。
27. チェックリストの作成、チェック更新、進捗確認、整合性検証は必ずPythonコードで行う。
28. 各作業フェーズの直前にチェックリストで現在位置を確認し、その時点で必要なコンテキストだけを読み込む。
29. チェックリストの進捗確認出力は800文字以内に収め、現在フェーズ、完了数、次タスク、必要コンテキストID、NEXT/DONE状態を短く出す。必要なら次に実行する短い `load`、`repeat`、`check` コマンドも含める。
30. 新規作成するSKILLには、必要に応じてSKILLフォルダ直下に `checklist_manager.py` を配置し、実行時は `/mnt/data` 直下へコピーして使う。
31. 成果物単位が作業途中で確定する場合は、Pythonで親項目直後にサブチェックリストを挿入できるようにする。
32. サブチェックリストも `status`、`next`、`check`、`verify` の対象にし、1項目ずつ順番に完了させる。
