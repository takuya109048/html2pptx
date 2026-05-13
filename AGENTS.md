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
* `context.md` も肥大化させず、code interpreter の状態機械ローダーを正しく使わせる薄い司令塔にする。
* 詳細ルール・参照情報・補足仕様は、必要に応じて外部JSONへ分離する。
* 外部JSONのフェーズ順、分岐、次に読むチャンクの判断は、原則として `context_loader.py` に持たせる。
* 外部JSONコンテキストはターン冒頭で一括読み込みせず、各作業フェーズの直前に必要分だけ取得する。

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
* 1回の code interpreter コード本文では、原則として個別コンテキストを1件だけ出力する。
* 同じターン内で code interpreter 呼び出しを複数回に分け、1チャンクずつ取得することは正しい。
* 禁止するのは、1つの code interpreter コード本文の中でループ、関数、複数の `subprocess.run`、複数の `exec` などを使い、ローダーを2回以上起動することである。
* 複数のコンテキストが必要な場合でも、ターン冒頭で全件を読み切ってから作業してはならない。
* 各作業フェーズの直前に、そのフェーズに必要なコンテキストだけを1件ずつ取得し、`DONE` が出てから作業へ進む。
* コンテキストローダーは、現在位置、フェーズ、NEXT/DONE状態、次回用ACKを短く出力する。

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
* `context_loader.py` は状態機械として設計し、フェーズ順、分岐、次に読むチャンク、DONE判定を内部で管理する。
* ローダーの公開コマンドは、原則として `init <route>`、`advance <ACK>`、`phase-done <ACK>`、`repair <type>`、`repeat`、`status`、`validate` のような少数に絞る。
* `read <phase> <number>`、`get <chunk_id>`、フェーズ名の直接指定など、AIが番号を回して一括取得しやすいAPIは作らない。互換用に残す場合も通常利用では拒否する。
* `context.md` には、詳細なフェーズ表ではなく、ローダーの公開コマンド、取得手順、停止条件、同一コード本文内で複数回ローダーを起動しないことを書く。
* ローダーは出力末尾に `NEXT 002/006 ACK xxxxxxxx` または `DONE 006/006 ACK xxxxxxxx` のような短い進捗を出す。
* ACKはstateファイルへ平文保存せず、ハッシュなど照合用の形で保存する。`status` ではACKを再表示せず、出力を見失った場合だけ `repeat` で新しいACKを再発行する。
* 後続フェーズへ移る場合は、現在フェーズがDONEになり、そのフェーズの作業を終えてから `phase-done <ACK>` で次フェーズの最初の1チャンクだけを読む。
* ローダー出力には、現在位置、フェーズ、NEXT/DONE状態、ACKを短く含める。
* 必須コンテキストが欠落した場合、ローダーはエラーを出し、AIは作業を進めてはならない。

#### 生成・変換スクリプトの状態ゲート

外部JSONコンテキストの読了が品質や安全性に直結するSKILLでは、生成・変換・検証スクリプト側にも状態ゲートを置く。

* 最終変換や成果物生成の前に、該当フェーズがDONEになっていることをstateファイルで確認するオプションを用意する。
* 例: `--require-context-done` のような明示オプションを付けた場合、必要フェーズがDONEでなければ変換を拒否する。
* ゲートは通常運用を壊さないよう任意オプションにしてよいが、SKILLの本番手順では必ずそのオプションを使わせる。
* stateファイルがない、壊れている、必要フェーズが未完了の場合は、スクリプトはエラーを出して成果物生成へ進まない。

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
for filename in ["deck.md", "deck.json", "deck.pptx"]:
    print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

* `sandbox:/mnt/data/` プレフィックスがカスタムGPTsのダウンロードリンクとして機能する。このプレフィックスなしでは通常のリンクとして扱われダウンロードできない。

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
* 状態機械の各ルートから参照されるフェーズとコンテキストIDがすべて存在すること。
* 必須コンテキストの欠落、未参照コンテキスト、重複IDがないこと。
* `init`、`advance <ACK>`、`phase-done <ACK>`、`repeat`、`status`、`validate` の基本動作を検証すること。
* 旧APIや直接指定APIを無効化している場合は、それらが正常に拒否されること。

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
10. 外部JSONを使う場合、`context.md` にはローダーの公開コマンド、取得手順、停止条件を必ず書き、詳細なフェーズ順やチャンク選択は原則として `context_loader.py` に持たせる。
11. 外部JSONの個別コンテキストは各800文字以内にする。
12. 外部JSONの個別コンテキスト文字数とローダー実出力文字数は、設計・編集のたびにPythonで確認する。
13. `code interpreter` に渡す `code` 文字列の冒頭には、何のために何を実行するかが自然に分かる一文コメントを必ず入れる。
14. 外部JSONローダーの出力には、現在位置、フェーズ、NEXT/DONE状態、次回用ACKを必ず含める。
15. 外部JSONローダーを続けて呼ぶcodeコメントには、直前の`NEXT`値などを含めた短い進捗文を書く。
16. 外部JSONコンテキストはターン冒頭で一括読み込みせず、各作業フェーズの直前に必要分だけ読む。
17. 各作業フェーズでは、そのフェーズの必要コンテキストをDONEまで読み切ってから作業へ進む。
18. 後続フェーズへ移る前には、現在フェーズの作業を終えてから `phase-done <ACK>` などで後続フェーズ用の最初のコンテキストだけを読み込む。
19. `code interpreter` で使う `.py` および関連ファイルは `/mnt/data` 直下に置く。
20. SKILL フォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。
21. 各 SKILL フォルダ直下には `resolve_uploads.py` を必ずコピー配置する。
22. SKILL.md には「チャット冒頭で `resolve_uploads.py` を code interpreter で実行する」指示を必ず記載する。
23. 外部JSONローダーは状態機械型にし、`init <route>`、`advance <ACK>`、`phase-done <ACK>`、`repeat`、`status`、`validate` のような少数の公開コマンドに絞る。
24. `read <phase> <number>`、`get <chunk_id>`、フェーズ名直接指定など、AIが番号を回して一括取得しやすいAPIは作らない。互換用に残す場合も通常利用では拒否する。
25. 同じターン内でcode interpreterを複数回呼び、1チャンクずつ読むのは許可する。1つのcode interpreterコード本文内で、ループや複数subprocessなどによりローダーを2回以上起動することは禁止する。
26. ACKはstateファイルへ平文保存せず、ハッシュなど照合用の形で保存する。`status` ではACKを再表示せず、出力を見失った場合だけ `repeat` で新しいACKを再発行する。
27. 重要な生成・変換スクリプトには、必要フェーズがDONEであることを確認する任意ゲート（例: `--require-context-done`）を用意し、SKILLの本番手順ではそれを使わせる。
