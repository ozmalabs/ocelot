# ShapeDecode name-aperture baseline v1 — results

## Result

The source-locked current-scan benchmark passed all 14 analysis checks over 24 fresh worker processes. Each worker held one exact target observation and an authored codebook size of 16, 32, 64, or 128 parts; the effective ShapeSignature populations were 33, 49, 81, and 145 after including 17 boot-installed entries. Every worker selected `r00`, and traced/untraced pairs matched winner and coarse closure work.

| Effective ShapeSignature population P | ShapeDecode calls | Population visits | Median untraced closure | Median CPU |
|---:|---:|---:|---:|---:|
| 33 | 66 | 2,178 | 15.934 ms | 15.943 ms |
| 49 | 98 | 4,802 | 24.129 ms | 24.068 ms |
| 81 | 162 | 13,122 | 41.530 ms | 41.525 ms |
| 145 | 290 | 42,050 | 86.711 ms | 86.702 ms |

The observed work is exactly `2P²` in each cell: the rule path makes two ShapeDecode calls per codebook candidate, and each call enumerates all P typed parts before applying its singleton `codebook_scope`. This is direct evidence of quadratic population-enumeration work for this authored candidate-at-a-time path. It is not a general complexity result for ShapeDecode or the substrate. Closure time grows 5.44× as P grows 4.39× over this range; three replicates per cell and millisecond-scale samples make the timing descriptive rather than a stable performance model.

## Evidence and limits

The runner and independent analyzer are [source-locked](../../../evaluation/substrate_capability/shapedecode_name_aperture_baseline_v1_lock_20261005.json). The [capture](../../../evaluation/reports/shapedecode_name_aperture_baseline_v1_20261005.json) retains per-worker trace rows, process IDs, source manifests, outputs, and timing. The independent [analysis](../../../evaluation/reports/shapedecode_name_aperture_baseline_v1_analysis_20261005.json) verifies all 14 gates. The initial capture is retained as a [pre-amendment audit artifact](../../../evaluation/reports/shapedecode_name_aperture_baseline_v1_pre_amendment_analysis_20261005.json); amendment v1.1 corrected effective population labels after the runner revealed 17 boot-installed codebook parts.

This is one synthetic cross-frame identity rule shape with one observation and predicate-distinct distractors. It does not compare an indexed implementation, measure natural task prevalence, isolate helper CPU time, or establish that name-index construction and mutation costs pay off in production. Trace work units are counts, not elapsed CPU. The next gate is an indexed-name prototype only after its case-folding, duplicate ordering/overwrite, `Str`/`Surface(Text)`, empty/absent scope, malformed-entry, and graph lifecycle semantics are fixed. Require exact graph/output parity, then compare paired untraced closure latency, CPU, peak RSS, and index lifecycle cost at larger populations.
