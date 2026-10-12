# Long-term memory restart scale envelope: 10,000–50,000 records

**Date:** 2026-09-25. This follow-up extends the locked scale-v1 protocol to larger per-cluster occupancy. It uses the same record generator and reader checks, with three independent writer/reader pairs at each size.

## Important scope constraint

`LongTermMemory._feature_vec(..., "category")` always returns exactly three values. `ShapeIndex.cluster_id` keys by their strict ordinal-rank shape, so this adapter path has at most `3! = 6` category clusters (fewer when values tie). Accordingly, these runs stress the number of files and records within those six clusters; they do not test growth in cluster count. The lock for this extension makes that limitation explicit.

## Results

| Records | Clusters | Durable bytes | Median write time | Median bind/index rebuild | Median one-key-per-cluster recall/page-in | Peak reader RSS | Full headers / sampled attribute checks |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10,000 | 6 | 1,267,780 B | 0.39 s | 307.54 ms | 66.95 ms | 30.39 MiB | 30,000 / 18 of 18 |
| 50,000 | 6 | 6,427,780 B | 2.02 s | 1.622 s | 351.05 ms | 71.78 MiB | 150,000 / 18 of 18 |

Each of the six reader processes (three per size) restored every record header and every representative recall returned the expected attrs. Writer and reader PIDs were distinct. The whole 12-process batch completed in 19.13 seconds. Peak RSS is the process high-water mark, including the interpreter/native import baseline, not an allocation-level index measure. Raw data: [`substrate_memory_restart_scale_extended_20260925.json`](../../../evaluation/reports/substrate_memory_restart_scale_extended_20260925.json); pre-run source and artifact hashes: [`memory_restart_scale_extended_lock_20260925.json`](../../../evaluation/substrate_capability/memory_restart_scale_extended_lock_20260925.json).

The bind cost remains close to linear with record count in this local synthetic family: 10,000 records take about 0.31 seconds and 50,000 take about 1.62 seconds. This includes glob enumeration, sorting, JSON decoding, feature projection and native index insertion. The six shape-class recalls page all 50,000 records into the fresh graph, so the 351 ms recall measure includes full attribute page-in. Per-key exact lookup cost is not isolated from cluster page-in here.

## Limits

This shows restart indexing and representative exact-key retrieval at 50,000 tiny synthetic records. It does not test larger feature vocabularies, more than six clusters, large attribute payloads, cold-cache I/O, malformed/duplicate keys, concurrent writes, all-key payload validation, or relationship restoration. Because adapter features enforce the six-cluster ceiling, measuring cluster-count sensitivity requires a deliberate feature-model change or a separate direct-native benchmark, and results from the latter must not be attributed to the current host adapter. Next decide whether to broaden the category feature signature; regardless, measure cold/warm startup and record integrity before treating restart recovery as robust.
