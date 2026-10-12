# Recurrence repair thoughtexperiment candidate-count scale v1 results

**Outcome: all 7 gates pass.** The locked 48-worker panel spans 1/16/64/128 recurrence candidates, full-copy/shared-page forks, and fanout 1/8 with paired sequential and concurrent waves. Every worker has the expected candidate count; all candidates satisfy the exact-one-offer oracle; sequential/concurrent signatures match; primary graph/rule state remains unchanged; sources and native binary match the lock; and timing/memory values are valid.

The graph is held at 100k unrelated path-noise nodes. Each candidate receives the same authored recurrence repair. To avoid adding quadratic harness readout, the branch builds a recurrence-key-to-node index in one pass, then checks every candidate. This isolates candidate-set growth more cleanly than the earlier wave runner, although timing still includes fork setup, native rule replacement, closure, and oracle work. Full data are in the [raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_candidate_scale_v1_raw_20261001.json), with the [pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_scale_v1_lock_20261001.json), [runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_scale_v1.py), and [preregistration](THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_SCALE_V1_PREREG_20261001.md).

| Candidates | Backend | Fanout | Sequential median | Concurrent median | Concurrent / sequential throughput | CPU / wall | Concurrent peak ΔPSS |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | Shared pages | 8 | 24.9 ms | 38.1 ms | 0.65× | 1.09× | 13.8 MiB |
| 16 | Shared pages | 8 | 60.9 ms | 53.2 ms | 1.14× | 1.80× | 50.3 MiB |
| 64 | Shared pages | 8 | 124.8 ms | 62.1 ms | 2.01× | 2.87× | 85.7 MiB |
| 128 | Shared pages | 8 | 216.1 ms | 72.0 ms | 3.00× | 3.90× | 90.6 MiB |
| 1 | Full copy | 8 | 257.8 ms | 518.3 ms | 0.50× | 0.80× | 251.3 MiB |
| 16 | Full copy | 8 | 283.5 ms | 512.8 ms | 0.55× | 0.85× | 258.3 MiB |
| 64 | Full copy | 8 | 349.7 ms | 486.9 ms | 0.72× | 0.98× | 260.5 MiB |
| 128 | Full copy | 8 | 433.7 ms | 520.4 ms | 0.83× | 1.14× | 264.7 MiB |

For shared pages, sequential latency rises 8.7× from one to 128 candidates, while concurrent latency rises 1.9×; concurrent throughput crosses from a penalty at one candidate to 3.0× at 128. This suggests that the larger per-branch work exposes useful parallelism in this task. Full-copy waves carry a much larger memory baseline at every candidate count and remain slower concurrently, although their sequential time rises with candidate count. These are medians from three fresh workers per cell on one 24-logical-CPU host; small cells are especially sensitive to setup and scheduler noise.

The experiment supports a bounded capability claim: the graph-resident task can evaluate a larger authored candidate set while preserving exact branch behavior, and shared-page execution can parallelize that work. It does not show autonomous candidate generation, diversity of candidate semantics, open-ended induction, learned search policy, or natural candidate-count distributions. Candidate count is not hypothesis-space complexity, and no asymptotic law follows from four points. PSS is sampled every 10 ms rather than measured with allocator or kernel peak instrumentation.

## Follow-up

Vary semantic candidate diversity and success prevalence independently of candidate count, and measure rule patch, closure, readout, and branch setup separately. Then transfer to a third independently authored task family and repeat on an independent host. Preserve source/native locks, exact branch signatures, candidate-level oracle checks, and primary isolation.
