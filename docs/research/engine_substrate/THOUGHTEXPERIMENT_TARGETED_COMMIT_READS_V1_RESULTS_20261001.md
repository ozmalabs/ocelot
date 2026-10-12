# Thoughtexperiment targeted commit reads v1 — results

**Date:** 2026-10-01  
**Status:** all semantic, isolation, authorization, oracle, and tombstone-ID gates pass.

Three fresh workers replayed 72 cases from the four-family × two-size × three-seed generated-residual panel. Each case compares legacy full-graph reads with targeted native reads on isolated branches from the same rehearsed state. Mode order is counterbalanced by family, size, and seed. Both branches are checked against the full semantic graph oracle, and each is given a trailing deleted high-ID node after the commit gate mints its audit record. All added-node cases allocate the same expected `max live NodeID + 1`; both legacy and targeted paths pass.

## Paired commit latency

The table reports nine-pair medians from the uninstrumented timing arm. A small wrapper creates the trailing tombstone after the gate; it runs identically in both arms. The detailed subphase arm separately wraps Python/native calls and is diagnostic only.

| Family / nodes | Legacy full-graph reads (ms) | Targeted native reads (ms) | Median ratio | Targeted wins |
|---|---:|---:|---:|---:|
| attribute / 64 | 5.42 | 4.79 | 1.13× | 6/9 |
| attribute / 1,000 | 24.33 | 4.48 | 5.44× | 9/9 |
| add / 64 | 6.69 | 5.61 | 1.19× | 5/9 |
| add / 1,000 | 22.75 | 4.73 | 4.81× | 9/9 |
| mixed / 64 | 7.16 | 4.62 | 1.55× | 8/9 |
| mixed / 1,000 | 26.12 | 5.72 | 4.57× | 9/9 |
| hub delete / 64 | 6.48 | 5.85 | 1.11× | 6/9 |
| hub delete / 1,000 | 8.35 | 5.97 | 1.40× | 8/9 |

At 1,000 nodes, attribute/add/mixed cells show 4.57–5.44× lower median commit time, with all nine paired comparisons favoring targeted reads in each cell. Hub deletion is 1.40× faster because its fixture has far fewer background edges. At 64 nodes, the gains are smaller and paired wins are mixed. The diagnostic arm records zero `graph_to_dict()` calls in the targeted commit path; the legacy snapshot takes 2.8–15.2 ms at 1,000 nodes and 0.6–0.9 ms at 64 nodes. These comparisons identify whole-graph conversion as a real cost in this fixture and show that the targeted implementation removes it without changing receipt semantics.

After making targeted reads the default, the existing five-worker deletion-commit adversarial probe also passes all 20 checks in each worker: stale edge/node before-images reject without partial writeback, corrupted late before-images fail atomically, and a writer injected at native transaction entry is preserved while the proposed batch is rejected. See [deletion-commit results](THOUGHTEXPERIMENT_DELETION_COMMIT_V1_RESULTS_20261001.md) and the [raw capture](../../../evaluation/reports/thoughtexperiment_deletion_commit_v1.json).

The result is limited to one host, nine pairs per cell, and synthetic fixtures whose edge population varies with family. The native next-live-ID method scans live node slots, so it is not constant-time. Do not infer an asymptotic bound or universal speedup. The next gate should independently cross node count, background-edge density, and aperture degree, add randomized tombstones/holes and stale-writer conflicts, and retain an uninstrumented baseline plus exact full-graph oracle. Manifold-assessment cost remains, particularly in small graphs.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_TARGETED_COMMIT_READS_V1_PREREG_20261001.md)
- [Commit phase protocol](THOUGHTEXPERIMENT_COMMIT_PHASE_PROFILE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_commit_phase_profile_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_commit_phase_profile_v1.json)
