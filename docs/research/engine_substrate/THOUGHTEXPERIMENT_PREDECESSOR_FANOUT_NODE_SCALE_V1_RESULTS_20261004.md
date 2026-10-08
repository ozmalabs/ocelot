# Thoughtexperiment predecessor fanout node scale v1 — results

Date: 2026-10-04

## Result

The source-locked sweep completed 18/18 workers and passed all fourteen
independent checks. It covers 10,511, 100,511, and 200,511 graph nodes (the
noise nodes plus a fixed 511-node task substrate), a fixed 467-edge structure,
four independent-state frames, four candidate branches, both snapshot
backends, and three fresh workers per cell. Every worker selects only the
correct supplied candidate, matches the direct monolithic oracle, preserves
primary isolation and active rules, rejects stale residual retries, and
reaches scoped closure quiescence.

At 100k→200k nodes, median graph-export time grows 1.95×/1.96× and canonical
digest time 1.97×/2.00× for full-copy/shared pages. Median lifecycle grows
1.95×/1.98×. From 10k→100k, lifecycle grows 7.95×/8.35×, graph export 9.21×/
9.82×, and digest 7.57×/8.41×. These ratios are consistent with roughly
proportional cost over these points, but three workers per cell and one
synthetic topology do not establish a complexity law.

At 200k nodes, median baseline PSS is about 334 MiB. Peak RSS after branch drop
is 881 MiB (full-copy) and 740 MiB (shared pages). While candidate branches
are retained, allocator in-use bytes rise by 148.0 MiB for full-copy versus
6.51 MiB for shared pages; after branches are dropped, allocator in-use returns
to within 0.23 MiB of baseline for both. This is glibc `mallinfo2` allocator
accounting and process RSS from one host. It does not measure concurrent
experiments or system-wide memory pressure.

Candidate-fork medians at 200k nodes are 159.7 ms (full-copy) and 0.907 ms
(shared pages), while complete lifecycle medians are 7.38 s and 7.13 s. The
fork difference is large, but graph export/digest dominate lifecycle; shared
pages improve total lifecycle by only about 3% in this small sample. Prior
instrumentation on/off intervals remain broad, so export/digest values are
reported without correction.

## Claim boundary

This measures isolated unrelated-node growth with fixed sparse edges, not
natural task graphs, edge-density/topology growth, candidate generation,
concurrent fanout, or a general scaling law. Three workers per cell on one host
make timing and memory medians descriptive.

## Artifacts

- [Protocol](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_NODE_SCALE_V1_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1.py)
- [Initial analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_node_scale_v1.py)
- [Amended analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_node_scale_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_node_scale_v1_lock_20261004.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_20261004.json)
- [Amended analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_node_scale_v1_1_analysis_20261004.json)
