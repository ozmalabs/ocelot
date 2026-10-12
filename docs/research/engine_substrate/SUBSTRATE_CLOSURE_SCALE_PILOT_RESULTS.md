# Closure scaling pilot results

**Status:** exploratory size sweep on synthetic graph-authored closure rules; not confirmatory evidence and not a hardware-scale claim.

## Method

Each topology/size instance ran in an isolated worker using the current native PyO3 rule runner. We measured rule-run wall and CPU time, process peak RSS, candidate enumeration, leaf visits, output graph size, exact closure against the independent oracle, and a terminal probe. The workload applies two rules: link-link to reach and reach-link to reach. For each family, reach denotes pairs connected by a path of length at least two.

Raw sparse records: [path and banded-DAG JSON](../../../evaluation/reports/substrate_closure_scale_pilot_20260924.json). Raw dense-control records: [complete-DAG JSON](../../../evaluation/reports/substrate_closure_dense_scale_pilot_20260924.json). Small structural/counter results: [isolated pilot report](SUBSTRATE_CLOSURE_ISOLATED_PILOT_RESULTS.md).

## Results

| Topology | Nodes | Input links | Output edges | Candidate pairs | Leaf visits | AddEdge attempts | Rule wall time | Peak RSS (total / over post-import) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Path | 32 | 31 | 496 | 526 | 465 | 465 | 0.273 ms | 26.1 / 2.36 MB |
| Path | 64 | 63 | 2,016 | 2,078 | 1,953 | 1,953 | 0.967 ms | 25.6 / 2.16 MB |
| Path | 96 | 95 | 4,560 | 4,654 | 4,465 | 4,465 | 2.242 ms | 26.0 / 2.16 MB |
| Banded DAG | 32 | 61 | 526 | 1,105 | 957 | 957 | 0.360 ms | 25.6 / 2.16 MB |
| Banded DAG | 64 | 125 | 2,078 | 4,273 | 3,965 | 3,965 | 1.363 ms | 26.1 / 2.36 MB |
| Banded DAG | 96 | 189 | 4,654 | 9,489 | 9,021 | 9,021 | 3.111 ms | 26.3 / 2.56 MB |
| Complete DAG | 32 | 496 | 961 | 10,416 | 9,455 | 9,455 | 3.699 ms | 27.5 / 3.74 MB |
| Complete DAG | 64 | 2,016 | 3,969 | 85,344 | 81,375 | 81,375 | 31.614 ms | 40.2 / 16.99 MB |

All eight instances matched the closure oracle and reached the settled terminal probe. The bounded-width families reached n=96; the complete-DAG high-width control reached n=64. Candidate and leaf work is substantially larger on the dense control. In this workload, wall time broadly tracks candidate/leaf work and grows faster for the dense topology.

The path family has treewidth 1, but closure output itself grows quadratically. This is a useful qualification to the cheap-cut argument: bounded separator width can make local inference tractable, but it does not remove the cost of materializing a quadratic relation. Any theoretical bound for this rule engine must specify whether it measures input size, output size, or both.

## Resource interpretation and limits

Peak RSS is the isolated worker's process high-water mark. The harness now records its post-import high-water mark, post-setup mark, and post-primary-run mark. The table reports total peak and its increment over the post-import mark. Incremental peaks are about 2.2–2.8 MB on these path/banded cases, 3.8 MB at complete-DAG n=32, and 17.2 MB at complete-DAG n=64. This captures a dense candidate-enumeration memory spike, but a high-water delta is not live heap size, and the two dense sizes do not establish a memory-complexity estimate.

Rule-run timings exclude worker launch and graph construction, but include native call overhead. The small sizes and sub-millisecond sparse timings remain sensitive to timer resolution and runtime state. There are no repeated seeds, confidence intervals, alternate machine replications, workload baselines, or instrumentation-off comparison. Treat these as engineering diagnostics only.

The Python-boundary graph_writes counter remains zero, as expected for this native path. A new native AddEdge-attempt counter tracks attempted insertions, including duplicates; its values appear in the table. Candidate counter identities reconcile. Graph-state delta is the authoritative committed growth measure for these records.

## Next gate

1. Add an explicit resource baseline and repeated runs, then characterize variance and measurement overhead.
2. Extend mutation-attempt counters to native node, attribute, delete, and replacement effects; retain state deltas as committed-change evidence.
3. Expand rule families to duplicate/no-op, cycles, bounded fresh-node growth, and termination-cap cases.
4. Freeze a representative structural suite and preregister thresholds before any envelope claim beyond this synthetic closure workload.
