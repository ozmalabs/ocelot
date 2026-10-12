# Long-term memory restart scale envelope

**Date:** 2026-09-25. This probe measures fresh-process directory scan/index reconstruction, exact-key recall and cluster page-in after the single-record restart repair.

## Protocol

[`substrate_memory_restart_scale.py`](../../../scripts/substrate_memory_restart_scale.py) runs fresh writer and reader subprocesses for 1, 10, 100, 1,000 and 5,000 durable records, with three independent temporary stores per size. The deterministic record attributes cycle through six permutations of three feature values, producing up to six category-shape clusters. The reader times adapter bind (directory scan plus native index insertion), recalls one key per shape class, checks the returned attrs, records restored key and cluster counts, and captures process peak RSS. Each run uses the current built native extension and a distinct PID for writer and reader.

The pre-run lock, including SHA-256 hashes for sources and engine artifacts, is [`memory_restart_scale_lock_20260925.json`](../../../evaluation/substrate_capability/memory_restart_scale_lock_20260925.json). Raw results are [`substrate_memory_restart_scale_20260925.json`](../../../evaluation/reports/substrate_memory_restart_scale_20260925.json). The three writer/reader pairs at each size completed in 3.28 seconds total. No test suite was run.

## Results

| Records | Clusters | Median durable bytes | Median write time | Median fresh-bind time | Median recall/page-in time* | Peak reader RSS** | Correct restore / sampled recalls |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 121 B | 0.27 ms | 0.24 ms | 0.07 ms | 20.4 MiB | 3/3; 3/3 |
| 10 | 6 | 1,210 B | 0.62 ms | 0.55 ms | 0.15 ms | 20.4 MiB | 3/3; 18/18 |
| 100 | 6 | 12,280 B | 3.93 ms | 3.40 ms | 0.73 ms | 20.4 MiB | 3/3; 18/18 |
| 1,000 | 6 | 124,780 B | 39.71 ms | 30.72 ms | 6.77 ms | 21.4 MiB | 3/3; 18/18 |
| 5,000 | 6 | 632,780 B | 200.39 ms | 157.19 ms | 33.74 ms | 26.8 MiB | 3/3; 18/18 |

*One recalled key per distinct category-shape class; the first recall for each cluster pages that cluster into the graph. Every restored JSON file is separately counted in `_known` and cluster path indexes.

**Linux `ru_maxrss`, including interpreter/import baseline; this is whole-process peak RSS, not memory attributed to the index or graph.

Within this constructed six-cluster family, median bind time is close to linear in record count over 1–5,000 records. This matches the implementation: Python scans each `*.json` file, decodes its record header, projects features, and inserts one path into the native `ShapeIndex`. Exact-key lookup scans the cluster table for the key and then accesses its per-cluster path map. The timings are local filesystem results, with no repeated warm-cache control, no high-cluster-count stress case, and no extrapolation beyond 5,000 files.

## Limits and next gates

This establishes a small synthetic startup envelope, not general memory tractability. Most records collapse into six clusters; it does not measure a high-cardinality shape distribution. Recall samples only one key per cluster class, though all record headers are indexed. It does not verify all 5,000 returned payloads, relationship restoration, concurrent access, corruption handling, duplicate keys, or retrieval quality/interference in an actual task. Peak RSS includes a roughly 20 MiB interpreter/native import floor.

The next extension measures 10,000–50,000 records; higher cluster-count sensitivity is not attainable through the current three-value host feature projection without changing that model. Separate file enumeration, JSON decode, feature projection, native insertion and page-in costs; measure cold and warm filesystem caches; then define robust duplicate, malformed-record and concurrent-writer behavior. Relationship persistence remains a separate data-model decision and is not established by these results. The extension is recorded in [`SUBSTRATE_MEMORY_RESTART_SCALE_EXTENDED_RESULTS.md`](SUBSTRATE_MEMORY_RESTART_SCALE_EXTENDED_RESULTS.md).
