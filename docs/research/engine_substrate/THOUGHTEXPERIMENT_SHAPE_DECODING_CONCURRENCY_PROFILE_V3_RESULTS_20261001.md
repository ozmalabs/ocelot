# Shape-decoding concurrency profile v3 — branch setup GIL intervention results

**Result:** 7/7 gates pass across 12 fresh processes. The intervention releases the GIL during native experimental fork and aperture-scope operations while retaining native mutex and fork behavior. All branches satisfy the positive shape-axis correction oracle, backend/mode outcomes match, primary graph/rules remain unchanged, and source/native binary locks match.

| Backend | Mode | v2 wave ms | v3 wave ms | v2 CPU/wall | v3 CPU/wall | v3 snapshot/setup ms per branch | v3 patch ms per branch | v3 prediction ms per branch |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Scoped full-copy | Sequential | 1,989.9 | 1,915.8 | 0.98× | 0.97× | 43.5 | 21.8 | 169.9 |
| Scoped full-copy | Concurrent | 3,069.3 | 1,615.1 | 0.98× | 2.00× | 357.6 | 47.0 | 995.9 |
| Shared graph pages | Sequential | 906.0 | 866.3 | 0.99× | 0.99× | 10.9 | 23.3 | 69.6 |
| Shared graph pages | Concurrent | 1,206.2 | 1,213.2 | 1.00× | 1.01× | 178.0 | 184.9 | 698.6 |

For this full-copy workload, concurrent wall time falls by about 47% against v2, while sequential time stays similar. Candidate-patch wall time in the concurrent cell also falls substantially, consistent with other Python worker threads progressing while native branch setup has released the GIL. The wave now accumulates about 3.24 CPU-seconds in 1.62 wall-seconds, demonstrating useful parallel CPU work. This is a substantial, task-specific concurrency result.

The shared-page backend does not benefit: its concurrent wave remains about 1.21 seconds with CPU/wall near 1.0×, and phase expansion in setup, patching, and prediction remains. This backend-specific difference matters: the more expensive eager native fork evidently offered independent work that could overlap once the GIL was released, whereas shared-page branch setup is cheaper sequentially and other Python/native work still serializes or contends. The experiment does not identify whether GIL-held Python patch/readout, shared primary locking, allocator, or memory behavior explains the shared-page ceiling.

The result establishes useful parallel throughput for one positive shape-decoding task with scoped full-copy branches, on one host and at fanout 8. It does not establish a general concurrency law, optimal backend policy, scaling beyond 100k nodes, or broad natural-task throughput. Next profile and intervene on the shared-page path, where patch and prediction dominate concurrent phase time; preserve full-copy v2/v3 as the before/after control and add candidate diversity and larger graph sizes after isolating this backend gap.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V3_PREREG_20261001.md)
- [Intervention amendment](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V3_AMENDMENT_20261001.md)
- [V3 lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v3_lock_20261001.json)
- [V3 runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_concurrency_profile_v3.py)
- [V3 raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_concurrency_profile_v3_raw_20261001.json)
- [Changed binding](../../../runners/dsl/src/py.rs)
- [V2 comparison](THOUGHTEXPERIMENT_SHAPE_DECODING_CONCURRENCY_PROFILE_V2_RESULTS_20261001.md)
