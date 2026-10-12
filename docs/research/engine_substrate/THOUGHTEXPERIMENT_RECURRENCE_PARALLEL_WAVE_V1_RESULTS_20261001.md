# Recurrence repair parallel thoughtexperiment wave v1 — results

**Result:** 5/5 gates pass across 24 fresh processes (three per backend/fanout cell). Every branch restores the authored idempotence guard, produces exactly one offer for each of 64 recurrence candidates, reaches a zero-progress fixed point, and leaves the primary graph/rules/revision unchanged. Sequential and concurrent branch outcomes match.

The host reports 24 logical CPUs; `/sys/fs/cgroup/cpu.max` was unavailable, so an effective CPU quota could not be established. Wall times are medians of three runs and include branch fork, repair, native closure, candidate oracle reads, and release.

| Backend | Fanout | Sequential ms | Concurrent ms | Sequential runs/s | Concurrent runs/s | Concurrent speedup | Concurrent peak ΔPSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| `full_copy` | 1 | 75.6 | 89.3 | 13.2 | 11.2 | 0.85× | 32.7 MiB |
| `full_copy` | 2 | 133.6 | 158.1 | 15.0 | 12.7 | 0.85× | 64.7 MiB |
| `full_copy` | 4 | 248.1 | 274.0 | 16.1 | 14.6 | 0.91× | 98.7 MiB |
| `full_copy` | 8 | 436.1 | 511.3 | 18.3 | 15.6 | 0.85× | 164.7 MiB |
| `shared_pages` | 1 | 29.4 | 35.9 | 34.0 | 27.8 | 0.82× | 10.8 MiB |
| `shared_pages` | 2 | 51.0 | 40.6 | 39.2 | 49.2 | 1.26× | 21.7 MiB |
| `shared_pages` | 4 | 103.1 | 64.3 | 38.8 | 62.2 | 1.60× | 43.4 MiB |
| `shared_pages` | 8 | 193.5 | 108.6 | 41.3 | 73.6 | 1.78× | 65.6 MiB |

At fanout 8, shared graph pages complete 73.6 rehearsals/s versus 41.3/s sequential (1.78×), with 65.6 MiB sampled peak ΔPSS. Full-copy concurrency reaches 15.6/s versus 18.3/s sequential (0.85×), with 164.7 MiB peak ΔPSS. This demonstrates a useful concurrency advantage for the shared-page backend on this task workload. Branch fork calls are serialized through the Python API/GIL; native `run_rules` releases the GIL and overlaps across isolated branches. The result therefore measures concurrent native closure with serialized fork setup, not fully parallel setup.

Memory grows with the number of simultaneously live branches: at fanout 8 shared-page peak ΔPSS is about 6× the sequential peak, while remaining about 2.5× below full-copy concurrent peak. The 10 ms sampler recorded only 4–15 points depending on the arm and can miss brief peaks. This is a single authored recurrence family with duplicated candidate structure and linked synthetic noise on one host; it does not measure autonomous candidate discovery, task diversity, natural workload throughput, or serving integration.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_PARALLEL_WAVE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_parallel_wave_v1_raw_20261001.json)
