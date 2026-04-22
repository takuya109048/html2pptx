# CLAUDE.md

このファイルはClaude Codeがこのプロジェクトで作業する際のガイダンスを定義します。
プロジェクトルートに配置し、Claude Codeが自動的に読み込みます。

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

カスタムGPTsのcode interpreter環境では、ユーザーがアップロードしたファイルは
**`assistant-{ユニークID}-{元のファイル名}`** という形式に自動リネームされる。
ユニークIDは実行時まで不明なため、パスをハードコードできない。

以下のパターンでファイルを動的に検索する:

```python
import glob
from pathlib import Path

def find_file(filename: str) -> Path:
    """アップロードファイルをプレフィックス付き名前で検索して返す。"""
    # プレフィックスなしでそのまま存在する場合（/mnt/data 生成ファイル等）
    exact = Path(f"/mnt/data/{filename}")
    if exact.exists():
        return exact
    # assistant-{id}- プレフィックス付きを検索
    matches = glob.glob(f"/mnt/data/assistant-*-{filename}")
    if matches:
        return Path(matches[0])
    raise FileNotFoundError(f"{filename} が /mnt/data に見つかりません")
```

* この `find_file()` ヘルパーをスクリプト冒頭に定義し、アップロードファイルへのアクセスはすべてこれ経由にする。
* `/mnt/data` 内で生成したファイル（スクリプトが書き出したもの）はプレフィックスが付かないため、`exact` チェックを先に行う。

#### プレフィックス対応に必要な2つの対処

**スクリプト内部のファイル参照だけを対応しても不十分。** スクリプト自体（`.py` ファイル）も `assistant-{id}-` プレフィックスが付いており、`python <script>` の実行パスにもプレフィックスを使う必要がある。以下の2点がセットで必要になる。

**① スクリプト実行パス: globで検索してから実行する**

```python
import glob, subprocess

# md_to_json.py を呼ぶ側（SKILL.md / code interpreter）
matches = glob.glob("/mnt/data/assistant-*-md_to_json.py")
script = matches[0] if matches else "/mnt/data/md_to_json.py"
subprocess.run(["python", script, "deck.md", "--assets-dir", "/mnt/data"], check=True)
```

スクリプトAがスクリプトBをサブプロセス呼び出しする場合も同様に `_find_prefixed()` でBのパスを取得してから実行する（`python /mnt/data/to_pptx.py` ではなく `python /mnt/data/assistant-{id}-to_pptx.py` のように）。

**② スクリプト内部のファイル参照: `_find_file()` / `_find_prefixed()` を使う**

スクリプトが実行されると、`HERE = os.path.dirname(__file__)` は `/mnt/data` に解決される（プレフィックスはディレクトリではなくファイル名に付いているため）。しかし `os.path.join(HERE, "templates.json")` = `/mnt/data/templates.json` は存在しない（`assistant-{id}-templates.json` のみ）。そのため、スクリプト内のすべてのファイル参照にもプレフィックス対応ヘルパーを使う。

`os.path` ベース（既存コードが `os.path` を使う場合）:

```python
def _find_file(base_dir: str, filename: str) -> str:
    exact = os.path.join(base_dir, filename)
    if os.path.exists(exact):
        return exact
    import glob as _glob
    matches = _glob.glob(os.path.join(base_dir, f"assistant-*-{filename}"))
    return matches[0] if matches else exact
```

`pathlib` ベース（`Path` を使う場合）:

```python
def _find_prefixed(directory: Path, filename: str) -> Path:
    exact = directory / filename
    if exact.exists():
        return exact
    matches = list(directory.glob(f"assistant-*-{filename}"))
    return matches[0] if matches else exact
```

* `exact` が存在する場合を先にチェックすることで、ローカル環境（プレフィックスなし）でも動作する。
* モジュールロード時に読み込むファイル（例: `templates.json`）も必ず `_find_file()` 経由にする。

#### ダウンロードリンクの貼り方

カスタムGPTs（code interpreter）でユーザーにファイルをダウンロードさせるには、以下のコードを code interpreter で実行する。

```python
print(f"- [Download {filename}](sandbox:/mnt/data/{filename})")
```

* `filename` にはファイル名（例: `deck_20260422.pptx`）を入れる。
* 複数ファイルをまとめて提示する場合はループで出力する:

```python
for filename in ["deck_20260422.md", "deck_20260422.json", "deck_20260422.pptx"]:
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
  example.md
  script.py
  ...
```

* `skill-name/refs/` や `skill-name/docs/` のような下位ディレクトリは作成しない。

### 文字数の計測方法

**文字数チェックには必ず `count_chars.py` を使う。**  
`wc -c` はバイト数を返すため日本語文字を正確にカウントできない。

```bash
python count_chars.py .claude/skills/<skill-name>/SKILL.md
python count_chars.py .claude/skills/<skill-name>/SKILL.md .claude/skills/<skill-name>/context.md
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
9. `code interpreter` で使う `.py` および関連ファイルは `/mnt/data` 直下に置く。
10. SKILL フォルダ配下ではサブディレクトリを作らず、すべて直下配置にする。