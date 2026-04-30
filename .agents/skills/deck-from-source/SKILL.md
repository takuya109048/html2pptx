---
name: deck-from-source
description: 原文ソース（テキスト/URL/ファイル）から分析済みスライドデッキMDとPPTXを生成するスキル。初回はPPTX生成へ進まず、必ずnanobanana2生成画像を使うかYes/No質問だけを返す。Yes/No回答後に、GLOBIS的な構成分析、MD生成、PPTX変換、md/pptxリンク提示まで実行する。カスタムGPTs流用前提（SKILL.md≤5000字、詳細はcontext.md）。
---

# deck-from-source

原文ソースから、発表用のスライドデッキMDとPPTXを生成する。
SKILL.mdは最小限の実行指示だけを持ち、詳細ルールは毎ターンcontext.mdから読む。

## 毎ターン最初に行うこと

file searchで次だけを実行する。

```json
{ "queries": ["context.mdのmd全文をfile search"] }
```

context.mdに、構成分析、レイアウト選択、MD構文、密度、note、ファイル名、ダウンロード提示の詳細がある。

## アップロードファイル解決

ターンBでcode interpreterを使う最初のコード冒頭に必ず入れる。

```python
import glob
_m = glob.glob("/mnt/data/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())
```

## ターン構造

このスキルは2ターンで動く。

ターンA:
ソースを受け取る。分析、判断、MD生成、PPTX生成はしない。次の質問だけを返す。

「nanobanana2による生成画像を挿入プランにしますか？ Yes / No で答えてください。（YesにするとPlainスライドに画像プレースホルダーとプロンプトを追加します。Noならテキスト中心で生成します）」

スライド枚数、発表者名、対象者は追加質問しない。必要ならターンBで自然に推定する。

ターンB:
直近のユーザー返答でYes/No方針を受け取ったら、ソース分析、構成決定、DECK_MD生成、自己点検、PPTX変換、リンク提示まで1ターンで完了する。思考過程、分析メモ、構成案はユーザーに出さない。

## ターンBの作業

1. ソース全体から主張、対象、目的、流れを内部分析する。
2. context.mdのSTORY_ANALYSIS、SOURCE_ENRICHMENT、TEMPLATE_WORKFLOW、MD_SYNTAX、CONTENT_LIMITS、CONTENT_VARIATION、SLIDE_STYLE、SPEAKER_NOTESに従ってDECK_MDを作る。薄い原文かどうかに関係なく、先に内部でだらだらと長文の詳細原稿へ書き直し、その厚みからスライドを設計する。
3. 2枚目は必ずplain_2colの目次にする。大見出しは内容上の章グループ、小見出しは3枚目以降の各スライドタイトルを一字一句そのまま使う。発表順に左カラムから積み、右カラムは入りきらない分だけを送るoverflow欄であり、前半/後半の分割にはしない。
4. nanobanana2がYesなら、plain_image_colとimage_label_1を使わない。プロンプト貼り付け用途はplain_2colを使い、左カラムに本文、右カラムにインデント式コードブロックのプロンプトを書く。plain_2col用は6:5説明図、card/step系の一括画像は6:5にせず3:1または4:1の横長アイコンストリップにする。
5. layoutごとの必須ブロック名を守る。plain_1colはcard-a、plain_2colはcard-a/card-b、flow_3stepはstep-a/step-b/step-c、flow_4stepはstep-a/step-b/step-c/step-dで書く。text、step、card、plainなどの独自ブロック名を作らない。
6. card-aなどの本文ブロック内にスライド区切りの3連ハイフンを書かない。
7. 生成後、DENSITY_REVIEWに従って目視で自己点検し、noteではなくスライド本文に厚みが戻っているかを確認する。短すぎる本文、flow系の名詞句だけのstep、弱いnote、単調な箇条書き、ですます調をDECK_MD本文で直す。
8. 表紙タイトルを短い英語のslugへ変換し、出力ファイル名に使う。詳細はcontext.mdのOUTPUT_FILESに従う。
9. mdとpptxだけをユーザーへ提示する。jsonは変換中に作ってよいが、ダウンロードリンクや最終報告には出さない。

## PPTX変換コードの型

nanobanana2がYesの場合、PPTX変換前にDECK_MDを必ず点検する。card/flow系はnote末尾に`[nanobanana2 icon prompt]`ブロックを置く。この一括アイコン素材では6:5を使わず、3要素なら3:1、4要素なら4:1の横長キャンバスに等幅アイコンを横並びで作る。プロンプト貼り付け用途はplain_2colにし、左を本文、右をインデント式コードブロックのプロンプトにする。plain_2col用の単体説明図だけ6:5を使い、画像内文字は短い日本語ラベルを許可する。note改行に`<br>`を使わず、表セル内では`\n`を書く。2枚目は必ずplain_2colの目次にし、3枚目以降のスライドタイトルを全件そのまま含める。本文密度はPython検証ではなくDECK_MD確定前の編集工程で担保する。ブロック名は`--strict-blocks`で検査されるため、存在しないタグを作らない。

DECK_MDを確定したら、code interpreterで次の型を使う。TITLE_SLUGは表紙タイトルを短い英語で表したsnake_caseまたはkebab-caseにする。

```python
import glob, os, subprocess, sys
MNT = "/mnt/data"
_m = glob.glob(f"{MNT}/*resolve_uploads.py")
if _m:
    exec(open(_m[0]).read())

TITLE_SLUG = "short_english_title"
DECK_MD = """(最終確定したDECK_MD全文)"""
deck_path = os.path.join(MNT, f"{TITLE_SLUG}.md")
json_path = os.path.join(MNT, f"{TITLE_SLUG}.json")
pptx_path = os.path.join(MNT, f"{TITLE_SLUG}.pptx")
with open(deck_path, "w", encoding="utf-8") as f:
    f.write(DECK_MD)
subprocess.run(
    [sys.executable, os.path.join(MNT, "md_to_json.py"), deck_path, pptx_path, "--json", json_path, "--assets-dir", MNT, "--nanobanana2", "--require-agenda", "--strict-blocks"],
    check=True, cwd=MNT,
)
for fn in [f"{TITLE_SLUG}.md", f"{TITLE_SLUG}.pptx"]:
    print(f"- [Download {fn}](sandbox:/mnt/data/{fn})")
```

## 変換補足

DECK_MD内の三重バッククオートはPythonの三重クオート文字列内でもそのまま貼れる。
/mnt/dataにスクリプト群がない場合は、context.mdのSETUP_SCRIPTに従って先に実行ファイル群を配置する。
