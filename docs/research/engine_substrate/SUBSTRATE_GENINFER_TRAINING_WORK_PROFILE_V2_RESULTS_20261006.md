# GenInfer relation-count × matrix-bound profile — results

All 27 fresh workers passed the independent gate. The capture records one source-matched 64-shard native artifact, stable per-worker source manifests, exact transformation semantics, and reconciled native counters. The analyzer confirms the treatment bound is the observed training bound in every cell.

## Factorial results

Audit-enabled training medians, native matrix attempts, and GenInfer-attributed term units:

| Relations N | Bound B | Training ms | Matrix attempts | GenInfer term units | Units / attempt |
|---:|---:|---:|---:|---:|---:|
| 4 | 3 | 10.186 | 4,800 | 76,800 | 16 |
| 4 | 5 | 53.663 | 29,280 | 468,480 | 16 |
| 4 | 7 | 183.345 | 101,248 | 1,619,968 | 16 |
| 16 | 3 | 39.007 | 4,800 | 307,200 | 64 |
| 16 | 5 | 217.334 | 29,280 | 1,873,920 | 64 |
| 16 | 7 | 764.971 | 101,248 | 6,479,872 | 64 |
| 64 | 3 | 148.831 | 4,800 | 1,228,800 | 256 |
| 64 | 5 | 891.993 | 29,280 | 7,495,680 | 256 |
| 64 | 7 | 3,001.706 | 101,248 | 25,919,488 | 256 |

Every cell has two eligible bases. Attempts equal `2 × ((2B+1)^4−1)`: 4,800 at B=3, 29,280 at B=5, and 101,248 at B=7. GenInfer term units are exactly `4N` per attempt across all nine cells. Source inspection ties those units to N aligned relation-pair checks plus 3N slot comparisons in `build_candidate`; the candidate is checked in two passes. This directly identifies a repeatable relation-scan cost for every enumerated matrix.

At fixed N, runtime follows attempt count: increasing B=3→5 multiplies attempts 6.1× and time 5.3–6.0×; B=5→7 multiplies attempts 3.46× and time 3.36–3.52×. At fixed B, increasing N=4→64 multiplies GenInfer term units exactly 16× and audit-enabled time 14.6–16.6×. The combined N=4/B=3 to N=64/B=7 cell increases term units 337× and time 295×. These are directional relationships in this fixture, not confidence intervals or broad asymptotic proof. Cells ran serially in fixed N-major order, so host drift and thermal effects could influence the timing gradients; the exact counter relationships do not depend on timing.

The observed work model for this 2D family is `4 × N × P × ((2B+1)^4−1)` term units, where `P=2` eligible bases. The current Rust operation explicitly skips signatures whose coordinate count is not exactly two. Higher-dimensional induction is therefore outside the implemented path; the `d²` matrix exponent is a theoretical cost for a generalized implementation, not a measured engine capability.

All positive cells acquire the transform, pass exact held-out transfer, and reject corrupted held-out data. Candidate and apply rejects are zero in every training cell; nearly all attempts reach residual validation and are rejected there. This suggests a potential optimization target in candidate validation, but any early exit or scan fusion must preserve selection and receipts exactly across broader differential workloads.

## Interpretation and next gate

This work narrows the tractability claim. With coordinate dimension fixed at two, candidate enumeration scales with the fourth power of the data-derived bound, and each candidate incurs relation-proportional work. On this workload the bound and relation-count effects are nearly multiplicative. That is a concrete operating-cost model for this rung, not a general learning guarantee. The empirical distribution of B and number of eligible bases on natural tasks remains unknown.

Next compare the current two-pass `build_candidate` validation with an exact one-pass/fused-check implementation. Preserve current matrix candidate order and exact selected generators, residuals, rejection behavior, and transform receipts. Measure term-unit reduction, audit-off wall time, allocation/copy work, and semantic parity on multiple separately authored shape families before promoting a code change. Keep the existing implementation as the control. Also retain a task-mix measurement for the natural frequency and bound distribution; the synthetic factorial cannot supply that prior.

## Artifacts

- [Preregistration](SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V2_PREREG_20261006.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_training_work_profile_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v2.py)
- [Raw capture](../../../evaluation/reports/substrate_geninfer_training_work_profile_v2_20261006.json)
- [Analysis](../../../evaluation/reports/substrate_geninfer_training_work_profile_v2_analysis_20261006.json)
