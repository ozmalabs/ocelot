# Discourse goal association guard v3 results

**Run:** 2026-09-26. **Grade:** four-arm locked diagnostic on one authored interleaved conversation fixture. No production rule or source code was changed.

## Semantic result

The baseline seed rules reproduce the v2 mismatch: both goals transition on events `[4,5,6]`. In the treatment arms, each lifecycle rule was replaced in memory with a copy requiring a shared `for_addressee` / `to_addressee` binding. The guarded full-closure arm follows the fixture's intended assignment exactly: origin 0 transitions on `[4,5,6]`; origin 3 transitions on `[7,8,9]`. This candidate fixes the observed fixture case. It is not a general identity solution: two concurrent goals for the same addressee remain ambiguous, and task/action links are not represented by this guard.

## Scheduling result

Under the guarded rules, the owner queue matched the full graph digest at all ten event checkpoints. Native write reports reached origin frame 0 when its result arrived at event 6 and origin frame 1 when its result arrived at event 9. The omitted-wakeup arm had stale receipts at both checkpoints and diverged through event 9. One final global closure restored exact graph parity. All scoped calls completed without deferred effects or budget exits. The independent analyzer passes 15 gates, including the source audit that found no domain-module call sites for the host `transition_goal` helper.

The external queue is slower than full closure in this small capture. Timings are single-run diagnostics only and do not show a performance benefit.

## Harness correction

The first capture was retained at [`attempt1_gatefail`](../../../evaluation/reports/substrate_discourse_goal_association_v3_attempt1_gatefail_20260926.json). One harness assertion incorrectly expected both origin frames to be notified at event 6. The amended preregistration maps the two result events correctly (frame 0/event 6 and frame 1/event 9); task, arms, and candidate guard were unchanged. The corrected locked capture passes all runner gates.

## Claim boundary

This measures one authored task, a manually declared partition, and one candidate rule guard. It supports a narrow correctness hypothesis: addressee matching is sufficient for this fixture and remains compatible with the tested owner-queue path. It does not establish production integration, general task identity, natural locality, or tractability at scale. See the [preregistration and amendment](SUBSTRATE_DISCOURSE_GOAL_ASSOCIATION_V3_PREREG_20260926.md), [runner](../../../scripts/substrate_discourse_goal_association_v3.py), [independent analyzer](../../../scripts/analyze_substrate_discourse_goal_association_v3.py), [lock](../../../evaluation/substrate_capability/discourse_goal_association_v3_lock_20260926.json), [raw capture](../../../evaluation/reports/substrate_discourse_goal_association_v3_20260926.json), and [analysis](../../../evaluation/reports/substrate_discourse_goal_association_v3_analysis_20260926.json).
