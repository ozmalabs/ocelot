# SynthEnumerate nonlinear-map acquisition v1.1 — results

**Date:** 2026-09-29. **Purpose:** measure whether the native bounded `SynthEnumerate` route can acquire small executable graph Terms for nonlinear coordinate maps, transfer them to held-out inputs, and separate acquisition cost from repeated application cost. This is a fixed synthetic grammar probe, not a general induction or capability result.

## Protocol and integrity

The registered design has four tasks (linear control, quadratic shear, hinge shear, and absolute-value shear), five grammars, five fresh substrate repetitions per task/grammar cell, six held-out inputs per acquired Term, a maximum size of 7–9 by task, and a 150,000-candidate cap. It includes 40 acquisition cells. Each acquired Term is independently replayed against the locked training and holdout tables. The v1.1 analyzer passes all nine gates, including source/native provenance, the complete unique matrix, candidate accounting, exact rechecks, the linear positive control, and capture stability. The separate version-comparison audit passes all five checks: preregistered cells match, terms and outcomes match v1 cell by cell, v1.1 per-call costs recompute from raw nanoseconds, source/native capture is stable, and both independent gate reports pass.

The initial v1 report mislabeled raw nanoseconds per call as milliseconds per call. Its raw capture and analysis remain preserved as diagnostic evidence; those displayed costs are invalid and are excluded here. V1.1 is a fresh source/native-locked repeat with unchanged task points, grammars, budgets, schedule, and scoring. The comparison artifact is a descriptive audit, not pooled evidence or an additional preregistered acquisition run ([amendment](SUBSTRATE_SYNTHENUMERATE_NONLINEAR_MAP_V1_1_AMENDMENT_20260929.md), [comparison audit](../../../evaluation/reports/synthenumerate_nonlinear_map_capture_comparison_v1_20260929.json)).

## Results

| Task | Grammar | Acquired | Exact holdout transfer | Median tested candidates | Median acquisition wall time |
|---|---|---:|---:|---:|---:|
| Linear | `plus_tuple` | 5/5 | 5/5 | 71 | 0.203 ms |
| Linear | `plus_minus_max_tuple` | 5/5 | 5/5 | 3,233 | 5.051 ms |
| Quadratic shear | `plus_tuple` (no multiply) | 0/5 | — | 84 | 0.208 ms |
| Quadratic shear | `plus_times_tuple` | 5/5 | 5/5 | 292 | 0.618 ms |
| Hinge shear | `plus_minus_tuple` (no max) | 0/5 | — | 15,143 | 33.514 ms |
| Hinge shear | `plus_minus_max_tuple` | 5/5 | 5/5 | 18,333 | 47.040 ms |
| Absolute shear | `plus_minus_tuple` (no abs) | 0/5 | — | 15,143 | 41.514 ms |
| Absolute shear | `plus_minus_abs_tuple` | 5/5 | 5/5 | 1,992 | 4.869 ms |

All 20 acquired Terms transfer exactly to all six registered holdout inputs in every repetition. The missing-operator arms refuse all 15 cases at the size boundary; none yields a false fit or transfer. Terms are stable within each acquisition cell. For batches of 100 native applications, median measured cost is 4.70–5.72 microseconds per call across the four acquired task/grammar pairs; single-call medians are 7.89–10.70 microseconds. These are in-process native evaluator timings for the exact returned Term, not whole-pipeline or external-service latency. The runner's total capture takes under one second; acquisition wall time includes each bounded search, while measured application batches are reported separately. Full per-cell counts and costs are in the [analysis](../../../evaluation/reports/synthenumerate_nonlinear_map_v1_1_20260929_analysis.json); raw worker rows are in the [capture](../../../evaluation/reports/synthenumerate_nonlinear_map_v1_1_20260929_raw.jsonl).

## Interpretation and limits

This demonstrates bounded program-term acquisition when the caller supplies an operator grammar containing the needed primitive. It shows a sharp refusal boundary when `Times`, `Max`, or `Abs` is absent, and low repeated application cost after successful acquisition. It does **not** demonstrate GenInfer discovering a nonlinear dimension, residual-driven escalation from transform failure, `DimensionGenerator` minting/adoption, a learned grammar, task-independent constants, noisy data handling, scaling beyond these tiny frames, or natural task frequency. The exact held-out transfer establishes correctness for these four formulas and six points, not broad generalization.

The earlier current-source GenInfer replication independently found linear transfer but failed on its two nonlinear families; this SynthEnumerate probe exposes a separate route that succeeds when its grammar already includes the needed operation. Thus it narrows the induction gap without closing the Rung 3/4 integration gap. Next test whether a preregistered residual can route into a bounded grammar-selection policy, charge grammar and search cost, and require a downstream held-out oracle before any new dimension is adopted. Keep a refusal budget and report unsupported-operator misses separately from search exhaustion ([preregistration](SUBSTRATE_SYNTHENUMERATE_NONLINEAR_MAP_V1_PREREG_20260929.md), [current-source GenInfer result](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_2_1_RESULTS_20260929.md)).
