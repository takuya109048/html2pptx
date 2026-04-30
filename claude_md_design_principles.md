# CLAUDE.md設計の実務原則
## AIの行動を安定させるルールブックとして育てる
| key | value |
|-----|-------|
| layout | cover |
| affiliation | Codex Working Deck |
| presenter | Takuya |
| date | 2026-05-01 |
| note | 本資料は、CLAUDE.mdを単なる設定ファイルではなく、AIの振る舞いをプロジェクト基準へそろえるための設計文書として捉え直すものである。Auto memoryとの違い、書くべき内容、章立て、運用改善までを一連の実務として整理する。 |

---

# 目次
## 設計論点を章ごとにたどる
| key | value |
|-----|-------|
| layout | plain_2col |
| note | まず全体像を確認する。CLAUDE.mdは、何を書くかだけでなく、何を書かないかによって効き方が変わる。ここでは正体と役割分担から入り、設計密度、章立て、スコープ分離、用途別テンプレート、最後に継続運用へ進む構成である。各章は独立した知識ではなく、AIに与える文脈をどう整えるかという一つの判断へつながっている。 |
```card-a
### 基本理解
- CLAUDE.mdはAIの行動基準を固定する
- MEMORY.mdとは役割と責任が異なる
- 書く量よりも、守らせる粒度が成果を左右する

### 実装設計
- CLAUDE.mdは毎回読み込まれる行動基準である
- MEMORY.mdには弱い好みと学習結果を逃がす
- 良いルールは短く、具体的で、実行できる
```
```card-b
### overflow
- 7章立てでAIに必要な地図を渡す
- rulesで文脈を局所化し、認知負荷を下げる
- 用途別テンプレートは現場制約から作る
- CLAUDE.mdは繰り返しの注意から育てる
- 3レイヤー構造で個人と案件のルールを分ける
```

---

# CLAUDE.mdは毎回読み込まれる行動基準である
## 単発のお願いではなく、プロジェクトの標準動作を定義する
| key | value |
|-----|-------|
| layout | bg_3card |
| note | まず押さえるべき前提は、CLAUDE.mdが単なるメモではなく、セッション開始時にAIへ渡される行動基準である点である。毎回同じ説明を繰り返さずに済むだけでなく、プロジェクト固有の前提、禁止事項、作業手順を安定して反映できる。だからこそ、会話でその場限りに依頼すべき内容と、常に守らせる内容を分ける必要がある。\n\n---\n\n[nanobanana2 icon prompt]\nCreate a 3:1 horizontal icon strip with three equal square icons, white background, minimal flat business style, very small outer margins, no top or bottom whitespace. Left icon: a document labeled CLAUDE.md with a small lock symbol. Center icon: a session start screen receiving rules. Right icon: a checklist aligning AI behavior to a project baseline. Keep the three icons same size, same color palette, centered in equal regions, easy to crop horizontally. Avoid vertical presentation-card composition. |
```section
### ルールブックとして扱う理由
CLAUDE.mdは、AIが作業を始めるたびに参照する「常設の前提」である。プロジェクトの安全策、判断基準、実行手順をここへ集約すると、会話ごとの揺れを抑えられる。
```
```card-a
### 反復説明を減らす
毎回伝える注意点を文書化し、開始時から同じ基準で作業させる。
- 禁止操作や必須コマンドを先に渡す
- 口頭の補足をルールへ昇格させる
```
```card-b
### 基準へ適合させる
AIの提案を一般論ではなく、プロジェクト固有の前提へ寄せる。
- 技術スタックと設計方針を固定する
- 迷いやすい判断を事前に狭める
```
```card-c
### 書きすぎを避ける
常に守るべき内容だけを残し、単発の依頼は会話へ逃がす。
- 一時的な指示を混ぜない
- 古い前提は定期的に削る
```

---

# MEMORY.mdには弱い好みと学習結果を逃がす
## 強制ルールと学習メモを混同しない
| key | value |
|-----|-------|
| layout | compare_2col_3row |
| note | ここで混同しやすいのは、CLAUDE.mdもMEMORY.mdもコンテキストであるため、同じ置き場に見えてしまう点である。しかし、CLAUDE.mdはユーザーが明示的に定義する強制指示であり、MEMORY.mdはAIが作業を通じて学んだ傾向を残す場所である。設計上は、必ず守る約束をCLAUDE.mdへ、よくある好みや最近の対処法をMEMORY.mdへ逃がすと、ノイズを増やさずに文脈を保てる。 |
```compare
| 観点 | CLAUDE.md | MEMORY.md / Auto memory |
| --- | --- | --- |
| 作成者 | ユーザーが明示的に書く。責任あるルールとしてレビューしやすい | AIが作業から自動的に学ぶ。好みや傾向の蓄積に向く |
| 内容 | コーディング規約、禁止事項、ビルド手順、設計方針など普遍的な前提 | 変数名の癖、最近のエラー対処、いつもの寄せ方など弱い記憶 |
| 使い分け | 守らないと品質や安全性に影響するものを置く | 守るよりも参考にする程度の情報を置く |
```

---

# 良いルールは短く、具体的で、実行できる
## 抽象的な期待を、AIが迷わない行動へ変換する
| key | value |
|-----|-------|
| layout | list_3card |
| note | 長さと粒度の話は、単に読みやすさの問題ではない。AIにとって、長すぎるルールは重要度の差が見えにくく、抽象的なルールは行動に変換しにくい。良いCLAUDE.mdでは、1ルールを1文に近づけ、宣言調で書き、実行できるコマンドや判断として表現する。これにより、AIは意図を推測するのではなく、次に取る行動として処理できる。\n\n---\n\n[nanobanana2 icon prompt]\nCreate a 3:1 horizontal icon strip with three equal square icons, white background, minimal flat business style, tiny outer margins, no top or bottom whitespace. Left icon: a short rule sentence on a document. Center icon: a decisive stamp saying DO as a tiny Japanese tag 「実行」. Right icon: a terminal command checklist with a green check. Same icon size, same palette, centered in three equal crop regions. Avoid vertical presentation-card composition. |
```card-a
### 1ルール1文
短く切ることで、AIがどの条件を守るべきか判断しやすくなる。
- 長い背景説明は別文書へ分離する
- 例外条件は必要な場合だけ添える
- 同じ文に複数の禁止を詰め込まない
```
```card-b
### 宣言調で書く
お願いではなく、プロジェクトの決まりとして断定する。
- 「してください」より「する」を使う
- 作業者の裁量ではなく標準動作にする
- 曖昧な努力目標を避ける
```
```card-c
### 実行可能にする
抽象語を、実際に走らせるコマンドや確認観点へ落とす。
- 変更後はテストを実行する
- 失敗したテストを修正する
- 危険操作にはdry-runを用意する
```

---

# 7章立てでAIに必要な地図を渡す
## 目的、技術、構造、手順、落とし穴を一枚の設計図にする
| key | value |
|-----|-------|
| layout | table_conclusion |
| note | この表は章立ての羅列ではなく、AIが作業前に何を知らないと危ないかを整理した地図である。プロジェクト概要は目的を伝え、技術スタックは選択肢を狭め、ディレクトリ構成は探索の起点を与える。さらにコマンド、規約、ワークフロー、落とし穴まで書くことで、AIの提案と実行が現場の制約から外れにくくなる。 |
```table
| 章 | 書く内容 | AIへの効き方 |
| --- | --- | --- |
| プロジェクト概要 | 目的、想定ユーザー、重要ユースケース | 何を優先すべきか判断できる |
| 技術スタックと禁止事項 | 言語、フレームワーク、禁止ライブラリ | 勝手な選択肢を減らせる |
| ディレクトリ構成 | 主要フォルダと責務 | 探す場所と変更範囲を誤りにくい |
| コマンド集 | dev、test、typecheck、lint | 計画と検証にそのまま組み込める |
| 作業ルール | 調査、計画、検証、報告の順序 | 期待する進め方を固定できる |
```
```conclusion
CLAUDE.mdは、読むだけの文書ではなく、AIが作業空間を理解するための最短地図である。
```

---

# rulesで文脈を局所化し、認知負荷を下げる
## 全体ルールと領域別ルールを分けて適用する
| key | value |
|-----|-------|
| layout | flow_3step |
| note | 大規模なリポジトリでは、すべてのルールを1つのCLAUDE.mdへ詰めるほど、関係のない指示も毎回読み込まれる。実際に進める時は、ルートの共通ルールを薄く保ち、frontendやinfraのような領域別ルールを分けるのが有効である。AIは今触っている場所に近いルールを優先でき、設計判断や禁止事項の取り違えが起きにくくなる。\n\n---\n\n[nanobanana2 icon prompt]\nCreate a 3:1 horizontal icon strip with three equal square icons, white background, minimal flat repository style, tiny outer margins, no top or bottom whitespace. Left icon: a root folder with CLAUDE.md. Center icon: nested folders labeled frontend and infra with small rule sheets. Right icon: a focused spotlight on the active folder rules. Same size, same palette, centered in equal crop regions. Avoid vertical presentation-card composition. |
```step-a
### 共通ルールを置く
ルートCLAUDE.mdには、全体で常に守る安全策と基本方針を残す。
```
```step-b
### 領域別に分ける
frontend、infra、dataなど、判断基準が異なる場所へ専用ルールを置く。
```
```step-c
### 関係する文脈だけ読む
今の変更対象に近いルールを優先し、無関係な制約で判断を濁らせない。
```

---

# 用途別テンプレートは現場制約から作る
## Web、データ、自動化では、AIに渡す前提が変わる
| key | value |
|-----|-------|
| layout | bg_3card |
| note | CLAUDE.mdのテンプレートは、どの現場にも同じ形で当てるものではない。WebアプリではUIライブラリやAPI配置が重要になり、データ分析では保存場所や再現性が重要になる。スクリプトや自動化では対象OS、シェル、安全策、ログの置き方が品質を左右する。用途ごとの失敗しやすい前提を先に書くほど、AIの初手が現場に合いやすくなる。\n\n---\n\n[nanobanana2 icon prompt]\nCreate a 3:1 horizontal icon strip with three equal square icons, white background, minimal flat technical style, tiny margins, no top or bottom whitespace. Left icon: a web app window with component blocks. Center icon: a data table and chart with a seed marker. Right icon: a PowerShell terminal with a safety shield. Same icon size, same colors, centered in three equal crop regions, easy horizontal crop. Avoid vertical presentation-card composition. |
```section
### 用途が変わると、書くべき制約も変わる
同じCLAUDE.mdでも、Webアプリ、データ分析、自動化ではAIが誤りやすい地点が異なる。テンプレートは章の形ではなく、現場の制約から逆算する。
```
```card-a
### Webアプリ
UIとAPIの責務を固定し、勝手な設計分岐を減らす。
- CSSフレームワークを指定する
- 状態管理の選択肢を絞る
```
```card-b
### データ分析
再現性と保存場所を明示し、結果の揺れを抑える。
- rawとprocessedを分離する
- ランダムシードを固定する
```
```card-c
### 自動化
OSとシェル、安全策を明示し、危険操作を抑止する。
- PowerShellやWSLの前提を書く
- dry-runやログ出力を標準化する
```

---

# CLAUDE.mdは繰り返しの注意から育てる
## 一度作って終わりではなく、運用で精度を上げる
| key | value |
|-----|-------|
| layout | list_3card |
| note | ここまでの話を運用に変えると、CLAUDE.mdは最初から完成させる文書ではなく、会話で繰り返された注意を吸い上げて育てる文書である。2回同じ注意をしたらルール化し、古くなった技術スタックや形骸化した制約は削る。さらに、書き換えた後は小さなタスクでAIの挙動を確認することで、ルールが本当に効いているかを検証できる。\n\n---\n\n[nanobanana2 icon prompt]\nCreate a 3:1 horizontal icon strip with three equal square icons, white background, minimal flat operations style, small outer margins, no top or bottom whitespace. Left icon: two repeated chat warnings becoming a rule document. Center icon: pruning outdated rule sheets. Right icon: a small test task with behavior check marks. Same size, same palette, centered in equal horizontal crop regions. Avoid vertical presentation-card composition. |
```card-a
### 2回言ったら昇格
同じ注意を繰り返した時点で、会話ではなくCLAUDE.mdへ移す。
- 繰り返しは設計漏れのサインである
- 注意を短い行動ルールへ変換する
- 単発の好みは昇格させない
```
```card-b
### 定期的に削る
古い前提や使われない制約を残すほど、重要ルールが埋もれる。
- 技術スタック変更後に見直す
- 形骸化した禁止事項を外す
- 長い背景説明を別文書へ逃がす
```
```card-c
### 小さく検証する
ルールを書き換えたら、期待する振る舞いが出るか軽い作業で確認する。
- テスト、lint、調査順序を見る
- 危険操作の抑止を確認する
- 効かない表現は具体化する
```

---

# 3レイヤー構造で個人と案件のルールを分ける
## グローバル、プロジェクト、ディレクトリを重ねて使う
| key | value |
|-----|-------|
| layout | plain_2col |
| note | 最後に持ち帰るべき判断は、すべてを一つのCLAUDE.mdへ集めるのではなく、ルールの射程ごとに置き場所を分けることである。個人の好みはグローバルへ、案件固有の技術や危険操作はプロジェクトへ、UIやインフラのような領域差はディレクトリ単位へ置く。こうすると、AIは常に必要な前提を受け取りつつ、不要な文脈で判断を濁らせにくくなる。 |
```card-a
### 実務での配置方針
CLAUDE.mdの設計は、ルールの内容だけでなくスコープ設計で決まる。
1. **グローバル:** 日本語回答、テスト重視、報告形式など個人の共通好みを置く。
2. **プロジェクト単位:** 技術スタック、ディレクトリ構成、危険操作の禁止を置く。
3. **ディレクトリ単位:** frontendやinfraなど、領域ごとの実装制約を置く。

この分離により、AIは「常に守ること」と「今だけ関係すること」を混同しにくくなる。
```
```card-b
### nanobananaプロンプト
    Create a 6:5 flat explanatory diagram for a Japanese business slide, white background, full-canvas composition with no letterbox and no large top or bottom whitespace. Show three stacked layers: グローバル at the top as personal preferences, プロジェクト in the middle as technical rules and safety constraints, ディレクトリ at the bottom as local frontend or infra rules. Use simple documents, folders, arrows, and small Japanese labels. Make it a coherent explanatory diagram, not separate icons.
```
