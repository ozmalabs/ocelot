# Shape-decoding correction parallel thoughtexperiment wave v1 — results

**Result:** 6/6 gates pass across 48 fresh processes (three per backend/fanout/mode cell). All rehearsals apply `dedup_identity_fix`, are non-inert, converge under the shape-axis oracle, return matching signatures across execution modes/backends, and preserve the primary graph/rules/revision. Source and native binary locks match.

Host: Linux x86_64, 24 logical CPUs; cgroup CPU quota was unavailable. Each branch uses the production shape-decoding candidate and a 100k-node linked noise graph. Wall time includes branch snapshot, candidate patch, prediction, and residual readout.

| Backend | Fanout | Sequential ms | Concurrent ms | Sequential runs/s | Concurrent runs/s | Concurrent speedup | Concurrent peak ΔPSS |
|---|---:|---:|---:|---:|---:|---:|---:|
| `native_full_copy_scoped` | 1 | 242.6 | 323.2 | 4.12 | 3.09 | 0.75× | 101.9 MiB |
| `native_full_copy_scoped` | 2 | 485.8 | 703.6 | 4.12 | 2.84 | 0.69× | 205.4 MiB |
| `native_full_copy_scoped` | 4 | 940.3 | 1455.8 | 4.25 | 2.75 | 0.65× | 413.5 MiB |
| `native_full_copy_scoped` | 8 | 1979.8 | 2892.9 | 4.04 | 2.77 | 0.68× | 829.2 MiB |
| `native_shared_graph_pages_scoped` | 1 | 98.1 | 124.3 | 10.19 | 8.04 | 0.79× | 13.1 MiB |
| `native_shared_graph_pages_scoped` | 2 | 220.2 | 258.2 | 9.08 | 7.75 | 0.85× | 26.3 MiB |
| `native_shared_graph_pages_scoped` | 4 | 395.4 | 507.9 | 10.12 | 7.88 | 0.78× | 55.7 MiB |
| `native_shared_graph_pages_scoped` | 8 | 889.9 | 1025.1 | 8.99 | 7.80 | 0.87× | 116.2 MiB |

Shared graph pages consistently reduce the full rehearsal cost relative to scoped full-copy. At fanout 8, shared pages reach 7.80 rehearsals/s concurrently versus 2.77/s for full-copy, and peak ΔPSS is 116.2 versus 829.2 MiB (about 7.1× lower). But threaded execution is slower than sequential for both backends at every measured fanout: at fanout 8, concurrent/sequential throughput is 0.87× for shared pages and 0.68× for full-copy. Thus branch sharing transfers as a cost reduction to this independent task family, while the parallel-throughput gain from the recurrence closure fixture does not. The end-to-end workload includes Python orchestration, graph reads, prediction, patching, and native operations; this panel does not localize the concurrency bottleneck.

Each cell has three fresh-process repeats. The sampler ran every 10 ms and can miss brief peaks. This is one authored shape-axis task, one host, one candidate repeated across branches, and one synthetic noise topology. It does not measure candidate discovery, independent task diversity, or natural workloads. Next profile Python and native phases separately, then test whether moving hot orchestration into native code improves concurrent throughput without changing task outcomes.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_PARALLEL_WAVE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_parallel_wave_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_parallel_wave_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_parallel_wave_v1_raw_20261001.json)
