# CLAUDE.md設計の実務ガイド
## ルールブックと学習メモを分けて、AIの作業品質を安定させる
| key | value |
|-----|-------|
| layout | cover |
| affiliation | Project Guide |
| presenter | Takuya |
| date | 2026-04-30 |
| note | この資料は、CLAUDE.mdを単なるメモではなく、Claude Codeの初動を揃えるルールブックとして設計するための実務ガイドである。Auto memoryやMEMORY.mdとの役割差、適切な長さ、章立て、スコープ設計、運用改善までを一連の判断として扱う。 |

---

# 目次
## 設計判断の流れを章で束ねる
| key | value |
|-----|-------|
| layout | plain_2col |
| note | まず全体像として、CLAUDE.mdをどの粒度で設計し、どこまでを書き、何をAuto memoryへ任せるかを順に確認する。目次は単なるタイトル一覧ではなく、前提、分担、構成、運用という判断の流れを示すための地図である。左側から順番に読み進めれば、最後にTakuyaさんの環境へ落とし込む設計指針までつながる。 |
```card-a
### 背景と前提
- CLAUDE.mdは強制指示の土台である
- 記憶はルールと学習メモに分ける

### 設計の判断軸
- 長さは守れる量へ絞る
- 7章立てで探索の迷いを減らす
- rulesは場所別に読む範囲を絞る
```
```card-b
### 運用への落とし込み
- 用途別テンプレートは判断を先に固定する
- 運用ループでCLAUDE.mdを育てる
- 3レイヤーでTakuya環境に合わせる
```

---

# CLAUDE.mdは強制指示の土台である
## 毎回説明する内容を、開始時に読まれるルールへ固定する
| key | value |
|-----|-------|
| layout | bg_3card |
| note | まず押さえるべき前提は、CLAUDE.mdが単なる便利メモではなく、セッション開始時の振る舞いを揃える基準である点である。毎回の会話で同じ注意を繰り返すと、指示の漏れや解釈の揺れが起きる。そこで、常に守ってほしいルールだけをCLAUDE.mdへ置き、単発の相談や一時的な好みは会話側に残す。この分離により、AIは最初からプロジェクトの前提に沿って作業できる。\n\n---\n\n[nanobanana2 icon prompt]\n6:5 aspect ratio. Three flat minimal business icons in one horizontal row, white background, no text. Left icon: rulebook with checkmark and bookmark. Center icon: startup switch powering a workflow line. Right icon: project folder connected to a target. Unified blue and teal palette, simple geometric shapes, equal square icon areas. |
```section
CLAUDE.mdは、AIの作業開始時に読み込まれる「常設ルール」である。毎回説明する負担を減らし、プロジェクト固有の判断基準を会話の前に置く役割を持つ。
```
```card-a
### 重要ルールを厳選する
常に守るべき基準だけを残すことで、AIが迷わず優先順位を判断できる。
- 単発の作業指示は会話で扱い、恒久ルールと混ぜない
- 禁止事項や必須コマンドなど、逸脱時の影響が大きいものを優先する
```
```card-b
### 適切な密度を保つ
長すぎるルールは、重要な指示を埋もれさせる。守れる量へ絞ることが精度を上げる。
- 60から300行程度を目安に、2から6画面で把握できる状態にする
- 150から200程度のルールを上限感として、重複や抽象語を削る
```
```card-c
### スコープを分ける
プロジェクトやディレクトリの役割に応じて、読むべき前提を変える。
- 全体共通の行動規範はルートに置く
- UI、インフラ、データ処理など、局所ルールは対象範囲へ寄せる
```

---

# 記憶はルールと学習メモに分ける
## CLAUDE.mdとMEMORY.mdを混ぜると、強制力と好みが曖昧になる
| key | value |
|-----|-------|
| layout | compare_2col_3row |
| note | ここで混同しやすいのは、CLAUDE.mdもMEMORY.mdもコンテキストに見えるため、同じ置き場として扱ってしまう点である。CLAUDE.mdはユーザーが明示的に書く強制指示であり、Claudeに守らせたい規約や手順を置く。一方でMEMORY.mdやAuto memoryは、作業から学んだ傾向や好みを蓄積する場所である。強制したいことはCLAUDE.md、観察から育つ好みはMEMORY.mdという切り分けにすると、指示の重みが安定する。 |
```compare
| 観点 | CLAUDE.md | MEMORY.md / Auto memory |
|---|---|---|
| 作成者 | ユーザーが明示的に管理し、プロジェクト基準として固定する | Claudeが作業から学び、傾向や好みとして蓄積する |
| 内容 | コーディング規約、禁止事項、必須コマンド、設計方針などの強制指示 | よく使う操作、変数名の傾向、最近の落とし穴などの学習メモ |
| 判断基準 | 守らないと品質や安全性に影響する内容を置く | あると便利だが、状況により変わる弱い好みを任せる |
```

---

# 長さは守れる量へ絞る
## 量を増やすほど安心ではなく、重要ルールが埋もれる危険が増える
| key | value |
|-----|-------|
| layout | table_conclusion |
| note | この表は行数の目安そのものよりも、守れる情報量へ絞るという判断を示している。CLAUDE.mdは、書けるだけ書けばよいファイルではない。長くなるほど、AIが重要な禁止事項や実行コマンドを見失うリスクが増える。短くする時も、抽象的なスローガンだけにすると行動へ変換できない。したがって、1ルール1文、宣言調、実行可能な指示という形で、少ない文字数でも判断に使える密度を作ることが重要である。 |
```table
| 設計観点 | 推奨 | 判断の理由 |
|---|---|---|
| 全体サイズ | 60から300行程度 | 2から6画面で確認でき、重要ルールが埋もれにくい |
| ルール数 | 150から200程度を上限感にする | 多すぎると優先順位が曖昧になり、遵守精度が落ちる |
| 文の粒度 | 1ルール1文で断定する | AIが実行単位へ変換しやすく、曖昧な努力目標になりにくい |
| 指示の具体性 | コマンドや禁止操作まで書く | 「しっかり」ではなく、何を実行するかが明確になる |
```
```conclusion
CLAUDE.mdは詳しさよりも、守れる量と実行可能性で設計する。
```

---

# 7章立てで探索の迷いを減らす
## 何を作るか、どこを触るか、どう検証するかを順に置く
| key | value |
|-----|-------|
| layout | list_3card |
| note | CLAUDE.mdを作る時に困りやすいのは、何を書けばよいかではなく、どの順番で置けばAIが迷わないかである。推奨される7章立ては、プロジェクト概要から始まり、技術スタック、ディレクトリ構成、コマンド、規約、作業ルール、落とし穴へ進む。これは人間向けの説明というより、AIが作業前に確認するチェックリストである。上流の目的から下流の実行手順まで並べることで、ファイル探索や検証の無駄を減らせる。\n\n---\n\n[nanobanana2 icon prompt]\n6:5 aspect ratio. Three flat minimal business icons in one horizontal row, white background, no text. Left icon: product map with user silhouette and target. Center icon: layered architecture blocks with code brackets. Right icon: terminal window with checklist and shield. Unified navy, teal, and green palette, simple geometric shapes, equal square icon areas. |
```card-a
### 前提を置く章
プロジェクト概要は、AIが「何を作っているか」を誤解しないための入口である。
- 目的、想定ユーザー、主要ユースケースを短く置く
- セキュリティや速度など、判断を左右する非機能要件を明示する
- 提案の良し悪しを測る基準として使える内容にする
```
```card-b
### 探索を助ける章
技術スタックとディレクトリ構成は、AIが余計な候補を探さないための地図である。
- 使用フレームワークや禁止ライブラリを明確にする
- `src/app` や `src/features` など主要ディレクトリの責務を書く
- ビジネスロジックの置き場など、境界を破りやすい点を先に示す
```
```card-c
### 実行を揃える章
コマンド、規約、ワークフロー、落とし穴は、変更後の品質を安定させる。
- `pnpm test` や `pnpm lint` など、そのまま実行できる形で書く
- インデントや `any` 禁止など、人間側の品質基準を明示する
- 本番環境や個人情報など、推測で触ると危険な制約を最後に固定する
```

---

# rulesは場所別に読む範囲を絞る
## 大規模リポジトリでは、全ルールを常に読ませない
| key | value |
|-----|-------|
| layout | table_conclusion |
| note | 大きなリポジトリでは、全領域のルールを毎回同じ重さで読ませると、関係のない制約まで判断に混ざる。たとえばUI作業中にインフラ専用の注意ばかり強く効くと、提案が過剰に慎重になったり、逆に必要なUI規約が埋もれたりする。そこで、ルートのCLAUDE.mdには共通ルールを置き、frontendやinfraなどのrulesファイルへ領域固有のルールを分ける。読む範囲を狭めることは、情報を減らすのではなく、今の作業に必要な前提を濃くする設計である。 |
```table
| 置き場 | 書く内容 | 効果 |
|---|---|---|
| ルートCLAUDE.md | 全体方針、禁止操作、共通コマンド、回答方針 | どの作業でも守る最低限の基準を固定する |
| frontend.md | UIライブラリ、コンポーネント設計、アクセシビリティ、状態管理 | 画面実装時に必要な判断だけを強く効かせる |
| infra.md | シェル前提、認証情報、デプロイ、破壊的操作の安全策 | 運用や自動化で事故につながる操作を抑える |
| data.md | データ保存場所、再現性、乱数シード、前処理手順 | 分析やML作業で結果の再現性を守る |
```
```conclusion
rules分割は、AIの認知負荷を下げ、作業場所に合うルールを前面に出す。
```

---

# 用途別テンプレートは判断を先に固定する
## Web、分析、自動化では、必要な安全策と前提が異なる
| key | value |
|-----|-------|
| layout | plain_2col |
| note | 用途別テンプレートを用意する意味は、文章量を増やすことではなく、作業領域ごとの判断を先に固定することにある。WebアプリではUIやAPI配置、データ分析ではライブラリと再現性、自動化ではOSやシェル、安全策が重要になる。右側のプロンプトは、このスライドに対応するnanobanana2用の画像生成指示であり、読み上げ原稿ではない。本文側では、用途ごとの違いが実務判断へどう効くかを明示している。 |
```card-a
### テンプレートは領域別の事故を減らす
作業領域ごとに、AIが先に確認すべき前提は変わる。テンプレートは、その違いを毎回の会話で説明し直さないための型である。
- **Webアプリ:** CSS、状態管理、API配置のルールを固定し、実装の揺れを抑える
- **データ分析:** ライブラリ、保存場所、乱数シードを明示し、結果の再現性を守る
- **自動化:** 対象OS、シェル、安全策、ログ出力を先に置き、破壊的操作を避ける
```
```card-b
### nanobananaプロンプト
    6:5 aspect ratio. Flat minimal business illustration, white background, no text. Show three connected template panels: a web app browser window, a data analysis chart with dataset blocks, and an automation terminal with a safety shield. Use clean geometric shapes, blue, teal, and green accents, modern presentation icon style.
```

---

# 運用ループでCLAUDE.mdを育てる
## 一度書いて終わりではなく、繰り返した注意をルールへ昇格させる
| key | value |
|-----|-------|
| layout | list_3card |
| note | 実際に運用する時は、CLAUDE.mdを完成品として固定しすぎないことが大切である。プロジェクトの技術スタックや作業習慣は変わるため、古いルールを残し続けると逆にノイズになる。会話で同じ注意を二度繰り返したらCLAUDE.mdへ昇格させ、古い制約は定期的に削る。さらに、小さなタスクでAIの振る舞いを確認すれば、ルールが本当に効いているかを早い段階で見つけられる。\n\n---\n\n[nanobanana2 icon prompt]\n6:5 aspect ratio. Three flat minimal business icons in one horizontal row, white background, no text. Left icon: speech bubbles turning into a rule document. Center icon: document with refresh arrows and eraser. Right icon: small test task card with checkmark and magnifying glass. Unified blue, teal, and lime palette, equal square icon areas. |
```card-a
### 2回言ったら昇格する
同じ注意が繰り返されるなら、それは会話ではなく常設ルールで扱うべき内容である。
- 例外的な依頼ではなく、今後も守る基準かを確認する
- 禁止操作、検証手順、回答スタイルなど再発しやすいものを優先する
- 昇格後は短い断定文にし、会話の文脈なしでも意味が通る形にする
```
```card-b
### 古いルールを削る
CLAUDE.mdは増やすだけではなく、効かなくなった情報を外すことで精度を保つ。
- 廃止したライブラリや古いコマンドを残さない
- 重複した表現をまとめ、重要な禁止事項が埋もれないようにする
- MEMORY.mdに任せられる弱い好みは強制ルールから外す
```
```card-c
### 小さくテストする
ルールを書き換えた後は、AIの振る舞いが期待通りかを小さなタスクで確認する。
- 変更直後に簡単な修正依頼を出し、探索順序や検証コマンドを見る
- 期待と違う場合は、抽象語を行動レベルの指示へ変える
- うまく効いたルールは、他プロジェクトへ横展開できる形に整える
```

---

# 3レイヤーでTakuya環境に合わせる
## 共通の好み、プロジェクト制約、ディレクトリ固有ルールを分ける
| key | value |
|-----|-------|
| layout | bg_3card |
| note | 最後に、Takuyaさんの環境へ落とし込むなら、全プロジェクト共通、プロジェクト単位、ディレクトリ単位の三層で考えるのが扱いやすい。グローバルには日本語回答やテスト重視などの普遍的な好みを置く。プロジェクト単位には技術スタック、禁止操作、ディレクトリ構成を置く。さらにUIとPowerShellやPythonのインフラ操作をrulesで分ければ、作業場所に合った制約だけが効きやすくなる。CLAUDE.mdはAIを縛るためではなく、迷わず安全に動かすための設計面である。\n\n---\n\n[nanobanana2 icon prompt]\n6:5 aspect ratio. Three flat minimal business icons in one horizontal row, white background, no text. Left icon: globe with preference sliders. Center icon: project folder with technology blocks and warning shield. Right icon: split directory tree with UI panel and terminal panel. Unified blue, teal, and green palette, equal square icon areas. |
```section
Takuyaさんの運用では、すべてを1つのCLAUDE.mdへ詰め込まず、効かせたい範囲ごとにルールを分けることで、AIの初動と安全性を両立できる。
```
```card-a
### グローバル
全プロジェクトに共通する性格や好みを置く層である。
- 日本語での回答、テスト重視、説明の粒度などを固定する
- 個別技術に依存しないため、全作業で効いても邪魔になりにくい
```
```card-b
### プロジェクト単位
対象リポジトリの技術と危険操作を扱う層である。
- 使用フレームワーク、ディレクトリ構成、実行コマンドを明示する
- 本番環境や秘密情報など、推測で触ると危険な対象を禁止する
```
```card-c
### ディレクトリ単位
作業場所ごとに違う判断を、rulesで局所的に効かせる層である。
- フロントエンドUIとPowerShell/Python操作を分離する
- 今触っている領域だけに必要なルールを読ませ、余計なノイズを減らす
```
