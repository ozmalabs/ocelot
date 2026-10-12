# Residual CoW fanout memory v1 results

The source-locked matrix passes all semantic, source, process-identity, and return gates: 18 fresh workers cover 100,000 unrelated host nodes × fanout 1/4/16 × full-copy/shared-graph-pages × three repeats. Every branch independently proposes `flip_comparison`, passes held-out scoring, and preserves its target rule. The host stays unchanged through exploration; exactly one validated 41-node/2-edge residual is returned, and the host rule store remains unchanged.

## Memory and branch cost

Values below are medians of current process `smaps_rollup` PSS deltas from the host baseline, in MiB. The branches are created and evaluated sequentially, then retained together for the sampled fanout state; this measures retained branch fanout, not parallel execution.

| Backend | Fanout | After forks | After candidate generation | After validation/package | After one return | After branch drop |
|---|---:|---:|---:|---:|---:|---:|
| Full copy | 1 | 1.9 | 4.9 | 8.6 | 25.6 | 25.6 |
| Full copy | 4 | 2.6 | 5.2 | 16.7 | 17.1 | 17.1 |
| Full copy | 16 | 154.0 | 178.2 | 209.9 | 209.9 | 209.8 |
| Shared graph pages | 1 | 1.9 | 4.9 | 8.6 | 9.9 | 9.9 |
| Shared graph pages | 4 | 2.6 | 5.2 | 16.7 | 23.7 | 23.6 |
| Shared graph pages | 16 | 2.6 | 6.4 | 36.8 | 38.0 | 37.8 |

At fanout 16, median per-branch fork latency is 17.32 ms for full copy and 0.186 ms for shared graph pages. Induction plus grounding is much larger: roughly 82–103 ms per branch across these cells; held-out scoring adds unreported time. There is no consistent backend advantage in candidate generation. Peak process RSS at fanout 16 is 828,768 KiB full copy and 545,984 KiB shared pages. These numbers describe one host, one rule family, and one 100k-node graph representation.

PSS/RSS remains well above baseline after branches are dropped, especially after one residual is adopted. Current mapping does not distinguish allocator-retained pages from still-live substrate state, so this is not a leak finding or a reclamation guarantee. The 5.6× fanout-16 PSS difference supports a substantial resident-memory benefit for this partial-CoW backend on this fixture. No concurrency throughput, natural-task rate, vLLM-style serving, complete-state CoW, or general performance estimate follows.

## Artifacts

- Protocol: [preregistration](RESIDUAL_COW_FANOUT_MEMORY_V1_PREREG_20261002.md)
- Runner: [measurement script](../../../evaluation/substrate_capability/measure_residual_cow_fanout_memory_v1.py)
- Analyzer: [independent gate checker](../../../evaluation/substrate_capability/analyze_residual_cow_fanout_memory_v1.py)
- Lock: [source lock](../../../evaluation/substrate_capability/residual_cow_fanout_memory_v1_lock_20261002.json)
- Raw workers: [capture](../../../evaluation/reports/residual_cow_fanout_memory_v1_20261002.json)
- Analysis: [gate results](../../../evaluation/reports/residual_cow_fanout_memory_v1_analysis_20261002.json)
