# Recurrence repair thoughtexperiment scale v1 results

**Outcome: all 6 gates pass.** A source/native-locked 48-worker scale sweep preserves the exact candidate-level branch outcomes and primary graph/rule state across four graph-size conditions, two fork backends, fanouts 1/8, and paired sequential/concurrent waves. Every one of 64 recurrence candidates receives exactly one offer in every branch, closure reaches its fixed point, and source hashes remain stable.

The fixture holds the recurrence repair and 64 candidates fixed while adding 0, 50k, 100k, or 200k unrelated path-noise nodes. Three fresh processes repeat every backend/size/fanout cell. The runner records wall time, branch throughput, per-thread CPU sum, CPU/wall, and 10 ms sampled process RSS/PSS. See the [raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_scale_v1_raw_20261001.json), [pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_scale_v1_lock_20261001.json), [runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_scale_v1.py), and [preregistration](THOUGHTEXPERIMENT_RECURRENCE_SCALE_V1_PREREG_20261001.md).

| Noise nodes | Backend | Fanout | Sequential median | Concurrent median | Concurrent / sequential throughput | CPU / wall | Concurrent peak ΔPSS |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | Full copy | 8 | 138.4 ms | 72.2 ms | 1.92× | 2.02× | 13.3 MiB |
| 50k | Full copy | 8 | 240.5 ms | 269.5 ms | 0.89× | 1.27× | 137.8 MiB |
| 100k | Full copy | 8 | 358.2 ms | 555.6 ms | 0.64× | 0.96× | 261.0 MiB |
| 200k | Full copy | 8 | 627.8 ms | 1,094.6 ms | 0.57× | 0.80× | 507.1 MiB |
| 0 | Shared pages | 8 | 123.6 ms | 75.3 ms | 1.64× | 1.92× | 12.7 MiB |
| 50k | Shared pages | 8 | 137.2 ms | 86.3 ms | 1.59× | 2.10× | 46.7 MiB |
| 100k | Shared pages | 8 | 152.6 ms | 90.0 ms | 1.70× | 2.21× | 85.5 MiB |
| 200k | Shared pages | 8 | 184.7 ms | 105.5 ms | 1.75× | 2.47× | 157.4 MiB |

Shared-page concurrent wall time grows 1.40× from 0 to 200k added nodes, while full-copy concurrent time grows 15.2× and crosses from a speedup at zero added nodes to a slowdown from 50k onward. At 200k, shared pages are about 10.4× faster than full-copy in the concurrent wave and have about 3.2× lower sampled peak PSS. The shared-page throughput benefit remains in the 1.59–1.75× range for all nonzero sizes. Its sampled ΔPSS rises with graph size, from 46.7 MiB at 50k to 157.4 MiB at 200k, while full-copy reaches 507.1 MiB at 200k.

This supports a bounded tractability result for one recurrence-repair workload: shared-page forks preserve correct branch behavior and maintain modest latency growth through 200k unrelated nodes, while concurrent eager copies become memory- and latency-heavy. These are four finite points, not an asymptotic complexity theorem. The all-zero-noise full-copy result is a small-graph regime where parallel fork work overlaps; the loss of overlap as copied state grows is visible in the CPU/wall series, but this panel does not isolate its cause. The scale axis is unrelated graph noise, candidate count and repair complexity remain fixed, and PSS is sampled rather than allocator/kernel peak memory. The task, repair, candidates, and oracle are authored. No natural-task distribution, autonomous candidate discovery, learning cost, or independent-host replication is established.

## Follow-up

Extend candidate count independently of graph size with a direct indexed readout to avoid conflating repeated scans with learning or closure cost. Then repeat the node × candidate design on a third independently authored thoughtexperiment task family and measure full lifecycle phases. Preserve exact sequential/concurrent signature parity, primary isolation, source/native locks, and memory sampling. Test one independent host before making a general throughput claim.
