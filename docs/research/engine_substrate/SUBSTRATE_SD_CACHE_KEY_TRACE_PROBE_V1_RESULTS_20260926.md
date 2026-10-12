# Shape-decode cache-key trace probe v1 results (2026-09-26)

The current-source native engine passes provenance verification. All seven runner checks pass across one- and two-effect paired cells.

- With one identical computed `DimInfer` effect, each codebook type (`CodebookPart`, `DimensionGenerator`) produces two `term_index_query` events across the two rule firings.
- With two identical computed effects, each type produces four query events. This is the expected 2× increase from the second key construction on each firing.
- Node type/attribute trace rows also increase, reflecting the extra fingerprint walks plus miss-path decoder work. Because the current event vocabulary merges fingerprint reads and decoder reads into the same type/attribute kinds, this probe does not infer an exact miss count from those rows.
- Traced and untraced states, progress counts, and fixed-point status match for both workload sizes. Plain arms emit no trace events; traced arms have no overflow.

This confirms source-level visibility of key construction under an active rule UID and that query markers scale with the number of computed terms. Combined with the source contract that `sd_ops` clears per firing and survives sibling effects, the second identical term is expected to reuse the cached decode. The trace does not itself label that hit. Direct evaluations outside a rule remain untraced; hit/miss event kinds, overhead, and speedup remain future measurements.

Reproduce with:

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_sd_cache_key_trace_probe_v1.py
```

See the [preregistration](SUBSTRATE_SD_CACHE_KEY_TRACE_PROBE_V1_PREREG_20260926.md), [runner](../../../scripts/substrate_sd_cache_key_trace_probe_v1.py), and [raw report](../../../evaluation/reports/substrate_sd_cache_key_trace_probe_v1_20260926.json) for the shared run manifest and source/native hashes. The manifest references a hashed parent-process log at `evaluation/run_logs/substrate-sd-cache-key-trace-probe-v1-20260926.stdout_stderr.log`; its scope is recorded in the manifest.
