# Full-seed GenMint matrix/layout and reuse-cost results

## Result

The preregistered sweep completed 360 fresh-process workers across three matrices, three predicate layouts, induction on/off, K={0,1,2,4}, and five replicates. There were no worker failures; every worker had a unique PID. All 14 registered analysis gates pass, including exact reconstruction of the training and held-out inputs, balanced cells/schedules, deterministic outcomes within cells, source/native/lock digest agreement, route classification, and replication of the fixture-selection pilot. The raw record and analyzer retain every worker and per-stage result.

With induction enabled, the expected matrix was acquired in 8/9 matrix/layout cells: all five replicates for the prior matrix and `shearA` in every layout, plus `shearB` in `opposite_03` and `adjacent_12`; it was not acquired in `shearB × adjacent_01` (0/5). Overall this is 40/45 enabled training cases for each K prefix. This reproduces the pilot's interaction and shows that `recognized_transformed` is not a reliable proxy for acquisition of a particular matrix.

Among 280 held-out application calls routed through a matrix acquired during training, independent reapplication of the selected generator plus its residual transforms predicts all rows exactly (1,120/1,120). Other routes remain separately scored: 15 applications mint a generator during application, 20 reuse one first minted during an earlier application, and 315 have no selected generator transform. Thus successful matrix reuse is demonstrated on these authored clean fixtures, while the K=4 sequence still exposes routes that cannot be credited as training transfer.

## Paired costs

Medians below pool the 45 matched matrix/layout/replicate pairs at each K. They are descriptive closure timings from this host; timing excludes worker startup, seed boot, and graph construction. Peak RSS is full-process maximum resident set size, not an operation-level allocation measurement.

| K held-out tasks | Enabled median closure (ms) | Disabled median closure (ms) | Enabled faster pairs | Median enabled/disabled quanta | Median enabled/disabled peak RSS (KiB) |
|---:|---:|---:|---:|---:|---:|
| 0 | 3.796 | 0.872 | 0/45 | 0 / 1 | 41,884 / 41,928 |
| 1 | 4.614 | 1.730 | 0/45 | 0 / 2 | 41,836 / 41,844 |
| 2 | 5.635 | 2.779 | 0/45 | 0 / 3 | 41,824 / 41,952 |
| 4 | 7.614 | 5.644 | 1/45 | 0 / 5 | 41,852 / 41,964 |

The enabled arm has not reached a median runtime crossover by K=4 in any matrix/layout stratum; pooled enabled closure also remains slower at K=4. The operation outcome is nevertheless different: enabled cases that acquire a matrix use zero CapabilityAxis quanta across training and these applications, while disabled cases use one quantum at training and one for each held-out task. The result therefore establishes an acquisition/reuse mechanism and a bounded cost curve, not economic break-even. Enabled runtime includes GenInfer search during training, and the recorded application closures include the existing full rule closure, so this small K sweep cannot isolate the asymptotic cost of applying a generator or support extrapolation to larger reuse counts.

## Interpretation and limits

This is a positive result for route-level transfer on an authored 2-D integer-linear family. It confirms the previously observed shearB/layout miss rather than averaging it away. It does not establish a natural-task frequency, learned-frame cheap-cut prevalence, general learning accuracy, commodity-scale operation, or an asymptotic runtime class. Peak RSS is dominated by the full Python/native worker footprint at these sizes and shows no useful memory distinction. The next learning-cost measurement should extend reuse count and report a staged profile that separates training induction, held-structure application, and fixed closure overhead; include more matrix families and independently authored geometries. In parallel, the substrate-wide cheap-cut claim still needs representative natural or independently authored workloads with measured separator/boundary width and execution factorisation.

## Reproduction artifacts

- Preregistration: [protocol](SUBSTRATE_GENMINT_MATRIX_REUSE_PREREG_20260926.md)
- Exact source/design lock: [lock](../../../evaluation/substrate_capability/genmint_matrix_reuse_lock_20260926.json)
- Runner: [runner](../../../scripts/genmint_matrix_reuse_probe_v1.py)
- Analyzer: [analyzer](../../../scripts/analyze_genmint_matrix_reuse_probe_v1.py)
- Raw capture: [raw](../../../evaluation/reports/substrate_genmint_matrix_reuse_v1_20260926.json)
- Analysis: [analysis](../../../evaluation/reports/substrate_genmint_matrix_reuse_v1_analysis_20260926.json)
