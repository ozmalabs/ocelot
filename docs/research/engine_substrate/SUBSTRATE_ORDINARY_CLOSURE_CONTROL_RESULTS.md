# Ordinary closure fast-path control

**Status:** exploratory same-build paired instrumentation pilot; 320 isolated workers, 20 repeats per mode/point.

## Question and workload

How does the ordinary rule-closure path behave under the corrected engine when the rules have typed match-edge dependencies but no term-edge reads? This control reuses the two-rule transitive-closure workload: `link-link -> reach` and `reach-link -> reach`, on path and banded-DAG inputs at 16, 32, 64, and 96 nodes.

The fresh native extension was used in both the earlier term-edge fan-out sweep and this control. The shared worker checks exact closure against an independent expected-state calculation and performs a separate terminal no-work probe. Audit-on and audit-off workers use separate processes and identical generated inputs; mode order alternates across paired replicates. A native access-set audit independently confirmed that both closure rules have empty `term_edge_reads` at every workload point. Raw worker records and hashes are in [`substrate_ordinary_closure_control_20260924.json`](../../../evaluation/reports/substrate_ordinary_closure_control_20260924.json); the wrapper is [`substrate_ordinary_closure_control.py`](../../../scripts/substrate_ordinary_closure_control.py).

## Results

| Topology | Nodes | Candidates (audit on) | Off median wall | On median wall | Paired wall ratio, on/off | Paired ratio range |
|---|---:|---:|---:|---:|---:|---:|
| Path | 16 | 134 | 0.126 ms | 0.116 ms | 0.923× | 0.590–1.534× |
| Path | 32 | 526 | 0.316 ms | 0.301 ms | 0.993× | 0.552–1.564× |
| Path | 64 | 2,078 | 1.057 ms | 1.045 ms | 0.983× | 0.827–1.595× |
| Path | 96 | 4,654 | 2.439 ms | 2.931 ms | 1.051× | 0.644–1.747× |
| Banded DAG | 16 | 289 | 0.146 ms | 0.155 ms | 1.012× | 0.562–1.918× |
| Banded DAG | 32 | 1,105 | 0.398 ms | 0.408 ms | 1.010× | 0.575–1.531× |
| Banded DAG | 64 | 4,273 | 1.454 ms | 1.478 ms | 1.026× | 0.641–1.657× |
| Banded DAG | 96 | 9,489 | 3.466 ms | 3.458 ms | 1.007× | 0.701–1.627× |

All 320 workers match their exact graph-state oracle and report settled. On-mode counter invariants reconcile. Since there are no term-edge reads, the new cursor invalidation condition is false for this workload; new `reach` edges continue to be consumed through the match-edge incremental path. Median paired audit-on/off ratios cluster near 1, but every point's paired range spans substantial values below and above 1. This pilot therefore does not resolve a small instrumentation overhead; it does show no large consistent slowdown for the instrumented path in this setup. Runtime grows with both candidate work and closure output, which is quadratic in `n` for these families.

## Claim boundary and next step

This establishes a same-build ordinary closure baseline on two sparse synthetic topologies through 96 nodes and a paired instrumentation pilot. Twenty pairs per point are still too variable to identify small overhead reliably; no independent hardware replication, broad rule mix, or general scale claim is supported. Next carry the no-term-read control into selected task workloads and use a tighter timing protocol before making an instrumentation-cost claim.
