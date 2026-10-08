# Shape-decoding Thoughtexperiment topology v1 — results

**Result:** 10/10 gates pass across 60 fresh processes. Both positive and negative candidates retain their expected outcomes across five topologies, two backends, and sequential/concurrent modes. Cross-backend/mode signatures, primary isolation, stable graph counts, and source/native provenance all pass.

All rows use 100k noise nodes; path/star have 100,743 total edges, grid/random4 about 200k, and observation spokes 100,744. The spoke graph connects each of the three focus observations to roughly one-third of the noise nodes, so its focus boundary is O(n) while its edge count remains almost identical to the path.

| Noise topology | Edges | Full-copy seq / concurrent positive wave (ms) | Full-copy concurrent CPU/wall | Shared-page seq / concurrent positive wave (ms) | Shared-page concurrent CPU/wall |
|---|---:|---:|---:|---:|---:|
| Path | 100,743 | 1,456 / 861 | 2.62× | 311 / 394 | 1.10× |
| Star | 100,743 | 1,583 / 971 | 2.65× | 380 / 452 | 1.08× |
| Grid | 200,111 | 1,870 / 1,027 | 2.83× | 372 / 469 | 1.02× |
| Random degree≈4 | 200,741 | 1,935 / 1,053 | 2.78× | 353 / 468 | 1.08× |
| Observation spokes | 100,744 | 10,142 / 2,277 | 5.71× | 9,132 / 1,683 | 6.47× |

For the four disconnected topologies, backend/mode behavior remains close to the path baseline: full-copy concurrent waves are about 1.6–2.2× faster than sequential; shared-page concurrent waves are 16–31% slower. Edge count moving from ~100k to ~200k causes only modest cost growth in the shared-page fixture.

The observation-spoke condition changes the regime even though its edge count is essentially the same as path. Shared-page sequential latency rises about 29× (311→9,132 ms), while the concurrent wave takes 1,683 ms and aggregate worker CPU/wall reaches 6.47×. Full-copy sequential latency rises about 7×; concurrent takes 2,277 ms at 5.71× CPU/wall. Branch setup grows from ~1 ms to ~270–314 ms sequentially for shared pages, and model-after prediction rises from ~37–43 ms to ~801–854 ms. Thus a large aperture boundary drives cost strongly; concurrency recovers part of throughput after the native GIL-release changes, but not the lost absolute latency.

This directly supports the proposed locality condition: fixed node count and near-equal edge count do not predict cost when a frame aperture exposes a graph-proportional boundary. It also shows that branch concurrency and latency depend on the work induced by that boundary. The experiment uses an intentionally extreme synthetic spoke graph, not a natural-task boundary distribution or a treewidth proof. Follow up with intermediate boundary sizes (e.g. 1%, 10%, 50%, 100% of noise nodes) and realistic multi-frame interfaces, while measuring memory and branch-local graph size.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_TOPOLOGY_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_topology_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_topology_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_topology_v1_raw_20261001.json)
- [Node-count scale results](THOUGHTEXPERIMENT_SHAPE_DECODING_SCALE_V1_RESULTS_20261001.md)
