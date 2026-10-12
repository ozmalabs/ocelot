# Thoughtexperiment predecessor fanout edge-topology v1.1 results

## Result

All 24 current-source workers completed, and the independent analyzer passed
all 19 checks: exact schedule and graph size, one correct candidate, exact
monolithic oracle parity, primary isolation, rule preservation, stale-retry
refusal, scoped quiescence, five graph exports/digests, timer conservation,
source stability, and three replicates in each cell. Each graph contains
100,511 nodes and 100,466 edges: the fixed 511-node/467-edge task plus 100,000
unrelated nodes and 99,999 background edges.

| Background layout | Full-copy lifecycle | Shared-page lifecycle | Full-copy export / digest | Shared-page export / digest |
|---|---:|---:|---:|---:|
| Path | 8.10 s | 7.99 s | 4.31 / 3.26 s | 4.29 / 3.45 s |
| Star | 8.15 s | 7.22 s | 4.18 / 3.42 s | 3.96 / 3.11 s |
| Cluster star | 7.95 s | 7.76 s | 4.25 / 3.32 s | 4.28 / 3.32 s |
| Random recursive tree | 7.85 s | 7.78 s | 4.11 / 3.31 s | 4.05 / 3.45 s |

Against the 100k-node, 467-edge sparse-background reference, lifecycle medians
are 2.00–2.22× higher, exports 1.46–1.58× higher, and digests 3.99–4.52× higher.
Full-copy candidate-fork medians are 111–119 ms; shared-page medians are
0.91–2.54 ms. Despite that fork difference, lifecycle medians remain close
because export/digest work dominates. Added topology construction for both the
primary and oracle graphs takes 0.57–0.84 s per worker, separately from the
measured lifecycle. Retained allocator deltas are 117–127 MiB full-copy and
6.5–15.3 MiB shared-page.

No stable topology ordering follows from three workers per cell. This study
shows the cost of serializing and auditing a graph with a fixed number of
unrelated edges across four degree layouts. The added edges are outside the
task frames and rule closure, so the result says nothing about learned frame
locality, natural topology prevalence, connected task performance, concurrency,
or asymptotic complexity. Instrumentation timing uncertainty remains as
reported in the prior eight-pair on/off control.

## Reproduction artifacts

- [Original preregistration](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_EDGE_TOPOLOGY_V1_PREREG_20261004.md)
- [v1.1 amendment](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_EDGE_TOPOLOGY_V1_1_AMENDMENT_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_1.py)
- [Original preregistered analyzer (failed on JSON key type)](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_edge_topology_v1_1.py)
- [Corrected independent analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_edge_topology_v1_1_1.py)
- [Analysis amendment](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_EDGE_TOPOLOGY_ANALYSIS_AMENDMENT_20261004.md)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_20261004.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_1_analysis_20261004.json)
- [Failed v1 fixture capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_edge_topology_v1_20261004.json), retained to disclose the fixture API error
