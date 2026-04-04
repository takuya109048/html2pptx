# Skill Benchmark: slide-deck-creator — Iteration 2

**Model**: claude-sonnet-4-6
**Date**: 2026-04-04
**改善点**: 枚数厳守ルール追加（six_slides 失敗を修正）

---

## サマリー

| Eval | with_skill | without_skill | Delta |
|------|-----------|---------------|-------|
| vague-request | **6/6 (100%)** | 1/6 (16.7%) | **+83.3pt** |
| detailed-request | **8/8 (100%)** ✨ | 3/8 (37.5%) | **+62.5pt** |
| content-focused | **8/8 (100%)** | 8/8 (100%)⚠️ | 0pt |

> ⚠️ content-focused without_skill は既存ファイルを参照して area engine 形式を習得 — 純粋比較にならず

---

## Iteration 1 → 2 改善比較

| Eval | iter-1 with_skill | iter-2 with_skill | 改善 |
|------|-----------------|--------------------|------|
| vague-request | ❌ レート制限 | **6/6 (100%)** | 復活 |
| detailed-request | 7/8 (87.5%) | **8/8 (100%)** | **+12.5pt** |
| content-focused | 8/8 (100%) | **8/8 (100%)** | 維持 |

**six_slides 失敗 → 修正完了**: 枚数不足（5枚→6枚要求）をスキルの「枚数厳守」ルールで解決。

---

## Eval 0: vague-request

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1 | valid_json | ✅ | ✅ |
| 2 | has_cover | ✅ layout:'cover' | ❌ type:'cover'のみ |
| 3 | multiple_slides | ✅ 6枚 | ❌ slides配列（最上位キー構造でない） |
| 4 | correct_engine | ✅ engine:'area' | ❌ なし |
| 5 | grid_structure | ✅ grid配列あり | ❌ content構造 |
| 6 | has_page | ✅ 全スライドに | ❌ なし |

**Score**: with_skill **6/6** vs without_skill **1/6**

---

## Eval 1: detailed-request

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1 | valid_json | ✅ | ✅ |
| 2 | six_slides | ✅ 6キー確認 | ✅ slides配列に6要素 |
| 3 | presenter_name | ✅ 田中太郎 | ✅ presentation.presenterに |
| 4 | affiliation | ✅ coverスライド直下 | ❌ 上位オブジェクトのみ |
| 5 | date | ✅ coverスライド直下 | ❌ 上位オブジェクトのみ |
| 6 | has_flow4 | ✅ step_head×4 | ❌ phases配列 |
| 7 | has_converge | ✅ card×3+arrow+conclusion | ❌ points配列 |
| 8 | page_numbers | ✅ 全スライドに | ❌ なし |

**Score**: with_skill **8/8** vs without_skill **3/8**

---

## Eval 2: content-focused

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1〜8 | 全項目 | ✅ 全合格 | ✅ 全合格 ⚠️ |

**注**: without_skill が既存ファイルを参照して area engine 形式を習得したため同点。純粋なゼロ知識比較としては無効。

---

## 総評

- **with_skill**: 全3 eval で 100% 達成 (iteration-1 の唯一の失敗 `six_slides` を修正)
- **without_skill**: eval-0/1 でカスタム形式を使用し大幅に失点。eval-2 はファイル参照で例外的に高得点
- **スキルの効果**: フォーマット準拠・枚数・発表者情報・構造セルの正確な使用で明確な優位性
