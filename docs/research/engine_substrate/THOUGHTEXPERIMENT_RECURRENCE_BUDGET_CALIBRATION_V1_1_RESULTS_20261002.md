# Thoughtexperiment recurrence budget calibration v1.1 — results

**Outcome: 12/12 independent analysis checks pass.** The fresh graph generator was exercised at arities 2, 4, and 8 with per-stage budgets of 200, 400, and 800 rule calls against a 1,000-call reference. Four workers each supplied two training and two held-out episodes per arity, with eight fixed proposals per episode. Training decisions select `dedup_identity_fix` in all 12 worker/arity cells for the reference and every bounded budget. Tie and all-wrong controls abstain in all 24 control decisions.

Each arity/split arm contains 64 paired candidate episodes. Every budget preserves the reference pass/fail outcome on all 64 training and all 64 held-out episodes. The selected repair succeeds and reaches fixed point on all 8 held-out episodes per arity and on all training samples. Forty of 64 proposals per arity/split exhaust their budget at the first stage; none of the reference-resolved episodes are falsely rejected. These are budget exhaustions, not termination proofs.

| Due-candidate arity | Reference median ms/episode | 200-call median ms | 400-call median ms | 800-call median ms | Outcome parity per arm | False rejects |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 428.1 | 23.4 | 74.9 | 280.7 | 64/64 | 0 |
| 4 | 435.5 | 23.1 | 77.1 | 275.3 | 64/64 | 0 |
| 8 | 429.6 | 25.3 | 75.9 | 284.8 | 64/64 | 0 |

The pooled episode median falls by 18.3×, 5.7×, and 1.5× at budgets 200, 400, and 800 for arity 2; the other arities show similar ratios. These savings come from rejecting poor proposals early. The selected candidate's own median runtime remains roughly 8–12 ms across arms, with no meaningful speedup; its measured rule work rises from 4 to 8 to 16 units as arity doubles. Overall cost is therefore sensitive to the mix of useful and poor proposals, not just the cost of applying the selected repair.

This is an independent graph-construction path with a different keyed workload size, but it reuses the same recurrence rule family, fixed candidate generator, and synthetic oracle. Arity had little effect on pooled latency because the five repeatedly capped proposals fail at the first candidate in every cell. Do not generalize this to other proposal distributions, natural tasks, or engine-level closure. The first v1 capture is retained as a censored pilot: its selector descriptor field mismatch caused every training decision to abstain. The v1.1 capture uses the corrected opaque-ID mapping; the analyzer is frozen before capture and passes all checks.

## Artifacts

- [Preregistration v1.1](THOUGHTEXPERIMENT_RECURRENCE_BUDGET_CALIBRATION_V1_1_PREREG_20261002.md)
- [Pilot amendment](THOUGHTEXPERIMENT_RECURRENCE_BUDGET_CALIBRATION_V1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_budget_calibration_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_budget_calibration_v1_1_lock_20261002.json)
- [Training orders](../../../evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_1_scores_20261002.json)
- [Frozen analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_budget_calibration_v1_1.py)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_1_analysis_20261002.json)

