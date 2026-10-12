# Thoughtexperiment full reground scale v1 — results

**Date:** 2026-10-01  
**Status:** source-locked synthetic scale probe; three workers and all survivor oracles pass.

Complete `reground()` timings include conclusion checks, incident-edge reads, and durable conclusion/imagination status writes. Graph construction and exact before-image receipt creation are outside the timed region. Every proposal correctly survives in all repeats.

| Nodes | Topology | Deletions | Validated incident edges | Median of worker medians | Highest worker median (3-worker p95 proxy) |
|---:|---|---:|---:|---:|---:|
| 1,000 | chain | 1 | 2 | 0.072 ms | 0.097 ms |
| 10,000 | chain | 16 | 32 | 0.766 ms | 0.770 ms |
| 50,000 | chain | 128 | 256 | 6.193 ms | 7.969 ms |
| 10,000 | star, delete hub | 1 | 9,999 | 42.575 ms | 43.853 ms |
| 50,000 | star, delete hub | 1 | 49,999 | 267.783 ms | 269.992 ms |
| 50,000 | star, delete 128 leaves | 128 | 128 | 5.535 ms | 5.731 ms |

These cells show that total node count alone is not a useful predictor for this path: the 50k-node, 128-leaf case completes near the 50k chain/128 case despite different total edge count, while deleting a 50k-degree hub takes about 268 ms because its full incident-edge before-image must be verified. The chain deletion panel rises from 0.072 ms for one conclusion at 1k nodes to 6.193 ms for 128 conclusions at 50k; node count and conclusion count change together there, so this is not a causal slope estimate. The local incident-edge microprobe separately measured far lower cost than full graph serialization at the same large graph sizes.

Scope is limited to three fresh workers, a chain and a star, and survivor-only proposals. The p95 label is the maximum of three worker medians, not a stable tail estimate. No changed-node conflicts, mixed conclusions, concurrent writes, snapshot costs, rule closure, or natural-task topology are represented. Next cross deletion count with graph size while holding degree/topology fixed, add mixed survivor/conflict cases and a randomized graph oracle, and compare full reground against a monolithic independent implementation.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_FULL_REGROUND_SCALE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_full_reground_scale_v1.py)
- [Raw three-worker capture](../../../evaluation/reports/thoughtexperiment_full_reground_scale_v1.json)
