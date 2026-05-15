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
* `SKILL.md`は肥大化させず、毎ターン`context.md`を読む責任だけを持たせる。
* `SKILL.md`はブートローダーとして扱い、詳細な運用判断、生成方針、検証、修復、出力手順は`context.md`へ委任する。
* `context.md`はfile searchで読む唯一のコンテキストにし、ターン判定と運用手順の司令塔にする。詳細ルール本文は必要に応じて`context_data.json`へ分離する。
* 外部JSONを使う場合、AIは`context.md`でフェーズを判定し、`context_loader.py`で必要な詳細を1件ずつ読む。
* 外部JSONコンテキストはターン冒頭で一括読み込みせず、作業へ入る直前に必須フェーズ群をすべて`DONE`まで読む。
* 初回生成の品質に関わる修復系・検証系コンテキストは、strictエラー後だけでなく生成前に読む`preflight_quality`などの必須フェーズへ含める。

### SKILL.md と context.md の責務分離

* `SKILL.md`には、スキルの用途、毎ターン`context.md`をfile searchで読むこと、以後は`context.md`に従うことだけを書く。
* `SKILL.md`には、ターンA/B判定、外部JSONフェーズ名、生成方針、JSON構造、変換コード、strict修復手順などの詳細ルールを書かない。
* `SKILL.md`へ詳細ルールを追加したくなった場合は、原則として`context.md`または`context_data.json`へ移す。
* スキル自体の修正、リファクタリング、検証を依頼された場合に生成フローへ入らないことは、`SKILL.md`と`context.md`の両方で分かるようにする。
* `resolve_uploads.py`の実行手順やcode interpreter用コード例は、原則として`context.md`に置く。`SKILL.md`には詳細コードを置かない。

### 原文変換系SKILLの忠実性

原文ソースを資料化、スライド化、要約、再構成、読み上げ原稿化するSKILLでは、見栄えのために原文のストーリーを作り替えない。

* 生成前に、原文の論理順、主張、根拠、例、注意点、結論を内部的な`source_spine`として固定する。
* スライドや本文の順序は、原則として`source_spine`の順序に従う。PREP、SDSなどの型に合わせるために原文の話順を大きく並べ替えない。
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
* 外部JSONの続きを読むcodeでは、直前出力の`NEXT 004/031 KEY ab12cd34`などを反映した進捗文にし、コマンドにもそのKEYを渡す。

初回コードの型:

```python
# アップロード済みファイル名を安定化するため、resolve_uploads.pyを探して実行し、後続処理で /mnt/data/{元ファイル名} を使えるようにします。
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
```

#### code interpreter のコンソールログ制限

カスタムGPTs環境では、code interpreterのコンソールログとしてAIに安定して渡る文字数は、先頭400文字と末尾400文字の合計800文字である。
800文字を超える場合、中間部分は`...`で省略される前提で設計する。

* code interpreterで長いコンテキストを一括出力してはならない。
* `context_data.json`の個別コンテキストは、1件あたり800文字以内にする。
* ローダー出力は、ヘッダー、本文、進捗フッターを含めて800文字以内に収める。
* `context_loader.py`は1回に1チャンクだけ出力する。
* 複数チャンクを読む時は、1回のcode interpreter実行につき`context_loader.py`を1回だけ起動する。
* ループ、複数の`subprocess.run`、複数の`exec`などで、同じcode本文内からローダーを2回以上起動してはならない。
* 続きの取得コードの冒頭コメントは固定文にせず、前回の`NEXT`値と`KEY`値を写して進捗がGUI上でも分かるようにする。

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
* `context_loader.py`は状態ファイルに現在フェーズ、次に読む位置、次回KEYのハッシュを保存し、次回の`next <KEY>`で続きを出す。
* ローダーの通常フローは、`start <phase>`でフェーズを開始し、出力末尾の`NEXT 次/総数 KEY 値`を次の`next <KEY>`へ渡して`DONE`まで読む。
* 公開コマンドは、実装に合わせて`start <phase>`、`next <KEY>`、`status`、`validate`に絞る。
* `next`は必ず前回出力された`KEY`を要求する。KEYは1回ごとに更新し、状態ファイルにはKEYそのものではなくハッシュだけを保存する。
* KEY方式は、同じcode interpreter本文内でローダーをループ実行して一括取得してしまうことを防ぐためのゲートである。`next`を無引数で動かせる実装にしてはならない。
* `get <chunk_id>`のようにKEYなしで任意チャンクを読める通常コマンドは作らない。必要なデバッグ用途がある場合も、通常フローや`context.md`には案内しない。
* フェーズを切り替える場合は、必要な作業を終えてから新しいフェーズを`start <phase>`で開始する。
* 初回生成に必要な品質ルールが複数フェーズへ分かれている場合は、`context.md`に必須フェーズ群と読み込み順を書く。生成フェーズだけを読んで本作業へ進んではならない。
* ローダー出力の先頭には`[ctx 現在/総数 chunk_id]`を置く。
* ローダー出力の末尾には`NEXT 次/総数 KEY 値`または`DONE 総数/総数`を置く。
* 出力末尾が`NEXT`なら、そのKEYを次回codeコメントと`next <KEY>`コマンドに写して次を読む。`DONE`ならそのフェーズの読み切り完了である。
* 必要フェーズが`DONE`になるまで、分析、生成、変換、修復の本作業へ進まない。
* 必須コンテキストが欠落した場合、ローダーはエラーを出し、AIは作業を進めてはならない。

最初の取得コードの型:

```python
# turn_b_yes用の詳細コンテキスト読み込みを開始し、何件中何件目まで読めたかとNEXT/DONE状態を表示します。
import glob, subprocess, sys
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0], encoding="utf-8").read())
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "start", "turn_b_yes"], check=True)
```

続きの取得コードの型:

```python
# 前回表示されたNEXT 002/031 KEY ab12cd34に従い、詳細コンテキスト002/031を読み込んで次のNEXT/DONE状態を確認します。
import subprocess, sys
subprocess.run([sys.executable, "/mnt/data/context_loader.py", "next", "ab12cd34"], check=True)
```

上の`002/031`と`ab12cd34`は例であり、固定文のまま使い回さない。
前回出力末尾が`NEXT 004/031 KEY ef567890`なら、次のcodeコメントとコマンドも`004/031`と`ef567890`に書き換える。

### 生成・変換スクリプトの検証方針

外部JSONコンテキストの読了が品質や安全性に直結するSKILLでは、スクリプト側に実装済みのstrict検証を使う。

* 生成・変換前に、必要な必須フェーズ群をすべて`DONE`まで読み切ったことをAIの手順として担保する。
* 修復フェーズに初回品質へ効くルールがある場合は、同じ内容を`preflight_quality`などで生成前に読ませる。初回生成後のstrictエラーまで品質ルールを遅延させない。
* 変換スクリプトには、実装済みの`--strict-*`系オプションを本番手順で使わせる。
* スクリプトに存在しない状態ゲートや未実装オプションを、AGENTS.mdの必須ルールとして書かない。
* strictエラーが出た場合は、該当する修復フェーズを`start <phase>` / `next <KEY>`方式で`DONE`まで読み、修復してから再実行する。

### アップロードファイルのパス解決

カスタムGPTsのcode interpreter環境では、ユーザーがアップロードしたファイルやSKILLのKnowledgeファイルが、`assistant-{ユニークID}-{元のファイル名}`形式へ自動リネームされる。
ユニークIDは実行時まで不明なため、スクリプト内でパスをハードコードできない。

これを解消するため、チャット開始直後に`resolve_uploads.py`をcode interpreterで1回実行する。
このスクリプトは`/mnt/data`直下を走査し、`assistant-{ユニークID}-`プレフィックス付きファイルを、プレフィックスなしの元ファイル名でコピー配置する。
以降は`/mnt/data/{元のファイル名}`で安定してアクセスできる。

* `resolve_uploads.py`はプロジェクトルートに置く。
* 新規作成するSKILLには、必ずSKILLフォルダ直下にも`resolve_uploads.py`をコピー配置する。
* SKILL.mdには、チャット冒頭で`resolve_uploads.py`をglobで探して実行する指示を記載する。
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
* `start <phase>`、`next <KEY>`、`status`、`validate`の基本動作を検証すること。
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
13. 外部JSONローダーは`start <phase>` / `next <KEY>`を中心にした状態機械として実装する。
14. 外部JSONローダーの出力には、`[ctx 現在/総数 chunk_id]`と`NEXT 次/総数 KEY 値`または`DONE 総数/総数`を必ず含める。
15. 外部JSONローダーを続けて呼ぶcodeコメントとコマンドには、直前の`NEXT`値と`KEY`値を含める。
16. 外部JSONローダーは、無引数`next`と古いKEYの再利用を拒否することを検証する。
17. 外部JSONコンテキストはターン冒頭で一括読み込みせず、作業直前に必須フェーズ群をすべて読む。
18. 初回品質に必要な修復系・検証系コンテキストは、`preflight_quality`などの生成前必須フェーズに含める。
19. 各作業フェーズでは、そのフェーズの必要コンテキストを`DONE`まで読み切ってから作業へ進む。
20. 後続フェーズや修復フェーズへ移る場合は、現在の作業を終えてから新しいフェーズを`start <phase>`で開始する。
21. `code interpreter`で使う`.py`および関連ファイルは`/mnt/data`直下に置く。
22. SKILLフォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。
23. 各SKILLフォルダ直下には`resolve_uploads.py`を必ずコピー配置する。
24. `resolve_uploads.py`をcode interpreterで実行する指示は、原則として`context.md`へ記載する。
25. 生成・変換スクリプトには、実装済みのstrict検証オプションを本番手順で使わせる。
26. 原文変換系SKILLでは、原文の論理順、主張、根拠、結論を固定してから厚み付けし、noteや話者原稿が本文と乖離しないように設計する。
