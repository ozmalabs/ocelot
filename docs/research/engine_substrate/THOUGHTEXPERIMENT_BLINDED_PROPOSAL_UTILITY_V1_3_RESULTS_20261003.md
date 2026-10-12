# Blinded proposal utility v1.3 — source-current results

Date: 2026-10-03

## Gate result

The source-current rerun reproduces the bounded four-family selection panel.
Four worker seeds each evaluate shape-axis, recurrence, navigation, and
control-kind repairs under experience ranking, frozen ranking, default order,
random order, and target memoization. The held-out order was frozen before
held-out scoring. All 104 worker/family/candidate held-out instances were
scored once; all 144 policy-prefix trials and all 104 exhaustive-audit branches
verified their candidate receipts and preserved primary state. The independent
analyzer passes 7/7 checks, and all 49 locked source/build inputs match before
and after capture and against the current checkout.

The candidate labels and set sizes match v1.2 in all four families (6 shape,
8 recurrence, 6 navigation, 6 control-kind candidates). Held-out first-choice
successes reproduce: experience ranking 8/16, frozen ranking 0/16, default
order 16/16, random order 5/16, and target memoization 16/16. Median attempts
are 1.5 for experience, 2 for frozen, 1 for default, 3 for random, and 1 for
target memoization. Thus experience evidence improves over the frozen rank in
this sample, but it does not beat the unchanged default or same-target
memorization controls.

## Cost and limits

Median end-to-end selection cost is 3.76 s for experience ranking, 103 ms for
frozen ranking, 49 ms for default order, 336 ms for random order, and 886 ms for
target memoization. Experience ranking's cost includes acquiring labeled
outcomes across the other task families. Exhaustive candidate auditing is
measured separately and is not treated as a free runtime capability.

This establishes current-source reproduction of bounded outcome-guided
candidate ranking and cross-family records over four authored families. It
does not show broad transfer: two families benefit from matching cross-family
outcome classes, while navigation and control-kind do not. Candidate generation
is a small fixed set from `_default_candidates` and reusable edit operations;
new operators, open-ended structure induction, natural task prevalence, and
incremental task-solving benefit remain unestablished.

## Artifacts

- [Source-refresh amendment](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_SOURCE_REFRESH_20261003.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_3.py), [analyzer](../../../scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1_3.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_3_lock_20261003.json)
- [Frozen orders](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_3_orders_20261003.json), [held-out scores](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_3_scores_20261003.json), [analysis](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_3_analysis_20261003.json)
- [Historical v1.2 results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_RESULTS_20261002.md)

## Next gate

Extend candidate generation beyond the fixed single-edit list, beginning with
multi-edge identity-aware guards and a controlled actor/verb output task. Freeze
the generated candidate pool before revealing held-out outcomes; compare pool
coverage, false-proposal rate, candidate count, search cost, and held-out
utility against the current generator. Keep a source-rule positive control and
the known actor-recipient false-suppression case. This tests whether the
substrate can acquire a missing edit structure without silently widening the
oracle or selecting only on held-out outcomes.
