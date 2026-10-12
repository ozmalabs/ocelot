# Shape-decoding aperture-boundary v1 — results

**Result:** 11/11 gates pass across 60 fresh processes. The node and edge counts are held exactly constant across all boundary fractions (100,771 nodes, 100,743 edges); realized spoke counts match 0%, 1%, 10%, 50%, and 99%. Positive and negative task oracles, cross-backend/mode semantic parity, primary isolation, and source/native provenance all pass.

| Boundary fraction | Full-copy positive seq / concurrent (ms) | Full-copy concurrent CPU/wall | Shared-page positive seq / concurrent (ms) | Shared-page concurrent CPU/wall |
|---:|---:|---:|---:|---:|
| 0% | 1,552 / 717 | 2.59× | 305 / 407 | 1.07× |
| 1% | 1,453 / 781 | 2.72× | 321 / 316 | 1.16× |
| 10% | 1,583 / 823 | 2.89× | 505 / 415 | 1.65× |
| 50% | 3,222 / 1,038 | 3.78× | 2,037 / 605 | 4.06× |
| 99% | 7,056 / 1,632 | 5.11× | 5,851 / 1,154 | 5.81× |

The negative candidate has the same trend: shared-page sequential/concurrent waves are 313/400 ms at 0%, 476/394 ms at 10%, 1,959/587 ms at 50%, and 5,642/1,208 ms at 99%. At low exposure, concurrent shared-page work is neutral or slower; at 50–99% exposure, it is 3.3–5.1× faster than sequential. Full-copy also becomes more expensive with boundary fraction and gets stronger concurrent gains.

For shared-page positives, sequential branch-setup phase rises from 1 ms at 0% to 7/59/183 ms at 10/50/99%; model-after prediction rises from 33 ms to 51/184/519 ms. Thus the latency response grows markedly as more edges cross the aperture at fixed node/edge count. Concurrent CPU/wall rises in parallel from 1.07× at 0% to 5.81× at 99%, showing that the GIL-released native branch work can use multiple CPUs when the aperture workload is large enough.

This provides stronger evidence for the cheap-cut hypothesis than the all-or-none spoke stress test: cost follows exposed boundary fraction under a matched node/edge budget, and backend concurrency changes with the induced work. The protocol replaces path edges with observation spokes, so it also fragments the original path as the boundary increases. It remains an authored synthetic shape task, not a natural boundary distribution, general treewidth result, or asymptotic proof. Next test nested multi-frame boundaries and additional task families, with memory use included.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_BOUNDARY_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_boundary_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_boundary_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_boundary_v1_raw_20261001.json)
- [Topology stress results](THOUGHTEXPERIMENT_SHAPE_DECODING_TOPOLOGY_V1_RESULTS_20261001.md)
