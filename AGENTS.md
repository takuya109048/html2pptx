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
* `SKILL.md` には最小限の行動指針のみを書き、詳細ルール・参照情報・補足仕様は `context.md` に分離する。

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

### code interpreter の利用方針

* `file search` のほかに `code interpreter` が利用できる。
* `code interpreter` で実行可能な Python ファイルは **`/mnt/data` 直下にある `.py` ファイルのみ** とする。
* Python が利用する入力ファイルも、必ず **`/mnt/data` 直下** に置く。
* 必要なファイルは以下のいずれかの方法で用意する。
  * `/mnt/data` 直下にアップロードする
  * `/mnt/data` 直下に生成する
  * `/mnt/data` 直下にコピー配置する
* Python 実行時は、必ず `/mnt/data` 直下のファイルを利用する。

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

### SKILL 作成時の必須ルール

1. カスタムGPTsへの流用を前提にする。
2. `SKILL.md` をシステムプロンプトとして使う前提で設計する。
3. `SKILL.md` は 5000 文字以内に収める（計測は `python count_chars.py` を使う）。
4. `SKILL.md` には最小限の指示のみを書く。
5. 詳細コンテキストは `context.md` に集約する。
6. 各ターン開始時に必ず `file search` で `context.md` を再読込する。
7. `file search` では `queries` のみを使う。
8. `context.md` は1ファイルに絞り、20000文字以内にする（計測は `python count_chars.py` を使う）。
9. `context.md` は文字数削減のため、原則として `*` や `` ` `` によるマークアップを使わない。
10. `code interpreter` で使う `.py` および関連ファイルは `/mnt/data` 直下に置く。
11. SKILL フォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。
12. 各 SKILL フォルダ直下には `resolve_uploads.py` を必ずコピー配置する。
13. SKILL.md には「チャット冒頭で `resolve_uploads.py` を code interpreter で実行する」指示を必ず記載する。
