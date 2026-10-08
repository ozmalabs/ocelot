# Endpoint-degree join-order oracle v1 results (2026-09-27)

## Result

The source/native-locked evaluation covered **54 fresh-process cells**: `M={4,16,64}`, balanced decoy ratios `D/M={0,4,16}`, the current count-based tie control, and the endpoint-degree policy, with three replications. The independent analyzer passed **491/491 checks**. All 54 worker inputs remained stable. Audit-on/off states and control/policy final graphs match exactly; queue work, outputs, installed order, and candidate accounting pass every gate.

The exact fixture cost model predicts the writer-rule candidate count for both installed orders in every cell. It chooses `left→right`, which the current install-time reorderer realizes when the authored match list is reversed. The control is authored `left,right`, which the same tie handling installs as `right→left`.

| `M` | `D/M` | Writer tests: count control → policy | Planner wall / CPU | Combined measured wall: control → policy |
|---:|---:|---:|---:|---:|
| 4 | 0 | 22 → 10 | 44 / 49 µs | 266 → 322 µs |
| 4 | 4 | 158 → 18 | 57 / 61 µs | 277 → 294 µs |
| 4 | 16 | 1,334 → 42 | 58 / 61 µs | 294 → 321 µs |
| 16 | 0 | 274 → 34 | 52 / 55 µs | 363 → 418 µs |
| 16 | 4 | 2,354 → 66 | 63 / 66 µs | 372 → 496 µs |
| 16 | 16 | 20,882 → 162 | 107 / 112 µs | 475 → 431 µs |
| 64 | 0 | 4,162 → 130 | 76 / 80 µs | 678 → 763 µs |
| 64 | 4 | 37,058 → 258 | 113 / 117 µs | 854 → 776 µs |
| 64 | 16 | 332,354 → 642 | 273 / 278 µs | 2,355 → 924 µs |

“Combined measured wall” is the median of per-replication planner wall time + writer-rule installation time + uninstrumented closure-call wall time. It excludes graph construction, target-rule installation (common to both policies), Python/process startup, readback, and analysis. The candidate-work reductions range from **2.2× to 518×**. The combined wall measure is worse for six of nine settings and better for three; the largest improvement is at `M=64, D/M=16`. The exact candidate oracle is therefore not economical as an always-on policy at these small scales. At that largest setting, plain closure median falls from 2.239 ms to 0.536 ms, and the charged combined median falls from 2.355 ms to 0.924 ms. Three repetitions make these timing estimates descriptive, not a stable performance guarantee.

## Interpretation and limits

This establishes an executable exact cost oracle for one two-edge schema and confirms its candidate predictions against the native matcher. It also demonstrates the economic gate: lowering candidate counts does not guarantee net benefit when planning overhead dominates. The estimator scans relation-pair lists in Python and exploits known two-edge structure; it is not a general engine optimizer, and it does not establish that a broader estimator can remain cheap.

Next implement a bounded endpoint-degree estimator for multi-edge patterns using the matcher's bound-source, bound-target, and both-bound access costs. Compare prediction error, planning cost, native candidate work, wall time, and peak RSS against the current installer. Include a threshold policy that skips estimation when its predicted work reduction cannot repay planning cost, then replay frozen task-derived rules before making general tractability claims.

## Artifacts

- [Preregistration](SUBSTRATE_ENDPOINT_DEGREE_JOIN_ORDER_V1_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_endpoint_degree_join_order_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_endpoint_degree_join_order_v1.py)
- [Raw workers](../../../evaluation/reports/substrate_endpoint_degree_join_order_v1_workers_raw_20260926.json)
- [Run summary](../../../evaluation/reports/substrate_endpoint_degree_join_order_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_endpoint_degree_join_order_v1_analysis_20260926.json)
- [Source/native lock](../../../evaluation/substrate_capability/endpoint_degree_join_order_v1_lock_20260926.json)
