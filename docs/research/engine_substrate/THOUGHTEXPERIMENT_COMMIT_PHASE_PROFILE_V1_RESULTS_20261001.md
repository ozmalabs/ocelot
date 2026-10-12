# Thoughtexperiment commit phase profile v1 — results

**Date:** 2026-10-01  
**Status:** all 72 paired trials pass semantic, isolation, authorization, oracle, and ID-allocation gates.

Three fresh workers compare legacy full-graph reads against the targeted native-read path for four rule families, two graph sizes, and three seeds. Counterbalanced order controls warm-cache bias. Each arm starts from an isolated copy of the same rehearsed state and includes a trailing tombstone inserted after the gate record is minted. Both paths produce the same full semantic graph and preserve the `max live NodeID + 1` allocation policy. A separate paired arm measures full commit without per-call timing wrappers; only a tiny symmetric gate wrapper inserts the tombstone.

## What the instrumentation identifies

For legacy commits, `graph_to_dict()` is called once per commit. Its median cost ranges from 0.62–0.88 ms at 64 nodes and 2.79–15.19 ms at 1,000 nodes, depending on fixture edge population. The targeted route calls it zero times during commit. Staged delta application costs approximately 0.19–0.60 ms in the 64/1,000-node treatments. Information-manifold assessment costs approximately 4.0–6.1 ms on this rebuilt engine across the cells. `set_attr` totals and before-image checks are small in comparison.

Detailed timings are nested and include instrumentation overhead, so they are localization evidence rather than an additive partition. The uninstrumented paired latency comparison and per-cell wins are reported in the [targeted-read result](THOUGHTEXPERIMENT_TARGETED_COMMIT_READS_V1_RESULTS_20261001.md). That comparison shows the effect of removing full graph materialization while holding rule, graph, and receipt constant.

This capture identifies a graph-serialization cost and verifies its removal for this implementation path. It does not establish an asymptotic law: node count and edge population are confounded in the current synthetic families, and next-live-ID lookup scans node slots. Manifold assessment remains a distinct cost, especially on smaller graphs.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_COMMIT_PHASE_PROFILE_V1_PREREG_20261001.md)
- [Targeted-read protocol](THOUGHTEXPERIMENT_TARGETED_COMMIT_READS_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_commit_phase_profile_v1.py)
- [Raw paired capture](../../../evaluation/reports/thoughtexperiment_commit_phase_profile_v1.json)
