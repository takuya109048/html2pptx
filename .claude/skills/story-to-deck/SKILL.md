---
name: story-to-deck
description: 原文ソース（テキスト/URL/ファイル）をGLOBIS手法で分析し、プレゼンテーションストーリーを設計した上でスライドデッキMDを生成するスキル。nanobanana2による画像生成プロンプトの付与にも対応する。
---

# Story-to-Deck: 原文からスライドデッキ生成スキル

原文テキストを受け取り、プレゼンテーション用のストーリーに変換し、テンプレートを選択して `deck_YYYYMMDD.md` を生成するスキル。

---

## トリガー条件

- 「原文/ソースからスライドを作って」と依頼されたとき
- URLやファイルを渡して「デッキにして」「プレゼン資料にして」と依頼されたとき
- 既存の `source-to-deck` より高度なストーリー設計を求められたとき

---

## 全体ワークフロー

```
Step 0: ソーステキスト受け取り
         └ テキスト直接入力 / URL → WebFetch / ファイルパス → Read
         ↓
Step 1: nanobanana2使用確認 [必須：解析前に実施]
         └ → NANOBANANA_RULES.md 参照
         ↓
Step 2: ストーリー分析
         └ → STORY_ANALYSIS.md 参照
         └ フレームワーク選択 → 骨子設計 → スライド構成案 → ユーザー確認
         ↓
Step 3: テンプレート割り当て
         └ → TEMPLATE_WORKFLOW.md 参照
         └ 各スライドに決定木を適用 → nanobanana2置換処理
         ↓
Step 4: MDコンテンツ生成
         └ → MD_SYNTAX_REF.md 参照（記法）
         └ → NANOBANANA_RULES.md 参照（プロンプト付与）
         ↓
Step 5: MDファイル保存
         └ ファイル名: deck_YYYYMMDD.md（例: deck_20260420.md）
         ↓
Step 6: setup_deck.py をプロジェクトルートに生成 → AI が順に実行
         └ SKILL.md に埋め込まれたコードをそのままプロジェクトルートに Write
         └ python setup_deck.py を実行（/mnt/data へファイルをコピー）
         └ python /mnt/data/md_to_json.py deck_YYYYMMDD.md --assets-dir /mnt/data を実行
```

---

## Step 0: ソーステキスト受け取り

ユーザーがソースをまだ提示していない場合、以下のいずれかを確認する:

1. **テキスト直接貼り付け**: チャットに貼り付けてもらう
2. **URL指定**: URLを教えてもらい `WebFetch` で取得する
3. **ファイルパス指定**: ファイルパスを教えてもらい `Read` で読み込む

ソースを受け取ったら、以下を確認・推定する（未指定なら推定値を伝えて進める）:
- 発表時間・スライド枚数の目安
- 発表者名・発表日（coverスライド用）
- 対象オーディエンス

---

## Step 1: nanobanana2使用確認

**解析を始める前に必ず** ユーザーに確認する:

> 「nanobanana2による生成画像の挿入プランにしますか？  
> （YesにするとPlainスライドに画像プレースホルダーとプロンプトが追加されます）」

- **Yes** → `NANOBANANA_RULES.md` のルールに従い、Step 3・Step 4で画像置換とプロンプト生成を実施する
- **No** → plain_1col / plain_2col をそのまま使用する

---

## Step 2: ストーリー分析

`STORY_ANALYSIS.md` の手順に従い:

1. プレゼンテーション文脈を把握する
2. 目的に合ったフレームワークを選択する（SDS/PREP/DESC/序論→本論→結論/AIDMA）
3. メインメッセージを1文で定義し、骨子を設計する
4. スライド構成案（各スライドのタイトル・レイアウト候補）を箇条書きで提示する
5. **ユーザーに骨子を確認してもらう** → 承認後にStep 3へ

---

## Step 3: テンプレート割り当て

`TEMPLATE_WORKFLOW.md` の決定木を各スライドに適用する。

- 強引な当てはめは行わない
- どの特殊テンプレートにも該当しない場合は `plain_1col` または `plain_2col` を選択
- nanobanana2 Yes の場合は `TEMPLATE_WORKFLOW.md` の置換ルールを適用する

---

## Step 4: MDコンテンツ生成

`MD_SYNTAX_REF.md` の記法に従い各スライドのMarkdownを生成する。

- nanobanana2 Yes の場合: `NANOBANANA_RULES.md` に従い `image_label_1` と `note` にプロンプトを追記する

---

## Step 5 & 6: 出力

### Step 5: MDファイル保存

生成したMDを `deck_YYYYMMDD.md` としてプロジェクトルートに保存する。

### Step 6: setup_deck.py を生成 → AI が順に実行

**① Write ツールでプロジェクトルートに `setup_deck.py` を作成する。**  
ファイルがすでに存在する場合も上書きして最新の状態にする。

```python
"""story-to-deck の実行ファイル群を /mnt/data にコピーするセットアップスクリプト。
Colab / Jupyter 等の環境で初回セットアップ時に一度実行する。
"""

import shutil
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent / ".claude" / "skills" / "story-to-deck"
DEST_DIR = Path("/mnt/data")

FILES = [
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
    print(f'  python "{dest}/md_to_json.py" deck_YYYYMMDD.md --assets-dir "{dest}"')


if __name__ == "__main__":
    main()
```

**② `setup_deck.py` を実行する（/mnt/data へのコピー）。**

```
python setup_deck.py
```

エラーが出た場合はメッセージを確認してユーザーに報告する。  
`/mnt/data` が存在しない環境（ローカルWindowsなど）では失敗する場合があるが、その旨をユーザーに伝えれば良い。

**③ JSON 変換 → PPTX 生成を実行する。**

`setup_deck.py` の出力に表示される「PPTX生成コマンド」をそのまま実行する。  
Windowsでは `C:\mnt\data\md_to_json.py`、Colab/Linux では `/mnt/data/md_to_json.py` のように環境によってパスが異なるため、ハードコードせず `setup_deck.py` の出力を参照すること。

```
python "<DEST_DIR>/md_to_json.py" deck_YYYYMMDD.md --assets-dir "<DEST_DIR>"
```

生成された `.pptx` のパスを最後にユーザーへ伝える。

`md_to_json.py`・`to_pptx.py`・`templates.json`・`design.json`・`logo.png`・`background.png`・`template_engine_area.html` はすべてこの `SKILL.md` と同じフォルダに置かれている。`--assets-dir /mnt/data` を指定することでこれらすべてが `/mnt/data` から参照される。
