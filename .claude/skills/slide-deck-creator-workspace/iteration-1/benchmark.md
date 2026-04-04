# Skill Benchmark: slide-deck-creator — Iteration 1

**Model**: claude-sonnet-4-6
**Date**: 2026-04-04
**Evals**: 3 (vague-request, detailed-request, content-focused)
**Runs per config**: 1

---

## Summary

| Eval | with_skill | without_skill | Delta |
|------|-----------|---------------|-------|
| vague-request | ❌ rate limit | ❌ rate limit | N/A |
| detailed-request | **7/8 (87.5%)** | ❌ rate limit | N/A |
| content-focused | **8/8 (100%)** | 5/8 (62.5%) | **+37.5pt** |

> ⚠️ eval-0 (vague-request) both runs hit rate limits. eval-1 without_skill also rate limited.
> Valid comparison available for eval-2 (content-focused) only.

---

## Eval 0: vague-request

**Prompt**: 新製品発表のプレゼン資料のJSONを作って

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1 | valid_json | ❌ rate limit | ❌ rate limit |
| 2 | has_cover | ❌ rate limit | ❌ rate limit |
| 3 | multiple_slides | ❌ rate limit | ❌ rate limit |
| 4 | correct_engine | ❌ rate limit | ❌ rate limit |
| 5 | grid_structure | ❌ rate limit | ❌ rate limit |
| 6 | has_page | ❌ rate limit | ❌ rate limit |

---

## Eval 1: detailed-request

**Prompt**: AIを活用したコスト削減の提案書のJSONを生成して。…6枚構成。発表者: 田中太郎、所属: DX推進部、日付: 2026-04-10

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1 | valid_json | ✅ | ❌ rate limit |
| 2 | six_slides | ❌ 5枚生成（1枚不足） | ❌ rate limit |
| 3 | presenter_name | ✅ 田中太郎 | ❌ rate limit |
| 4 | affiliation | ✅ DX推進部 | ❌ rate limit |
| 5 | date | ✅ 2026-04-10 | ❌ rate limit |
| 6 | has_flow4 | ✅ step_head×4確認 | ❌ rate limit |
| 7 | has_converge | ✅ card×3+arrow+conclusion | ❌ rate limit |
| 8 | page_numbers | ✅ 全スライドにpage | ❌ rate limit |

**Score**: with_skill 7/8 (87.5%) — with_skill生成は構造正確。枚数1枚漏れのみ。

---

## Eval 2: content-focused

**Prompt**: 四半期レビュースライドのJSONを5枚で作って。…

| # | Assertion | with_skill | without_skill |
|---|-----------|-----------|---------------|
| 1 | valid_json | ✅ | ✅ (独自形式) |
| 2 | five_slides | ✅ slide_01-05 | ✅ slides配列×5 |
| 3 | cover_title | ✅ "Q2 2026 業績レビュー" | ✅ titleフィールドに含む |
| 4 | table_data_120m | ✅ rows[0]="120M" | ✅ |
| 5 | table_data_profit | ✅ rows[2]="30M" | ✅ |
| 6 | has_table_conclusion | ✅ rowHeightRatios+grid構造 | ❌ grid構造なし |
| 7 | three_cards | ✅ card×3 in grid | ❌ cardsネスト配列 |
| 8 | flow_3step | ✅ step_head×3確認 | ❌ steps配列(step_headなし) |

**Score**: with_skill **8/8 (100%)** vs without_skill **5/8 (62.5%)**

---

## Key Findings

1. **フォーマット遵守**: without_skillは独自JSON形式（カスタム`type`/`template`/`content`構造）を生成。`engine:"area"`、`grid`配列、`step_head`セルタイプを使用しない。スキルがあれば100%正確なtemplates.jsonフォーマットを出力。

2. **構造精度**: スキルなしでは`three_cards`・`flow_3step`・`table_conclusion`のgrid構造assertion全敗。スキルありでは全合格。

3. **詳細指示への対応**: with_skillは発表者名・所属・日付・フロー構造・収束構造を全て正確に生成（6枚指定に対し5枚のみ軽微ミス）。

4. **レート制限**: vague-request eval（eval-0）は両runともレート制限でデータ取得不可。次回の再実行が必要。

---

## Next Steps

- [ ] eval-0 (vague-request) を再実行（レート制限解除後）
- [ ] detailed-request without_skill を再実行
- [ ] six_slides失敗の原因調査 → SKILL.mdに「枚数を必ず守る」指示を追加
- [ ] iteration-2で改善スキルを評価
