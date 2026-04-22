# context.md — deck-from-source 詳細ルール集

---

## STORY_ANALYSIS — GLOBISストーリー分析手法

### Step 2-1: プレゼンテーション文脈の把握

| 項目 | 確認内容 |
|------|---------|
| 発表目的 | 情報共有 / 説得・提案 / 依頼 / 報告 |
| 対象オーディエンス | 社内（上司/同僚） / 顧客 / 経営層 / 一般 |
| 発表時間 | 5分 / 10分 / 15〜20分 / 30分以上 |

**発表時間→スライド枚数の目安（cover含む）:**

| 発表時間 | 推奨枚数 |
|---------|---------|
| 5分 | 5〜7枚 |
| 10分 | 8〜12枚 |
| 15〜20分 | 12〜18枚 |
| 30分以上 | 18〜25枚 |

### Step 2-2: フレームワーク選択

| 目的 | フレームワーク | 構造 | 適したシーン |
|------|--------------|------|------------|
| 要点を端的に伝える | **SDS法** | Summary → Details → Summary | 短いスピーチ、忙しい上司への報告 |
| 説得・提案 | **PREP法** | Point → Reason → Example → Point | 提案書、説得場面 |
| 依頼・言いにくい内容 | **DESC法** | Describe → Express → Suggest → Choose | 依頼、交渉 |
| 汎用・長尺プレゼン | **序論→本論→結論** | 導入 → 主張+根拠 → まとめ | 一般的なビジネスプレゼン |
| 営業プレゼン | **AIDMA応用** | Attention → Interest → Desire → Memory → Action | 顧客向け提案 |

### Step 2-3: ストーリー骨子設計

**1. メインメッセージの定義**
ソース全体を通じて「聴衆に最も伝えたい1文」を定義する。

**2. フレームワークに沿ったセクション分割**

PREP法の例:
- Point（結論）: AIで開発生産性50%向上
- Reason（理由）: コード生成・レビュー・テストの自動化
- Example（具体例）: 導入事例・数値データ
- Point（結論の再述）: 早期導入が競争優位につながる

**3. 各セクションの内容抽出**

ソースから以下を抽出・整理する:
- 主張・メッセージ（スライドタイトルになる）
- 根拠・理由（本文箇条書きになる）
- データ・事例（tableやカードの内容になる）
- プロセス・手順（flowステップになる）
- 並列要素（3カード系になる）
- 結論・まとめ（conclusionになる）

**4. スライド構成案の提示**

以下の形式でユーザーに提示する:
```
1. [表紙] デッキタイトル
2. [plain_1col or flow] 背景・現状
3. [list_3card or diffuse_3card] 主要ポイント
4. [table or flow_3step] 詳細・根拠
...
N. [plain_1col or converge_3card] まとめ・結論
```

**5. ユーザー確認**
構成案を提示し、「この骨子で進めてよいですか？修正点があればお知らせください」と確認してから次のステップへ進む。

---

## TEMPLATE_WORKFLOW — テンプレート選択決定木

各スライドに以下の決定木を**上から順番に**適用する。最初に一致した条件でテンプレートを決定し、それ以降のルールは確認しない。どれにも当てはまらない場合のみ `plain_1col` / `plain_2col` を使う。**強引な当てはめは行わない。**

```
1. タイトル/表紙スライドか？
   → cover

2. 時系列・フェーズ変遷など「流れ」があり3段階か？
   → flow_3step

3. 時系列・フェーズ変遷など「流れ」があり4段階か？
   → flow_4step

4. 並列する3つの要素・特徴・メリット・施策がフラットに並ぶか？
   → list_3card

5. 1つの共通テーマ・課題から3つのアプローチ・方向性に展開するか？
   → diffuse_3card

6. 3つの根拠・証拠・理由が1つの結論に収束するか？
   → converge_3card

7. 背景・文脈の説明＋3つのポイントという構成か？
   → bg_3card

8. 表形式のデータがあり、かつ1つの重要な結論・示唆があるか？
   → table_conclusion

9. 表形式のデータのみで結論は別スライドか？
   → table

10. 2つのものを3つの観点で対比・比較するか？
    → compare_2col_3row

11. マトリックス形式のデータか？
    - 3×3グリッドで縦方向にフロー → flow_matrix_3x3
    - 3×3グリッドで横方向にフロー → h_flow_matrix_3x3
    - 3×2グリッドで横方向にフロー → h_flow_matrix_3x2
    - 4×2グリッドで横方向にフロー → h_flow_matrix_4x2
    - 単純な3×3表 → matrix_3x3

12. 2つの対立・比較・対照する概念を並べて説明するか？
    → plain_2col

13. それ以外（単一コンセプトの説明・段落テキスト）
    → plain_1col
```

### nanobanana2使用時の置換ルール

Step 1でnanobanana2使用が確認された場合、手順12・13で `plain_1col` / `plain_2col` に決定したスライドを以下の基準で置換する。

| 元テンプレ | コンテンツ特性 | 置換先 | 画像比率 |
|-----------|------------|--------|---------|
| `plain_1col` | テキスト量が少ない + 広い概念図・インフォグラフィックが合う | `plain_image_row` | 16:5（横長ワイド） |
| `plain_1col` | テキスト量が中程度 + 正方形〜縦長のイラストが合う | `plain_image_col` | 6:5（ほぼ正方形） |
| `plain_2col` | 片方のカラムを図解に置き換えた方が伝わりやすい | `plain_image_col` | 6:5（ほぼ正方形） |

**置換しない条件（そのまま維持する）:**
- テキスト量が多く、画像を置くスペースが確保できない
- 図解が不自然・コンテンツに合わない

### テンプレート早見表

| テンプレート | 用途 | 主要セクションタグ |
|-------------|------|----------------|
| `cover` | 表紙 | （なし） |
| `plain_1col` | 単一コンセプト説明 | `card-a` |
| `plain_2col` | 2つの概念を並べる | `card-a`, `card-b` |
| `list_3card` | 並列3要素 | `card-a`, `card-b`, `card-c` |
| `flow_3step` | 3ステップフロー | `step-a`, `step-b`, `step-c` |
| `flow_4step` | 4ステップフロー | `step-a`, `step-b`, `step-c`, `step-d` |
| `diffuse_3card` | 1→3展開 | `section`, `card-a`, `card-b`, `card-c` |
| `converge_3card` | 3→1収束 | `card-a`, `card-b`, `card-c`, `conclusion` |
| `bg_3card` | 背景+3ポイント | `section`, `card-a`, `card-b`, `card-c` |
| `table` | データ表 | `table` |
| `table_conclusion` | データ表+結論 | `table`, `conclusion` |
| `compare_2col_3row` | 2×3対比 | `matrix`（2列×3行） |
| `matrix_3x3` | 3×3マトリックス | `matrix` |
| `flow_matrix_3x3` | 縦フロー3×3 | `flow_matrix` |
| `h_flow_matrix_3x2` | 横フロー3×2 | `h_flow_matrix` |
| `h_flow_matrix_3x3` | 横フロー3×3 | `h_flow_matrix` |
| `h_flow_matrix_4x2` | 横フロー4×2 | `h_flow_matrix` |
| `plain_image_row` | テキスト+横長画像 | `card-a` + `image_label_1` |
| `plain_image_col` | テキスト+縦目画像 | `card-a` + `image_label_1` |

---

## MD_SYNTAX — MD記法リファレンス

### 基本構造

```markdown
# スライドタイトル
## サブタイトル（メッセージ）

| key | value |
|-----|-------|
| layout | <レイアウト名> |
| note | 発表者ノート |

\```card-a
### カード見出し
- 箇条書き1
- **強調テキスト**
\```

---
```

- スライドは `---` で区切る
- `# タイトル` は必須（`## メッセージ` はオプション）
- フロントマターはMarkdownテーブル形式
- **⚠️ 重要:** card-a等のコンテンツブロック内に `---` を書いてはいけない。パーサーがスライド区切りとして解釈し、直後のスライドが layout を失う。区切り線が必要な場合は空行または `####` 見出しで代替する

### レイアウト別タグ早見表

| レイアウト | 使用するタグ |
|-----------|-----------|
| `cover` | タグなし（`# タイトル` + フロントマターのみ） |
| `plain_1col` | ` ```card-a ` |
| `plain_2col` | ` ```card-a `, ` ```card-b ` |
| `list_3card` | ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `flow_3step` | ` ```step-a `, ` ```step-b `, ` ```step-c ` |
| `flow_4step` | ` ```step-a `, ` ```step-b `, ` ```step-c `, ` ```step-d ` |
| `diffuse_3card` | ` ```section `, ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `converge_3card` | ` ```card-a `, ` ```card-b `, ` ```card-c `, ` ```conclusion ` |
| `bg_3card` | ` ```section `, ` ```card-a `, ` ```card-b `, ` ```card-c ` |
| `table` | ` ```table ` (Markdownテーブル必須) |
| `table_conclusion` | ` ```table `, ` ```conclusion ` |
| `plain_image_row` | ` ```card-a ` + `image_label_1` メタデータ |
| `plain_image_col` | ` ```card-a ` + `image_label_1` メタデータ |

### フロントマターキー一覧

| キー | 必須 | 説明 |
|-----|------|------|
| `layout` | 必須 | テンプレート名 |
| `note` | 任意 | 発表者ノート（PPTX発表者ビューに表示） |
| `image_label_1` | 画像スライド | 画像プレースホルダーのラベル/nanobanana2プロンプト |
| `affiliation` | coverのみ | 組織・所属名 |
| `presenter` | coverのみ | 発表者名 |
| `date` | coverのみ | 発表日（YYYY-MM-DD） |

### インライン書式

| 記法 | 用途 |
|-----|------|
| `**テキスト**` | 太字・強調キーワード |
| `*テキスト*` | 斜体・補足・定義 |
| `` `テキスト` `` | 固有名詞・コード・コマンド名 |
| `~~テキスト~~` | 打ち消し・旧情報 |

### coverスライドのテンプレート

```markdown
# デッキタイトル

| key | value |
|-----|-------|
| layout | cover |
| affiliation | 組織名 |
| presenter | 発表者名 |
| date | YYYY-MM-DD |
| note | 発表の背景・目的を1〜2文で。 |

---
```

### tableスライドのテンプレート

```markdown
# テーブルタイトル
## サブメッセージ

| key | value |
|-----|-------|
| layout | table |
| note | 表の読み方・注目ポイント。 |

\```table
| 列1 | 列2 | 列3 |
| --- | --- | --- |
| データ | データ | データ |
\```

---
```

---

## NANOBANANA_RULES — nanobanana2プロンプト生成ルール

### ルールA: image_label への画像プロンプト

**対象テンプレート:** `plain_image_row`, `plain_image_col`
**書き込み先:** フロントマターテーブルの `image_label_1` フィールド

**image_row（16:5 横長ワイド）のプロンプト形式:**
```
[スライドテーマ]の概念を示す横長インフォグラフィック。フラットデザイン、ミニマル、ビジネス向け、白背景。16:5の横長比率で[要素1]・[要素2]・[要素3]を視覚的に図解する。文字なし。
```

**image_col（6:5 ほぼ正方形）のプロンプト形式:**
```
[スライドテーマ]を表すシンプルなイラスト。フラットデザイン、ミニマルアイコン風、ビジネス向け、白背景。6:5の比率で[具体的な概念]を1枚のビジュアルで表現する。文字なし。
```

### ルールB: note へのアイコン一括生成プロンプト

**対象テンプレート:** `list_3card`, `flow_3step`, `flow_4step`, `diffuse_3card`, `converge_3card`, `bg_3card`
**書き込み先:** `note` フィールドの末尾に追記

```
[nanobanana2 icon prompt]
[N]つのフラットアイコンを横一列に並べた1枚の画像を生成する。
左から順に:
  アイコン1: [カードAのテーマを表す概念・シンボル]
  アイコン2: [カードBのテーマを表す概念・シンボル]
  アイコン3: [カードCのテーマを表す概念・シンボル]
各アイコンは正方形の枠内に収まるシンプルなフラットデザイン。白背景、色統一、ミニマルスタイル、文字なし。
※生成後に水平[N]等分にトリミングして各カード/ステップのアイコンとして使用。
```

| テンプレート | アイコン数 |
|------------|----------|
| `list_3card`, `flow_3step`, `diffuse_3card`, `converge_3card`, `bg_3card` | 3 |
| `flow_4step` | 4 |

### プロンプト品質ガイドライン

1. **具体性**: 「ビジネス」ではなく「会議室でのプレゼン」など具体的なシンボル・シーンを指定
2. **スタイル統一**: 全スライドで「フラットデザイン、白背景、ミニマル」を一貫させる
3. **アスペクト比の明示**: image_rowは「16:5の横長比率」、image_colは「6:5の比率」を必ず明記
4. **テキスト不要**: 画像内にテキスト・文字を含めないよう「文字なし」を追記する

---

## SETUP_SCRIPT — setup_deck.pyコード

Step 6①でプロジェクトルートに以下のコードを `setup_deck.py` として Write する（既存ファイルがあっても上書き）。

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

**実行後の注意:**
- `/mnt/data` が存在しない環境（ローカルWindowsなど）では失敗する場合があるが、その旨をユーザーに伝えればよい
- Step 6③では、`setup_deck.py` の出力に表示される「PPTX生成コマンド」をそのまま実行すること（パスをハードコードしない）
- Windowsでは `pathlib.Path("/mnt/data").resolve()` は `C:\mnt\data` になるため、出力されたパスを使えば環境差異を吸収できる
- スクリプトファイル群（`md_to_json.py`, `to_pptx.py`, `templates.json`, `design.json`, `logo.png`, `background.png`, `template_engine_area.html`）はすべて `.claude/skills/story-to-deck/` に置かれている
