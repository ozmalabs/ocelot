# Recurrence repair parallel thoughtexperiment wave v2 results

**Outcome: 6/6 gates pass.** The source and native binary matched the pre-run lock; all 24 worker rows came from distinct processes; sequential and concurrent branch signatures matched exactly; all 64 candidate offers were correct in every branch; parent graph/rule state remained unchanged; and timing/memory measurements were finite and valid.

This repeats the v1 recurrence-repair task after the native experiment-fork bindings release the GIL. Each process builds the same 100k-noise-node graph and 64-candidate recurrence task, then runs sequential and concurrent waves at fanout 1, 2, 4, and 8 using eager full-copy and shared graph-page branches. Each branch replaces the authored idempotence guard, runs five closure rounds, checks exactly one offer per candidate, verifies fixed point, and confirms the authored guard was restored. The 10 ms process sampler reports sampled RSS/PSS deltas; per-branch thread CPU is summed to estimate overlap. The complete capture is [raw JSON](../../../evaluation/reports/thoughtexperiment_recurrence_parallel_wave_v2_raw_20261001.json); its source/native lock is [here](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v2_lock_20261001.json).

| Backend | Fanout | Sequential median | Concurrent median | Concurrent / sequential throughput | CPU / wall | Concurrent peak ΔPSS |
|---|---:|---:|---:|---:|---:|---:|
| Full copy | 1 | 64.7 ms | 76.6 ms | 0.84× | 0.82× | 32.1 MiB |
| Full copy | 2 | 102.7 ms | 131.0 ms | 0.78× | 0.95× | 64.8 MiB |
| Full copy | 4 | 196.1 ms | 260.5 ms | 0.75× | 1.00× | 130.0 MiB |
| Full copy | 8 | 370.4 ms | 533.7 ms | 0.69× | 0.99× | 261.0 MiB |
| Shared pages | 1 | 23.5 ms | 28.0 ms | 0.84× | 0.90× | 10.8 MiB |
| Shared pages | 2 | 41.9 ms | 34.6 ms | 1.21× | 1.44× | 21.7 MiB |
| Shared pages | 4 | 76.5 ms | 52.5 ms | 1.46× | 2.05× | 43.7 MiB |
| Shared pages | 8 | 153.6 ms | 89.4 ms | 1.72× | 2.40× | 85.2 MiB |

At fanout 8, shared-page concurrent execution is 1.72× the sequential throughput and uses about 3.0× less sampled peak PSS than eager full-copy concurrent execution. The GIL-released fork path does not make full-copy waves scale on this workload: CPU overlap remains about 1× and concurrent throughput is lower than sequential at every fanout. Relative to v1, shared-page concurrent throughput gain at fanout 8 is similar in direction (1.72× here versus 1.78× in v1), while its absolute measured wave time is lower (89.4 ms versus 108.6 ms). This cross-version timing comparison is descriptive: the binary/source state differs, and three repeats per cell on one host leave substantial run-to-run noise.

The result supports a task-specific claim: this recurrence rehearsal can use shared-page branches to overlap CPU work and reduce wall time as fanout grows, while eager-copy branches pay additional memory and do not gain throughput. It does not show that GIL release alone caused the shared-page gain, nor that all thoughtexperiment workloads parallelize. The separate shape-decoding family has different Python-heavy costs and has shown backend- and pipeline-dependent concurrency. The fixture and candidate set are authored; there is no autonomous repair discovery or natural-task distribution estimate. See the [v2 preregistration](THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_WAVE_V2_PREREG_20261001.md), [GIL-release amendment](THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_WAVE_V2_AMENDMENT_20261001.md), and [v1 results](THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_WAVE_V1_RESULTS_20261001.md).

## Follow-up

Repeat across an independently authored task family with the same branch lifecycle and oracle discipline, then test recurrence at increasing graph sizes and candidate counts. Separate fork/setup, rule patch, closure, graph readout, and oracle costs. Retain paired sequential/concurrent measurements, source/native locks, exact branch-signature parity, primary isolation, and sampled memory. A general parallelism claim requires replication across workload structures and at least one independent host.
