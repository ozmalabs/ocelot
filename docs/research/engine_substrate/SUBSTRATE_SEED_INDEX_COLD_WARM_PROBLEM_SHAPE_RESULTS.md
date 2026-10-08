# Seed-index cold/warm ProblemShape parity results

Date: 2026-09-25  
Status: locked exploratory workload comparison; all parity gates passed

## Result

Four fresh processes ran the current ProblemShape worker at N=32 on the immutable 833-manifest baseline snapshot: recognition with a cold and warm seed-index cache, and recurrent residual with a cold and warm cache. Each worker passed its task and fixed-point gates. The full declared task/work projection was identical within both cold/warm pairs, including seed-load order, rule order and positions, observation outcomes, mint counts, final codebook size, and per-observation operation counters. Cache bytes remained stable during warm workers, and all four workers used distinct PIDs.

| Workload | Cold / warm boot wall time | Cold / warm task-observation wall sum | Candidate pairs | Term evaluations | Mints |
|---|---:|---:|---:|---:|---:|
| Recognition | 28.21 / 24.10 s | 0.845 / 1.002 s | 3,696 / 3,696 | 21,616 / 21,616 | 0 / 0 |
| Recurrent residual | 28.99 / 27.09 s | 1.060 / 0.764 s | 3,707 / 3,707 | 22,135 / 22,135 | 1 / 1 |

The boot and observation times are single-run descriptive measurements for each arm. They show that seed loading dominates this measured N=32 task run, but are too few and too noisy to support a cache speedup or general timing claim. Warm loading still takes about 24–27 seconds here. Exact parity supports the repaired cache's order/state consistency for these two workloads; it does not establish parity for other order-sensitive applications.

## Protocol and claim boundary

The preregistration locks the current loader, task worker/helpers, domain sources, native extension/build record, and corpus. The earlier V1.7 runner rejected the repaired `boot_all.py` hash against its historic lock; this follow-up uses a new current-source lock. The V1.7 ordered manifest digest and the seed transformer's canonical sorted-path digest differ because they serialize the same manifest/hash rows in different orders; both were verified separately before the run. Raw records retain full worker details.

This is one frozen authored corpus, two N=32 workload mixes, and one cold/warm pair per mix. It measures a narrow application-level cache-parity question, not natural-task frame locality, broad reliability, asymptotic scaling, or rung 3/4 tractability. The substantial startup interval is an engineering-scale observation and should be decomposed by loader stage in a separate repeated benchmark.

## Artifacts

- Preregistration: [`protocol`](SUBSTRATE_SEED_INDEX_COLD_WARM_PROBLEM_SHAPE_PREREG_20260925.md)
- Source/corpus lock: [`lock JSON`](../../../evaluation/substrate_capability/seed_index_cold_warm_problem_shape_lock_20260925.json)
- Runner: [`probe`](../../../scripts/substrate_seed_index_cold_warm_problem_shape_probe_v1.py)
- Raw report: [`worker data`](../../../evaluation/reports/substrate_seed_index_cold_warm_problem_shape_v1_20260925.json)
- Cache repair: [`cold/warm repair results`](SUBSTRATE_SEED_INDEX_CACHE_ORDER_FIX_V2_RESULTS.md)
