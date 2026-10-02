# Native work attribution for scaled solver alternatives v1.2 results

Date: 2026-10-01

## Result

The instrumented 18-worker panel passes **11/11 checks** across 72 solver branches (CoW and eager for each of four alternatives per worker). Source/native inputs remain stable. Candidate counts are nonzero, and per-rule candidate-test totals reconcile exactly to global `cand_tested` in all **144** branches. CoW and eager arms execute identical candidate and term work on every matched input. Instrumented counters are reported separately from the uninstrumented v1.1 timings because per-rule audit adds work.

Medians across the 12 branches per size/topology/backend (CoW and eager values are identical):

| Concepts | Topology | Candidate tests | Term evaluations | Term units | Rule enumerations | Where evaluations | Candidate scan tests | Local bucket tests |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 32 | path | 17,923 | 137,514 | 32,157 | 12 | 5,152 | 128 | 17,795 |
| 32 | banded2 | 17,060 | 138,333 | 36,958 | 12.5 | 5,188 | 128 | 16,932 |
| 128 | path | 1,098,945 | 7,281,717 | 1,989,200 | 13 | 83,496 | 512 | 1,098,433 |
| 128 | banded2 | 1,056,140 | 7,074,074 | 1,990,771 | 12.5 | 82,552 | 512 | 1,055,628 |
| 256 | path | 8,721,255 | 56,474,170 | 15,877,107.5 | 14 | 334,038 | 1,024 | 8,720,231 |
| 256 | banded2 | 8,546,102 | 55,621,200 | 15,865,332 | 13 | 332,120 | 1,024 | 8,545,078 |

Local-bucket enumeration accounts for 99.3%–99.99% of candidate tests across these cells, rising to about 99.99% at N=256. The candidate scan count is exactly 4N in every reported cell. Rule enumeration counts remain between 12 and 14 while candidate and Term work grow sharply. Global `scheduler_passes` remains zero because this consumer calls the scoped CAN closure API; the scoped match-source counters are recorded separately. No `deferred_queue:*` counters were emitted for these CAN solver branches.

## Interpretation

Candidate tests increase approximately 62× when N increases 4× (32→128), then approximately 8× when N doubles (128→256), in both path and banded2. That is consistent with cubic work over these three measured sizes, but three synthetic points do not establish a complexity bound. Term evaluations track a similar steep rise. The two Hebbian rules dominate per-rule candidate tests: at N=256, `can_native_hebbian_reweight` contributes about 68.5M over the 12 path alternatives and `can_native_hebbian_mint` about 34.8M; the other measured rules are much smaller. Source inspection shows these rules join two `Microtheory-has_concept` relations and coactivation links, with the coactivation-noting rule minting graph objects. This is a plausible mechanism for the work growth, not a proven causal decomposition.

This changes the next engineering question: optimize or bound match work in the repeated Hebbian joins before pursuing further CoW changes for this workload. Because local-bucket enumeration already accounts for nearly all candidate tests, the most direct follow-up is to vary coactivation population and join order under exact semantic controls, then test a rule-local index/pushdown strategy against eager baseline results. These results concern one native CAN fixture, not general closure complexity.

V1.2 operation counts pair with the uninstrumented timing reference in [v1.1 results](COW_SOLVER_ALTERNATIVES_SCALE_V1_1_RESULTS_20261001.md). See [v1.2 preregistration](COW_SOLVER_ALTERNATIVES_SCALE_V1_2_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/cow_solver_alternatives_scale_v1_2.py), [analyzer](../../../scripts/analyze_cow_solver_alternatives_scale_v1_2.py), [lock](../../../evaluation/substrate_capability/cow_solver_alternatives_scale_v1_2_lock_20261001.json), [worker capture](../../../evaluation/reports/cow_solver_alternatives_scale_v1_2_workers_20261001.json), and [analysis](../../../evaluation/reports/cow_solver_alternatives_scale_v1_2_analysis_20261001.json).
