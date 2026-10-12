# Coactivation population × Hebbian join order v1 results

Date: 2026-10-01  
Status: complete; all 8 analysis gates pass.

## Result

The source-locked panel ran 45 fresh workers: N={32,64,128}, five directed coactivation populations per size, and three replicates per cell. Each worker compared the authored matcher order with the sparse-first order for the two production Hebbian rules. Only those two rules were active, and the epoch guards made the run read-only.

Across all 90 arms, progress and terminal progress were zero, graph state stayed unchanged, baseline and sparse-first graph digests matched, the installed match orders had the expected first clause, and per-rule candidate counts reconciled with the global counter. Worker inputs matched the source lock before and after capture.

| N | Q | Baseline candidate tests | Sparse-first candidate tests | Reduction |
|---:|---:|---:|---:|---:|
| 32 | 0 | 2,112 | 0 | 100.00% |
| 32 | 32 | 4,128 | 192 | 95.35% |
| 32 | 128 | 10,176 | 768 | 92.45% |
| 32 | 248 | 17,736 | 1,488 | 91.61% |
| 32 | 992 | 64,608 | 5,952 | 90.79% |
| 64 | 0 | 8,320 | 0 | 100.00% |
| 64 | 64 | 16,448 | 384 | 97.67% |
| 64 | 256 | 40,832 | 1,536 | 96.24% |
| 64 | 1,008 | 136,336 | 6,048 | 95.56% |
| 64 | 4,032 | 520,384 | 24,192 | 95.35% |
| 128 | 0 | 33,024 | 0 | 100.00% |
| 128 | 128 | 65,664 | 768 | 98.83% |
| 128 | 512 | 163,584 | 3,072 | 98.12% |
| 128 | 4,064 | 1,069,344 | 24,384 | 97.72% |
| 128 | 16,256 | 4,178,304 | 97,536 | 97.67% |

The data separate two costs. Baseline traversal performs substantial work even when Q=0 because the two `has_concept` clauses create a broad pair search. Sparse-first starts from coactivation edges and reduces candidate enumeration by 90.79–100% across the panel. At fixed Q/N ratios, both orderings grow with N; for example at Q=4N, baseline candidate tests rise from 10,176 (N=32) to 163,584 (N=128), while sparse-first rises from 768 to 3,072. These are finite synthetic measurements, not an asymptotic proof. They show that the authored join order is a major work multiplier and that measured work depends on both N and relation population Q.

## Scope and limitations

The graph contains uniformly distributed directed cyclic-offset pairs. This isolates matcher work for two rules; it does not measure productive closure, learned or natural coactivation distributions, total wall time, memory, arbitrary rules, or task-level capability. The result supports measuring Q and actual installed join order in future closure profiles. It does not imply that sparse-first is universally best; selectivity changes with relation density, and the engine's install-time ordering policy should be evaluated against the workload distribution.

The first capture attempt failed only because the analyzer's graph digest included rule metadata, whose order intentionally differs between arms. The corrected runner hashes graph state alone; a new lock and full 45-worker capture were produced. The failed preliminary data were not used in the result.

## Reproduction and artifacts

- Preregistration: [population × join-order protocol](CAN_COACTIVATION_POPULATION_JOIN_ORDER_V1_PREREG_20261001.md)
- Runner: [capture script](../../../evaluation/substrate_capability/can_coactivation_population_join_order_v1.py)
- Analyzer: [independent gate and summary script](../../../scripts/analyze_can_coactivation_population_join_order_v1.py)
- Lock: [source/input lock](../../../evaluation/substrate_capability/can_coactivation_population_join_order_v1_lock_20261001.json)
- Raw data: [45 worker records](../../../evaluation/reports/can_coactivation_population_join_order_v1_workers_20261001.json)
- Summary: [analysis output](../../../evaluation/reports/can_coactivation_population_join_order_v1_analysis_20261001.json)

Run `python3 evaluation/substrate_capability/can_coactivation_population_join_order_v1.py` to check the lock, execute the panel, and invoke the analyzer.
