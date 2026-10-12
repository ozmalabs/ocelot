# Predecessor-dependent thought-experiment fanout v1.1 results

Date: 2026-10-03

## Result

The source-locked 216-cell panel completed successfully: 1/4/8 frames,
chained/independent state layouts, 1/4/16 candidate branches, 0/10,000 noise
nodes, full-copy/shared-graph-pages backends, and three fresh worker processes
per cell. The runner's 12 checks and the independent analyzer's 14 checks all
pass. Exactly the correct supplied head grounds, every decoy abstains, all
scoped sweeps reach quiescence, and the selected branch and returned primary
match the monolithic oracle's canonical graph. Primary isolation before return,
rule-store preservation, and atomic stale-revision rejection also hold in all
cells.

This establishes an outcome-guided candidate adjudication and residual-return
path over an evaluator-authored candidate set. It does not measure candidate
generation, frame discovery, natural-task frequencies, open-ended concept
invention, or autonomous self-improvement.

## Cost and memory

At eight frames and 10,000 noise nodes, median full lifecycle time for K=16 is
311 ms with full-copy and 269 ms with shared graph pages. At K=1 the medians
are 242 and 240 ms respectively. These are total costs for snapshot creation,
K forks, edits, K scoped closures, residual extraction/readout, and selected
return. The independent monolithic oracle is about 0.5 ms; it performs one
closure, not K-way exploration, so the values are not a speed comparison.

`mallinfo2` in-use bytes rise with retained branches and return to approximately
baseline after branch references are dropped. At eight frames, 10,000 noise
nodes, K=16, median in-use deltas are +37.1 MiB for full-copy and +10.1 MiB for
shared graph pages while branches are retained, then approximately zero after
drop. Post-drop PSS remains above baseline by 39.5 MiB and 12.2 MiB respectively;
the allocator has released live allocations while the process retains resident
pages. This is why the v1 PSS-only post-drop field was withdrawn. The v1.1
allocator observation is glibc-specific and does not measure total system
memory, fragmentation outside `mallinfo2`, or long-lived concurrent workloads.

Shared graph pages reduce retained allocator growth at high fanout in this
matrix, but lifecycle speed is mixed and still grows with candidate count and
noise graph size. The largest measured graph has 10,539 nodes and 535 edges;
this does not establish million-node fanout performance. Three replicates per
cell and one host support controlled mechanism evidence, not a general scaling
law.

## Reproducible artifacts

- Protocol and measurement amendment: [v1 protocol](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_V1_PROTOCOL_20261003.md), [v1.1 amendment](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_V1_1_AMENDMENT_20261003.md)
- Runner and independent analyzer: [runner](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_v1_1.py), [analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_v1_1.py)
- Source lock and raw/derived records: [lock](../../../evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_v1_1_lock_20261003.json), [capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_v1_1_20261003.json), [analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_v1_1_analysis_20261003.json)

## Next gate

Measure this complete path on independently authored task families with
outcome-blind candidate construction and task-level held-out correctness. Add
larger graph sizes and repeated/concurrent branches with explicit memory caps.
Only after those gates pass should the programme evaluate substrate-generated
candidates and incremental benefit over an LLM-designed baseline.
