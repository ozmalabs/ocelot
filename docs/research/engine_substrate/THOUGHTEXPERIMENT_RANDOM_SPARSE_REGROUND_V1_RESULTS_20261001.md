# Thoughtexperiment randomized sparse reground v1 — results

**Date:** 2026-10-01  
**Status:** source-locked randomized-model probe; all gates pass.

Five fresh workers each run two independent seeds at 1k, 10k, and 50k nodes. Every graph contains `2N` seeded directed sparse edges and 50 independently selected, non-adjacent deletion targets. Each target is assigned one of five balanced treatments: clean, node-attribute edit, incident-edge attribute edit, incident-edge addition, or incident-edge removal. The exact source fact model is updated alongside native graph mutations and computes expected reground outcomes independently of the native incident-edge accessor.

| Nodes | Seeded graph cells | Median full reground (50 proposals) | Max observed | Oracle parity |
|---:|---:|---:|---:|---|
| 1,000 | 10 | 3.528 ms | 6.582 ms | all pass |
| 10,000 | 10 | 4.096 ms | 5.908 ms | all pass |
| 50,000 | 10 | 5.569 ms | 7.829 ms | all pass |

Across each size, 100 clean proposals survive and all 400 injected conflicts are rejected: 100 each for node-attribute, edge-attribute, edge-addition, and edge-removal conflict modes. The complete model-derived per-conclusion verdict map matches `reground()` in all 30 worker/seed/size graphs. All five process IDs are distinct and the native build/source locks match.

This validates the regrounder's exact judgments on a small seeded sparse graph model with isolated conflict modes. The selected targets are a randomized independent set conditioned on nonzero degree, and this generator is not a natural-task sample. The timing increase with graph size could reflect storage/cache effects or runtime noise; do not interpret six seeded graph cells per worker as a scaling law. Next vary degree distributions and target counts, add randomized mixed node/edge receipts with an independent full-delta application oracle, then validate against naturally generated task receipts.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RANDOM_SPARSE_REGROUND_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_random_sparse_reground_v1.py)
- [Raw five-worker capture](../../../evaluation/reports/thoughtexperiment_random_sparse_reground_v1.json)
