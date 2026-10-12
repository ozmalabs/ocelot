# GenInfer shared-codebook versus frame-isolated cost v1.1 preregistration (2026-10-03)

## Question

How much closure cost does the shared-codebook search add relative to running
the same frame tasks with one eligible shape part per isolated substrate
instance? This is a controlled cost comparison; it does not claim that the
current engine discovers or enforces frame boundaries.

## Frozen shared-codebook baseline

The comparator is the completed 15-worker capture in
`SUBSTRATE_GENINFER_MULTIPART_CODEBOOK_SCALING_V1_RESULTS_20261003.md` and its
raw/analysis artifacts. Its K=1,2,4,8,16 workloads contain K frame-tagged base
parts and K corresponding observations in one graph. Every frame is exactly
matched to its expected transform. The shared capture was recorded at
2026-10-03T00:41:48Z on the current Linux host and native binary. Baseline
capture, lock, and analysis digests are included in this study's source lock.

## Isolated condition

For every shared K/repeat pair, run each of the same K frame inputs in its own
fresh full-seed graph/process with exactly one eligible base part and one
observation. Use the same four matrices in frame order and the same four
relations per frame. Each subprocess records its own closure wall/CPU time,
process HWM delta above post-boot input state, graph size, route receipt, and
generator inventory. The comparison sums closure times across the K isolated
frames and compares that total with the previously measured single shared
closure. Boot, child-process startup, data construction, and orchestration
are excluded from both timed totals; this isolates rule-settle/search cost.
The excluded setup cost is important: an eventual frame-partitioned system
must measure it before claiming an end-to-end advantage.

The isolated case has a theoretical and direct-code path of one eligible part
per query, B=3, or 2,400 candidate checks per new transform. Across K
independent frames the nominal sum is K×2,400. The shared baseline's pure
preflight diagnostic observed K²×2,400 checks across K queries, though
production closure can reuse generators after initial minting.

## Gates and interpretation

Require 15 K/repeat groups and exactly K isolated child workers in each group;
verify the previous shared capture and current source/native lock; require
every isolated output to recognize its exact locked matrix through its own
base; and require valid resource/timing fields. Report paired shared-to-
isolated closure-time ratios and memory deltas by K. No threshold is imposed
on the ratio. Interpret it only as the cost of one shared codebook closure
versus the sum of isolated closures on these authored maps. This is not a
comparison of task quality, total CPU across concurrent execution, graph
construction, or a deployed frame scheduler.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_geninfer_frame_isolation_v1_1.py`
- Analyzer: `evaluation/substrate_capability/analyze_geninfer_frame_isolation_v1_1.py`
- Source lock: `evaluation/substrate_capability/geninfer_frame_isolation_v1_1_lock_20261003.json`
- Raw capture: `evaluation/reports/geninfer_frame_isolation_v1_1_20261003.json`
- Analysis: `evaluation/reports/geninfer_frame_isolation_v1_1_analysis_20261003.json`
