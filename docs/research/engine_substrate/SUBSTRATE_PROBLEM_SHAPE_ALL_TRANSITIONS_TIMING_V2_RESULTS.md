# ProblemShape all-transition eventization timing V2 results

**Outcome:** all 12 fresh-process pairs passed semantic checks, with 24 unique worker PIDs and balanced arm order (six baseline-first, six candidate-first). This measures one authored N=8 recurrent-residual sequence and remains exploratory.

## Timing and work

The eventized candidate was faster in 7/12 pairs. Its median observe-path wall ratio was 0.968 (candidate/baseline), mean 1.006, with range 0.833–1.264. A paired bootstrap interval for the median ratio was 0.898–1.132 and therefore includes equal timing. Median process-CPU ratio was 0.973. This sample does not support a reliable wall-time improvement claim.

Operation counts were stable across pairs and showed a clear reduction on this fixed sequence:

| Measure | Full closure | Eventized candidate | Change |
|---|---:|---:|---:|
| ProblemShape candidate pairs | 263 | 66 | −74.9% |
| ProblemShape Term evaluations | 2,011 | 1,008 | −49.9% |
| `ps_mint` candidate pairs | 38 | 6 | −84.2% |
| `ps_mint` Term evaluations | 358 | 116 | −67.6% |

Median host index/event maintenance was 0.401 ms per worker. Median peak RSS was about 1.79 GB in both arms, dominated by full runtime/seed startup. Median full-seed boot wall time was roughly 22 seconds; boot is reported separately and excluded from the observation-path ratios.

The V2 raw report's baseline `ps_mint` summary fields contain zero defaults because the baseline worker schema does not export those summary keys. Treat those raw fields as missing, not measurements. The post-run correction analysis obtains baseline `ps_mint` counts from the `problem_shape_rule_scale_audit` rows in the pre-run hash-locked population-scale baseline artifact; the V2 raw file is preserved unchanged. See amendment [V2.2](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_2_AMENDMENT_20260925.md) and its [analysis report](../../../evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_analysis_20260925.json).

The first V2 coordinator attempt was observed running but left no aggregate artifact or recoverable exit status. It contributes no data. Amendment [V2.1](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_1_AMENDMENT_20260925.md) added atomic per-pair checkpoints before the completed 12-pair repetition. The amended run completed all gates.

## Interpretation and limits

The eventized variant substantially reduces measured rule work in this fixed sequence, but that reduction does not yield a resolved wall-time benefit here. Full-seed startup is expensive, host process RSS is too coarse to attribute the candidate's memory cost, and `tracemalloc` does not capture native allocations. The result does not establish a scaling law, natural-task locality, persistence/rebuild correctness, concurrency safety, rollback under injected failure, or a substrate-wide speedup. Broader N and task-sequence variants with allocation-level memory capture remain the next gate before considering any default-path change.

Artifacts: [V2 protocol](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_PREREG_20260925.md), [V2.1 execution amendment](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_1_AMENDMENT_20260925.md), [runner](../../../scripts/substrate_problem_shape_all_transitions_timing_v2.py), [pre-run lock](../../../evaluation/substrate_capability/problem_shape_all_transitions_timing_v2_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_20260925.json), [V2.2 readback amendment](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_2_AMENDMENT_20260925.md), [analyzer](../../../scripts/analyze_substrate_problem_shape_all_transitions_timing_v2.py), and [analysis](../../../evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_analysis_20260925.json).
