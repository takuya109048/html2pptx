# CLAUDE.md

このファイルはClaude Codeがこのプロジェクトで作業する際のガイダンスを定義します。
プロジェクトルートに配置し、Claude Codeが自動的に読み込みます。

---

## プロジェクト概要

<!-- TODO: プロジェクトの目的・概要を記載 -->
<!-- 例: このリポジトリは〇〇を目的としたPythonアプリケーションです -->

---

## 開発環境

### Pythonバージョン・パッケージ管理

<!-- TODO: 使用するツールに合わせてコメントを外す -->

```bash
# パッケージ管理 (いずれか1つを選択)
# uv sync                          # uv を使う場合（推奨）
# pip install -r requirements.txt  # pip を使う場合
# poetry install                   # Poetry を使う場合
```

- Python: `3.11+`  <!-- TODO: バージョンを確認して修正 -->
- パッケージ管理: `uv` / `pip` / `poetry`  <!-- TODO: 使用するものだけ残す -->

### よく使うコマンド

```bash
# 開発サーバー / アプリ起動
# python -m uvicorn app.main:app --reload   # FastAPI
# python manage.py runserver                # Django
# python src/main.py                        # スクリプト

# テスト
pytest                                          # 全テスト実行
pytest tests/unit/                              # ユニットテストのみ
pytest -k "test_login"                          # 特定テストのみ
pytest --cov=src --cov-report=term-missing      # カバレッジ付き

# Lint / フォーマット
ruff check .          # lint
ruff format .         # フォーマット
mypy src/             # 型チェック
```

---

## 実装ポリシー

Claude は **Read / Edit / Write / Bash ツールを直接使って**コーディング・ファイル操作を行う。

### 実装の原則

- 変更前に必ず対象ファイルを `Read` で確認する
- 変更は最小限にとどめ、指示された箇所のみ修正する
- 実行して結果を確認してからユーザーに報告する

---

## Agent Skills

### Skill: Pythonコード生成・開発支援

**トリガー**: 以下の依頼があれば必ずこのスキルの手順に従うこと。
- 新しいモジュール・クラス・関数の作成
- 既存コードのリファクタリング・最適化
- バグ修正・デバッグ支援
- テストコードの生成
- 型アノテーションの追加・修正

> **注意**: 以下はコーディング規約。実装時はこの規約に従って Claude が直接コードを書く。

---

#### Step 1: 実装前の確認

コードを書き始める前に必ず行うこと:

1. `src/` 以下に同様の処理が既にないか `grep` で調査する
2. `requirements.txt` / `pyproject.toml` で利用可能なライブラリを確認する
3. 既存コードのスタイル（型アノテーション有無、docstringスタイル等）に合わせる

---

#### Step 2: コーディング規約

**スタイル**:
- フォーマッター: `ruff format`（Black互換）
- Linter: `ruff check`
- 型チェック: `mypy`（strict推奨）
- 1行の最大文字数: 88文字

**命名規則**:
| 対象 | 規則 | 例 |
|------|------|----|
| 変数・関数 | `snake_case` | `get_user_by_id` |
| クラス | `PascalCase` | `UserRepository` |
| 定数 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| プライベート | `_` プレフィックス | `_internal_state` |
| 型エイリアス | `PascalCase` | `UserId = NewType("UserId", int)` |

**型アノテーション**:
```python
# 必ず付ける。Anyは極力使わない
def fetch_users(limit: int, offset: int = 0) -> list[User]:
    ...

# 戻り値がない場合
def send_notification(message: str) -> None:
    ...

# Optional より X | None を使う（Python 3.10+）
def find_user(user_id: int) -> User | None:
    ...
```

**docstring**: Google スタイルを使用する
```python
def calculate_discount(price: float, rate: float) -> float:
    """割引後の価格を計算する。

    Args:
        price: 元の価格（税抜）
        rate: 割引率（0.0〜1.0）

    Returns:
        割引後の価格

    Raises:
        ValueError: rate が 0〜1 の範囲外の場合
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0 and 1, got {rate}")
    return price * (1 - rate)
```

---

#### Step 3: エラーハンドリング

```python
# NG: 広すぎるexcept
try:
    result = process()
except Exception:
    pass  # サイレント失敗は厳禁

# OK: 具体的な例外を捕捉し、ログを残す
import logging
logger = logging.getLogger(__name__)

try:
    result = process()
except ValueError as e:
    logger.error("Invalid input: %s", e)
    raise
except httpx.TimeoutException:
    logger.warning("Request timed out, retrying...")
    raise RetryableError("upstream timeout") from None
```

カスタム例外はプロジェクト共通の基底クラスを継承する:
```python
# src/exceptions.py に定義
class AppError(Exception):
    """アプリケーション共通の基底例外"""

class NotFoundError(AppError):
    """リソースが見つからない場合"""

class ValidationError(AppError):
    """入力値が不正な場合"""
```

---

#### Step 4: テストコード生成

**ファイル構成**:
```
tests/
├── unit/          # 外部依存なし・高速
├── integration/   # DB・外部APIを含む
└── conftest.py    # 共通フィクスチャ
```

**テスト名**: `test_<対象>_<条件>_<期待結果>` 形式
```python
# pytest + AAA パターン
def test_calculate_discount_valid_rate_returns_discounted_price():
    # Arrange
    price = 1000.0
    rate = 0.1

    # Act
    result = calculate_discount(price, rate)

    # Assert
    assert result == 900.0


def test_calculate_discount_rate_over_1_raises_value_error():
    with pytest.raises(ValueError, match="rate must be between 0 and 1"):
        calculate_discount(1000.0, 1.5)
```

**外部依存はモックする**:
```python
from unittest.mock import AsyncMock, patch

async def test_fetch_user_not_found_raises_not_found_error():
    with patch("src.repository.UserRepository.find") as mock_find:
        mock_find.return_value = None

        with pytest.raises(NotFoundError):
            await get_user_service(user_id=999)
```

**カバレッジ目標**: 単体テスト 80% 以上（`pytest --cov` で確認）

---

#### Step 5: リファクタリング方針

1. **変更前にテストを実行**し、全パスを確認する
2. **1コミット1変更**: リファクタリングと機能追加を混在させない
3. **段階的に変更**: 一度に全部書き直さず、小さく変えてはテストする
4. 変更後は `ruff check .` と `mypy src/` を実行してエラーがないことを確認する

---

#### Step 6: デバッグ支援

バグ修正の手順:

1. エラーメッセージ・トレースバックをそのままコピーして提示する
2. 最小再現コードを特定する
3. 修正は最小限の変更にとどめる（関係ない改善は別PRで）
4. 修正後、同種のバグが他の箇所にないか確認する
5. 原因と修正内容をコミットメッセージに記載する

---

## Skills 管理

**すべての skills はプロジェクト内の `.claude/skills/` で管理する。**
グローバル（`~/.claude/skills/`）には置かない。

```
.claude/
└── skills/
    ├── slide-deck-creator/       # スライドデッキJSON生成スキル
    │   ├── SKILL.md
    │   └── references/
    ├── slide-deck-creator-workspace/  # eval ワークスペース
    ├── skill-creator/            # スキル作成・改善スキル
    ├── pptx/                     # PPTX操作スキル
    ├── pdf/                      # PDF操作スキル
    └── ...                       # その他スキル
```

新しいスキルを作成する際は `.claude/skills/<skill-name>/` に作成すること。

---

## ディレクトリ構成

```
.
├── CLAUDE.md
└── .claude/
    ├── settings.json
    └── skills/
        ├── slide-deck-creator/      # スライドデッキ生成スキル（メイン）
        │   ├── SKILL.md
        │   ├── to_pptx.py           # PPTX生成スクリプト
        │   ├── templates.json       # スライドテンプレート定義
        │   ├── design.json          # デザイントークン
        │   ├── background.png       # 表紙背景画像
        │   ├── logo.png             # ロゴ画像
        │   ├── template_engine_area.html  # プレビューエンジン
        │   ├── server.js            # プレビューサーバー
        │   ├── templates/           # HTMLテンプレート群
        │   ├── references/          # テンプレートリファレンス
        │   └── evals/               # evalデータ
        └── ...                      # その他スキル
```

---

## セキュリティ・注意事項

- **APIキー・パスワードは絶対にコードに書かない** → `.env` を使い `.gitignore` に追加する
- 外部入力は必ず `pydantic` 等でバリデーションする
- SQLクエリは必ずパラメータバインドを使う（文字列結合でのSQL組み立て禁止）
- 300行を超える実装は先に設計をユーザーと確認してから書く
- 既存の公開APIのシグネチャを変更する前にユーザーに確認する

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