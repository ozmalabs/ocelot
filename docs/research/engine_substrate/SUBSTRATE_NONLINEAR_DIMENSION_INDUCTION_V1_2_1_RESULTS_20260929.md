# Nonlinear dimension induction current-source replication v1.2.1 results

## Admission and outcome

The source-refresh replication completed all 60 registered cases (three transform families × production/frozen arm × ten fresh substrates). The independent analysis passes all 12 gates, including exact schedule and lock checks, pre/post source/native stability, current source hash agreement, the loaded native extension hash, complete cells, linear positive-control acquisition and transfer, nonlinear-vs-linear separation, and frozen-arm mint behavior.

The current engine reproduces the prior bounded learning boundary:

| Transform | Production acquisition and transfer | Frozen/no-induction |
|---|---:|---:|
| Linear `T(x,y)=(x+y,2y)` | Exact matrix acquired and transfer recognized in 10/10 | No acquisition; both stages mint in 10/10 |
| Quadratic shear `T(x,y)=(x+y²,y)` | No operator acquired; both stages fall back to quanta in 10/10 | Both stages mint in 10/10 |
| Piecewise shear `T(x,y)=(x+max(y−1,0),y)` | No operator acquired; both stages fall back to quanta in 10/10 | Both stages mint in 10/10 |

Every current-source cell matches v1.1 process replicate 2 on semantic status, quantum count, and final generator state for the identical locked point schedules. This is a same-host source/build replication, not an independent environment replication.

## Closure cost

Median / p90 / maximum closure time across both stages and ten replicates, milliseconds:

| Family | Production induction | Frozen/no-induction |
|---|---:|---:|
| Linear | 36.65 / 75.29 / 78.37 | 0.492 / 0.605 / 0.789 |
| Quadratic shear | 1,066.69 / 2,068.18 / 2,104.29 | 0.473 / 0.548 / 0.715 |
| Piecewise shear | 42.20 / 78.19 / 99.12 | 0.476 / 0.550 / 0.758 |

The expensive quadratic miss persists in the current build: median enabled closure is about 1.07 s, over 2,000 times the frozen median. It finds no admissible operator on these samples. The result gives a concrete local cost for one small out-of-family shape and learner configuration; it is not a general worst-case or average-case bound. The linear and piecewise medians remain tens of milliseconds under enabled induction. All timings are one-host observations with ten repetitions per cell.

## Analyzer-attempt disclosure

The preceding v1.2 current-source capture is preserved as a diagnostic. Its capture and all semantic gates passed, but its analyzer emitted one false-negative provenance gate because a hard-coded comparison omitted the preregistration hash present in the locked source map. The v1.2.1 amendment corrects this comparison, repeats the experiment in fresh substrates, and passes every gate. V1.2 records are not pooled with the admitted v1.2.1 run.

## Interpretation and limits

The current production route acquires and reuses this in-family linear map. On the two tested nonlinear families it does not propose a transferable new operator and incurs far more work than the frozen path, especially for the quadratic shear. This confirms a bounded induction envelope and an expensive miss path; it does not establish how often natural tasks reach either route, whether a richer learner would succeed, or how costs amortize over repeated use. The held-operator control is reported separately in existing codebook-ablation results and is not counted as induction here.

## Reproduction artifacts

- [v1.2.1 analyzer amendment](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_2_1_AMENDMENT_20260929.md)
- [Current-source preregistration](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_2_CURRENT_SOURCE_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_nonlinear_dimension_induction_v1_2_1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_nonlinear_dimension_induction_v1_2_1.py)
- [Comparison script](../../../scripts/compare_substrate_nonlinear_dimension_induction_current_source_v1.py)
- [Comparison analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_current_source_comparison_v1_20260929.json)
- [Raw capture](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_1_20260929.json)
- [Analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_1_analysis_20260929.json)
- [Source/native lock](../../../evaluation/substrate_capability/nonlinear_dimension_induction_v1_2_1_lock_20260929.json)
- [Preserved v1.2 diagnostic capture](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_20260929.json) and [false-negative analysis](../../../evaluation/reports/substrate_nonlinear_dimension_induction_v1_2_analysis_20260929.json)
