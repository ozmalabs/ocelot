# Recursive self-improvement, tranche 9: results (2026-10-08)

Follows the [tranche 8 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE8_RESULTS_20261008.md).

## Summary

| Item | Result |
|---|---|
| **Preregistered real-verdict credit gate v2** ([prereg](SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V2_PREREG_20261008.md)) | **PASS on all four gates.** Over 12 problems per arm, with two streams and two object templates: no credit 0/12 handled in 36 experiments; per-trial credit 11/12 in 20; credit plus the tranche-9 policy 12/12 in 18. 0 false adoptions. |
| Credit granularity (`credit_internal_exempt`, opt-in) | **Done.** A family with its own internal retry is not charged, within the same concern, for trials that still had an untried alternative. It recovers the tranche-8 miss (condense): `comprehend_text` refuted, then `world_action` supported. |
| `exclude_inconclusive` (opt-in) | **Done.** A family judged inconclusive for a concern is dropped from that concern. |
| Real-judge "too rarely" knob probe | **Null, diagnosed.** Both knobs tried were inconclusive (5 → 5 reform marks). The observable is saturated at its grain, so no step on the knobs available can produce more reforms without reforming everything. |
| Regression | **0 new failures** across 179 files. The failing set is identical to tranche 8. |

## 1. Credit policy options

`seeds/variation_ops.json` v1.11.0 is emitted by `scripts/gen_variation_credit_seed.py`, which is idempotent; `seeds/variation_credit.json` is byte-unchanged. Both new options are attributes on the agent's own `VariationPolicy` node, and absent means unchanged behaviour.

- **`exclude_inconclusive == 1`.** A family whose trial for this concern was judged inconclusive is excluded from this concern's pick. This mirrors `exclude_refuted`, including the same retry_internal exemption while an internal alternative remains.
- **`credit_internal_exempt == 1`.** In this concern's pick, a retry_internal family's trial count is reduced by its own non-supported trials on this concern that carried an internal alternative (`cue_route`). Credit for every other concern is still charged per trial.

  Rationale: while route exclusion is still working through the family's routes, a refuted route is evidence about that route, not yet about the family on this problem.

Tests in `tests/test_variation_credit_migrated.py`:
- `test_inconclusive_family_is_retried_unless_policy_excludes_it`
- `test_retry_internal_trial_with_alternative_is_not_charged_in_its_own_concern`. This test reproduces the tranche-8 condense arithmetic: per-trial credit scores 10·4/3 against 8·4/3 and leaves the family; with the exemption the score is 10·1. It also checks that a new concern of the same kind is still charged.

## 2. Credit gate v2 (preregistered)

Runner: `evaluation/substrate_capability/variation_credit_real_judge_v2.py`. Reports: six part files `variation_credit_real_judge_v2_{A,B,C}_{S1,S2}_20261008.json` plus `variation_credit_real_judge_v2_gate_20261008.json`.

| Arm | Policy | Handled | Experiments | First pick `cue_set_edit` | False adoptions |
|---|---|---|---|---|---|
| A | no credit | 0/12 | 36 | 0 | 0 |
| B | per-trial credit | 11/12 | 20 | 9 | 0 |
| C | credit + exempt + exclude_inconclusive | **12/12** | **18** | 10 | 0 |

Per stream:

| Arm | S1 ("the data") | S2 ("the list") |
|---|---|---|
| A | 0/6 in 18 | 0/6 in 18 |
| B | 5/6 in 11 | 6/6 in 9 |
| C | 6/6 in 9 | 6/6 in 9 |

All four gates hold: G1 (B > A, replication), G2 (C ≥ B on handled), G3 (C ≤ B on experiments) and G4 (no false adoptions in B or C).

The only difference between B and C in handled count is S1 condense:
- B: reply_ablation inconclusive → cue_set_edit/comprehend_text refuted → reply_ablation inconclusive. Not handled; the tranche-8 miss reproduced.
- C: reply_ablation inconclusive → cue_set_edit/comprehend_text refuted → cue_set_edit/world_action supported. Handled.

C also needed one fewer experiment on tabulate.

Caveats:
- Each run is deterministic, one per (arm, stream).
- Both templates share one sentence frame ("<Verb> the <object>."), with 11 distinct verbs.
- C differs from B by one problem. G2 and G3 are non-inferiority gates; this is not evidence of a large improvement.
- The A–B and A–C differences replicate tranche 8 on a second template.

## 3. "Too rarely" knob probe (real judge)

Runner: `knob_retry_probe_v2.py`. Report: `knob_retry_probe_v2_rarely_20261008.json`.

- The concern was "you reform garden path sentences too rarely, test whether the threshold is too high".
- The corpus was 10 garden-path and centre-embedded statements. They were chosen after measuring their reading signals beforehand, and that choice is disclosed in the runner docstring.
- The builder read `increase_fires` and stepped knobs down.
- The agent's own retries tried:
  - `reform_eviction_threshold` 2.0 → 1.9: inconclusive;
  - `reply_ablation`: inconclusive;
  - `reform_swallowed_threshold` 0.5 → 0.4: inconclusive, 5 → 5 reform marks.
- Retries stopped at the bound. Nothing was adopted and no reply changed.

Diagnosis:
- The `reform_overcomplex_clause` disjuncts read `residual_marker_count` (0 on every parse) and `swallowed_ratio` (0 or 0.5 on every parse).
- All 5 parses at 0.5 already reform at the held threshold 0.5. The other 5 sit at exactly 0.
- `reform_eviction_threshold` is not read by that rule.

So there is no parse just below a threshold. The observable's values are halves, and the next step on its grain (0.5 → 0) would reform every parse, signal or not.

The honest conclusion is that the "too rarely" direction is wired end to end: builder, delta, judge. On this reading layer, however, the observable is saturated, and a fixed 0.1 step is off-grain. Two things are needed:
- the knob step should be quantised to the observable's own grain (the set of distinct values the signal takes);
- the corpus needs a signal that has headroom.

## 4. Regression

Scope: `/tmp/pfv14/t8scope.txt`, 179 files, against `pf_t8.failed`.

**0 new failures.** The failing set is identical to tranche 8 (92 tests, all pre-existing). `test_residual_promote` timed out, as it has in every earlier tranche. The seeds the runs could write to (`comprehend_instruction`, `experiment_conclusions`) were byte-identical after every run.

## Next

- **Grain-quantised knob steps.** Step to the next distinct observed value of the signal the knob gates, never by a fixed 0.1. This turns the "too rarely" null into a real test, and it follows the exact-approximation rule (dynamic quantization, not tolerance).
- **More frames.** Credit gate v3 should use different sentence frames, not only different verbs and objects, and should mix concern kinds so credit is tested across kinds.
- **Make the tranche-9 policy the default.** It is opt-in now. Promotion needs an independent stream that it does not regress.
- **The 11 malformed seeds** that fail on every boot.
