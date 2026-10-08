# Bigville Graph Construction and Partition Scaling Results (2026-09-26)

## Accepted capture

Nine fresh processes measured the authored Bigville five-Concept resident template at 100, 250, and 500 frames (500, 1,250, and 2,500 Concepts), with three replicates per size. At each size, the worker measured engine/production setup, resident graph construction, live owner discovery, live causal-edge extraction, component derivation, and the composed partition pass separately. Thirty-one repetitions were recorded for each live derivation stage. Every worker checked that live ownership is unique, owner frames contain five Concepts, causal components equal the owner frames, and all recomputed partitions agree. The independent analyzer passes all 12 integrity checks, including the frozen schedule, source/native hashes, worker count, expected graph shape, and sample counts.

| Frames | Concepts | Graph assembly median | Assembly / frame | Owner discovery | Edge extraction | Component derivation | Composed partition pass |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 500 | 5.40 ms | 54.0 µs | 0.314 ms | 0.341 ms | 0.299 ms | 0.969 ms |
| 250 | 1,250 | 12.80 ms | 51.2 µs | 0.823 ms | 0.867 ms | 0.773 ms | 2.471 ms |
| 500 | 2,500 | 24.61 ms | 49.2 µs | 1.646 ms | 1.903 ms | 1.519 ms | 5.140 ms |

The measured passes grow roughly in proportion to the replicated frame count over this range. Graph assembly per frame is stable in the medians. The composed partition pass includes ownership, edge extraction, and components in one timed function; its median need not equal the sum of the separate medians. `ru_maxrss` is 32,328 KiB at all three sizes, matching the process high-water mark and therefore providing no useful memory scaling result here.

## Limits and failure disclosure

This is a controlled workload with one authored frame template replicated, and baseline frames are disconnected. It gives a 100-to-500-frame scaling trace for the construction and partition routines, not a complexity theorem or evidence that natural tasks have similarly cheap cuts. It does not cover dynamic repartitioning, learning/selecting a partition, scheduler notification, closure, inference, or larger scales. Graph assembly covers repeated `build_resident_can_mt` calls; engine setup and production installation are timed separately, and no combined end-to-end number should be inferred without adding paired samples.

The first analysis attempt rejected an otherwise complete capture because the analyzer mistakenly expected five construction samples per resident instead of one. That capture is retained as [`initial gate failure`](../../../evaluation/reports/substrate_bigville_partition_scale_v1_initial_gate_failure_20260926.json) and excluded. The analyzer gate was corrected, the lock regenerated, and all nine workers rerun for the accepted capture.

## Artifacts

- [Preregistration](SUBSTRATE_BIGVILLE_PARTITION_SCALE_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_bigville_partition_scale_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_bigville_partition_scale_v1.py)
- [Accepted raw capture](../../../evaluation/reports/substrate_bigville_partition_scale_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_bigville_partition_scale_v1_analysis_20260926.json)
- [Source lock](../../../evaluation/substrate_capability/bigville_partition_scale_lock_20260926.json)
