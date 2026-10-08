# Scoped local candidate seeding results (2026-09-26)

## Result

The ownership-seeded one-edge rule matcher passes the amended topology matrix and its focused correctness controls. The capture reports 606/606 gates passed; the independent analyzer confirms the protocol, runner, Rust sources, native extension, and source fingerprint match. The initial v1 focused order oracle was invalid because unscoped closure continues through all bindings while a scoped progress step applies one. That failed pilot is preserved in the v1 raw capture; amendment v1.1 compares optimized scoped execution with the same scoped API forced through full-match/filter fallback.

The fast path is deliberately narrow: a single match edge, distinct source and target variables, an owned endpoint with the relevant typed adjacency, and no edge deletions anywhere in the graph. Unsupported shapes and any deletion use the previous full matcher/filter path. A monotone graph-wide deletion generation is necessary because edge-index slots are reused across edge types.

## Measurements

At 64 frames, median event/full candidate counts and audit-instrumented wall ratios were:

| Topology | Event candidates | Full candidates | Candidate ratio | Wall ratio |
|---|---:|---:|---:|---:|
| Chain | 2,591 | 32,385 | 0.080 | 0.357 |
| Binary tree | 2,774 | 3,429 | 0.809 | 3.077 |
| Star | 14,123 | 889 | 15.886 | 18.530 |

Thus candidate enumeration improves substantially for chains and modestly for the tree, but the tree remains about 3.1× slower in measured wall time. Star work grows sharply with frame count and is much worse than full closure. At smaller counts, chain crosses into a wall-time advantage by 32 frames; tree and star do not in this matrix. Timings include audit instrumentation and are descriptive; candidate and term-evaluation counts are the stronger evidence.

## Interpretation and next work

The optimization validates a local-candidate route for a common one-edge rule shape, not general frame-local tractability. It exposes scheduler/requeue overhead and hub fanout as the next bottlenecks: candidate filtering no longer explains the tree/star wall ratios. Next, attribute per-frame queue turns, ownership notifications, duplicate requeues, and local-vs-fallback matches on these same topologies; then test a hub-aware batching/coalescing change against the frozen parity matrix. Add deletion/reuse and multiedge fixtures to any future widening of the fast path. Natural task partitions and rung-3/4 cost remain unmeasured by this synthetic probe.

## Reproducibility

- Protocol: [v1 preregistration](SUBSTRATE_SCOPED_LOCAL_CANDIDATE_PREREG_20260926.md), [v1.1 amendment](SUBSTRATE_SCOPED_LOCAL_CANDIDATE_V1_1_AMENDMENT_20260926.md)
- Runner: [v1.1 runner](../../../scripts/substrate_frame_topology_local_candidates_v3_1.py)
- Analyzer: [independent analyzer](../../../scripts/analyze_substrate_frame_topology_local_candidates_v3_1.py)
- Raw capture: [JSON](../../../evaluation/reports/substrate_frame_topology_local_candidates_v3_1_20260926.json)
- Analysis: [JSON](../../../evaluation/reports/substrate_frame_topology_local_candidates_v3_1_20260926_analysis.json)
- Preserved pre-comment-fix native/source snapshot: `evaluation/substrate_capability/scoped_local_candidates_engine_snapshot_20260926/`
