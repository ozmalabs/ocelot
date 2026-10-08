# Thoughtexperiment recurrence repair memory across graph topologies v1 — results

**Result:** 6/6 preregistered gates pass across the confirmatory 36-process run (three per topology/size/backend cell). Every branch restored the authored rule, emitted one offer, reached a zero-progress fixed point, and preserved the primary graph, rules, and revision. All topologies have the same node count, edge count, and node payload; full-copy and shared-page branches had matching outcomes. The initial run is retained as a diagnostic only; see the [confirmation amendment](THOUGHTEXPERIMENT_RECURRENCE_TOPOLOGY_MEMORY_V1_AMENDMENT_20261001.md).

## Median sampled peak increase over process baseline

MiB from Linux `smaps_rollup`, sampled every 10 ms:

| Nodes | Topology | Backend | ΔPSS | ΔRSS | ΔPrivate Dirty |
|---:|---|---|---:|---:|---:|
| 100,000 | path | native eager full copy | 32.12 | 32.12 | 31.30 |
| 100,000 | path | native shared graph pages | 2.70 | 2.70 | 1.89 |
| 100,000 | star | native eager full copy | 30.12 | 30.12 | 29.30 |
| 100,000 | star | native shared graph pages | 3.82 | 3.82 | 3.01 |
| 100,000 | balanced tree | native eager full copy | 30.05 | 30.05 | 29.24 |
| 100,000 | balanced tree | native shared graph pages | 2.50 | 2.50 | 1.68 |
| 200,000 | path | native eager full copy | 62.95 | 62.95 | 62.14 |
| 200,000 | path | native shared graph pages | 4.05 | 4.05 | 3.24 |
| 200,000 | star | native eager full copy | 58.93 | 58.93 | 58.12 |
| 200,000 | star | native shared graph pages | 6.30 | 6.30 | 5.48 |
| 200,000 | balanced tree | native eager full copy | 58.82 | 58.82 | 58.01 |
| 200,000 | balanced tree | native shared graph pages | 3.66 | 3.66 | 2.84 |

Shared graph pages reduced median incremental PSS in all six topology/size comparisons. At 200k nodes, full-copy/shared-page deltas were 62.95/4.05 MiB (path), 58.93/6.30 MiB (star), and 58.82/3.66 MiB (balanced tree). The star used about 1.7× the shared-page peak PSS of the balanced tree at 200k, despite matched graph counts. This suggests adjacency layout can affect branch memory for this fixture; three repeats per cell do not estimate variability precisely.

The sampler recorded only 3–5 observations per run, so short peaks may be missed. Results are from one host and one task-shaped correction on synthetic noise graphs. They do not establish natural topology prevalence, concurrent serving throughput, or autonomous correction capability.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_TOPOLOGY_MEMORY_V1_PREREG_20261001.md)
- [Confirmation amendment](THOUGHTEXPERIMENT_RECURRENCE_TOPOLOGY_MEMORY_V1_AMENDMENT_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_topology_memory_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_topology_memory_v1.py)
- [Raw confirmatory capture](../../../evaluation/reports/thoughtexperiment_recurrence_topology_memory_v1_raw_20261001.json)
- [Excluded initial diagnostic](../../../evaluation/reports/thoughtexperiment_recurrence_topology_memory_v1_initial_diagnostic_20261001.json)
