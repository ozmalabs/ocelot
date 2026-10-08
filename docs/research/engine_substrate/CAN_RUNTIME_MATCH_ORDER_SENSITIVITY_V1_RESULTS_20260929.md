# Runtime CAN match-order sensitivity v1 (2026-09-29)

## Result

All 16 fresh workers passed all eight gates: complete coverage, unique workers, only the two registered match-order changes, exact semantic parity, audited/uninstrumented parity, zero fixed-point residuals and terminal work, complete target-rule counters, and stable source/seed/native locks. The only experimental variant reorders the four positive match clauses in `can_native_hebbian_mint` and `can_native_hebbian_reweight`, starting from the sparse coactivation relations. Rule conditions and effects are unchanged; the repository seed remains unchanged.

| N | Topology | Mode | Target candidate pairs, base → reordered | Target Term evaluations, base → reordered | Plain closure, base → reordered (ms) | Candidate reduction | Time ratio |
|---:|---|---|---:|---:|---:|---:|---:|
| 128 | Path | 2-state | 5.97M → 0.179M | 30.1M → 1.02M | 1,269 → 344 | 33.3× | 3.69× |
| 128 | Path | 3-state | 4.80M → 0.176M | 24.3M → 0.998M | 1,047 → 299 | 27.3× | 3.50× |
| 128 | Banded-2 | 2-state | 7.63M → 0.230M | 38.5M → 1.30M | 1,657 → 444 | 33.2× | 3.74× |
| 128 | Banded-2 | 3-state | 5.62M → 0.196M | 28.4M → 1.11M | 1,249 → 345 | 28.7× | 3.62× |
| 256 | Path | 2-state | 62.5M → 0.953M | 314M → 5.41M | 14,245 → 3,446 | 65.6× | 4.13× |
| 256 | Path | 3-state | 48.0M → 0.881M | 241M → 5.00M | 10,814 → 2,870 | 54.4× | 3.77× |
| 256 | Banded-2 | 2-state | 83.2M → 1.27M | 417M → 7.18M | 19,220 → 4,875 | 65.7× | 3.94× |
| 256 | Banded-2 | 3-state | 57.1M → 0.991M | 287M → 5.62M | 12,962 → 3,435 | 57.6× | 3.77× |

Each cell reports the median of two paired workers. Candidate and Term counts aggregate the two target rules only. Wall times are uninstrumented closure times; the audited variant is run separately and is excluded from timing comparisons.

## Semantic parity and interpretation

In every worker, baseline and reordered variants reached the same progress count and named Concept state. A canonical whole-graph signature (node types/attributes and typed directed edges, independent of allocation IDs) and extracted CAN model signature also matched. The reordered run's audit-enabled twin matched its uninstrumented run, and an independent fixed-point predicate over the final extracted network found zero residuals. Thus the large work reduction is not explained by dropped graph effects or incomplete settlement in this panel.

The result validates a concrete join-order hypothesis for this authored CAN seed: enumerating the two high-cardinality `mt→Concept` membership relations before the sparse coactivation links creates many candidates that are later rejected. Starting from the coactivation links cuts candidate and Term work by 27–66× and reduces uninstrumented closure time by 3.5–4.1× across the tested cells. The remaining gap between count and time ratios reflects other rules and runtime costs. This is a benchmark variant, not a production seed change or a general rule optimizer.

## Limits and next gate

The result covers one seed, path/banded-2 topologies, N=128/256, and two replicates per cell. It does not establish confluence under arbitrary clause reorderings, transfer to other rule families, natural workload frequency, or a universal matcher improvement. Before adopting any production rule change, repeat on held-out CAN draws and a second authored rule family, retain full graph parity and all fixed-point controls, and measure instrumentation-off costs in fresh workers. Broader natural graph/frame-discovery measurement remains open.

## Reproducibility

- [Preregistration](CAN_RUNTIME_MATCH_ORDER_SENSITIVITY_V1_PREREG_20260929.md)
- [Runner](../../../evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1.py)
- [Input lock](../../../evaluation/substrate_capability/can_runtime_match_order_sensitivity_v1_lock_20260929.json)
- [Raw capture](../../../evaluation/reports/can_runtime_match_order_sensitivity_v1_20260929.json)
- Baseline closure attribution source and capture: [runner](../../../evaluation/substrate_capability/can_runtime_closure_attribution_v1.py), [raw](../../../evaluation/reports/can_runtime_closure_attribution_v1_20260929.json), [lock](../../../evaluation/substrate_capability/can_runtime_closure_attribution_v1_lock_20260929.json)
