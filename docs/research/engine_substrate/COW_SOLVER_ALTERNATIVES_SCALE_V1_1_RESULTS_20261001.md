# Scaled solver-alternative reusable snapshot v1.1 results

Date: 2026-10-01

## Result

All **18 locked workers** completed with distinct process IDs and stable pre/post source/native fingerprints. The independent analyzer passes **8/8 gates** over 72 reusable-CoW/eager branch pairs. Every pair matches exactly on perturbation input, solver progress, final states, energy, frustration, coverage, and full branch graph digest. All 72 one-step terminal probes report zero progress. The primary graph, baseline state, read-only/later snapshot forks, and sibling alternatives remain unchanged.

Median costs by Concept count and topology (milliseconds):

| Concepts | Topology | Snapshot capture | CoW fork | Eager fork | CoW solver settle | Eager solver settle |
|---:|---|---:|---:|---:|---:|---:|
| 32 | path | 0.035 | 0.109 | 0.134 | 7.09 | 7.75 |
| 32 | banded2 | 0.042 | 0.123 | 0.132 | 8.44 | 6.21 |
| 128 | path | 0.066 | 0.665 | 0.647 | 458.99 | 475.58 |
| 128 | banded2 | 0.052 | 0.625 | 0.658 | 400.21 | 422.81 |
| 256 | path | 0.084 | 2.346 | 2.498 | 3,968.76 | 3,841.10 |
| 256 | banded2 | 0.116 | 2.341 | 2.241 | 3,851.32 | 3,751.64 |

## Interpretation

The reusable snapshot works as a solver-alternative consumer through 256 Concepts, and semantic parity holds for both topologies. Branch creation grows from about 0.1 ms to 2.3 ms; at 256 nodes CoW and eager fork costs are similar. Solver settle dominates branch creation by orders of magnitude and rises sharply between measured sizes, while CoW does not consistently speed the solve. These three synthetic sizes and one host do not establish an asymptotic law. The profile does identify native closure work as the next scale bottleneck to explain; the next measurement should pair candidate/match/queue work counters with N and topology before attributing growth to CoW or claiming tractability.

The first v1 orchestration attempt was interrupted before aggregate capture; it has no result evidence. V1.1 uses bounded three-process parallelism without changing the cells, has separate artifacts, and is the confirmatory capture. See [v1.1 preregistration](COW_SOLVER_ALTERNATIVES_SCALE_V1_1_PREREG_20261001.md), [runner](../../../evaluation/substrate_capability/cow_solver_alternatives_scale_v1_1.py), [analyzer](../../../scripts/analyze_cow_solver_alternatives_scale_v1_1.py), [lock](../../../evaluation/substrate_capability/cow_solver_alternatives_scale_v1_1_lock_20261001.json), [worker capture](../../../evaluation/reports/cow_solver_alternatives_scale_v1_1_workers_20261001.json), and [analysis](../../../evaluation/reports/cow_solver_alternatives_scale_v1_1_analysis_20261001.json).
