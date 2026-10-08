# Predecessor fanout at 100,000 nodes: exploratory checkpoint

This exploratory extension runs the existing predecessor-dependent fanout
worker at 100,000 unrelated noise nodes. It uses four independent discourse
frames, four candidate branches, the chained closure/selection/residual/return
path, and three fresh processes per backend (`full_copy` and
`shared_graph_pages`). It was not preregistered and has no pre-capture source
lock; treat the timing and memory values as directional evidence, not a
confirmatory result.

All six rows selected the one correct supplied candidate. Every candidate
closure reached quiescence. The selected branch and returned primary matched
the independent monolithic graph oracle, primary state stayed isolated before
return, and stale residuals were rejected without mutation. Each process
contained 100,511 nodes and 467 edges.

| Metric (three-run median) | Full copy | Shared graph pages |
|---|---:|---:|
| Snapshot creation | 13.69 ms | 0.23 ms |
| Four candidate forks | 53.49 ms | 0.43 ms |
| Complete recorded lifecycle | 2,516.96 ms | 2,369.05 ms |
| Retained allocator in-use growth | 75.79 MiB | 4.61 MiB |
| Allocator in-use growth after drop | -0.11 MiB | -0.10 MiB |
| Sampled peak RSS above baseline | 268.52 MiB | 197.95 MiB |

The branch fork and retained-allocation advantages survive at this graph size,
while complete lifecycle time improves by only about 1.06x. The harness's
whole-graph canonical hashing and audit work dominate the measured lifecycle;
this run does not show a comparable end-to-end speedup. Allocator counters are
glibc-specific and sampled peak RSS is process-wide.

The raw rows and independent integrity summary are [capture](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_20261003.json),
[analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_100k_exploratory_20261003.py),
and [analysis](../../../evaluation/reports/thoughtexperiment_predecessor_fanout_100k_exploratory_analysis_20261003.json).
The analyzer passes all eight row, semantic, isolation, and relative-cost
checks. The next confirmatory gate should preregister repeated 100k/1m graph
sizes and multiple frame/fanout topologies, lock all code/build inputs before
capture, and report both instrumented and minimally instrumented end-to-end
costs so whole-graph audit overhead is not confused with branch execution.
