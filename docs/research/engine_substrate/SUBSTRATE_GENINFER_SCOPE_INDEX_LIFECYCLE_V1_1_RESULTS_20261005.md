# Full-Substrate GenInfer scope-index lifecycle v1.1 results

Date: 2026-10-05. The confirmatory v1.1 capture passes all 16 independent gates across 36 fresh processes. Each of the nine case/replicate cells has a separate traced and untraced process for both scan and indexed modes. All traced/untraced and scan/index comparisons preserve exact task outputs, transformation receipts, acquired generators, and `run_rules()` return count. The trace has zero dropped rows.

The traced workers isolate GenInfer helper 4. Population visits scale with the complete typed codebook in the scan arm and disappear in the indexed arm. Parsed parts and candidate searches remain exact matches:

| Decoys | Typed population | Scan node visits | Indexed node visits | Parts parsed, both | Search candidates, both | Indexed queries / members |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 76 | 0 | 4 | 9,600 | 4 / 4 |
| 1,000 | 1,019 | 4,076 | 0 | 4 | 9,600 | 4 / 4 |
| 10,000 | 10,019 | 40,076 | 0 | 4 | 9,600 | 4 / 4 |

## Untraced closure and lifecycle

Times are medians of three fresh untraced workers per cell. Closure ratios are indexed/scan; small differences are within the resolution of this pilot.

| Decoys | Scan closure | Indexed closure | Indexed / scan | Index build | Index rebuild after restore | Fork scan / indexed |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19.52 ms | 19.67 ms | 1.008× | 0.003 ms | 0.006 ms | 0.220 / 0.186 ms |
| 1,000 | 27.19 ms | 26.44 ms | 0.972× | 0.060 ms | 0.096 ms | 0.197 / 0.300 ms |
| 10,000 | 86.14 ms | 85.91 ms | 0.997× | 0.500 ms | 1.019 ms | 0.429 / 0.405 ms |

The index removes the typed-population scan without reducing the fixed parse or candidate-search work. Closure medians are effectively equal at all three population levels; six of nine individual pairs favored the index, with three favoring scan, and the median differences are small. This does not demonstrate an end-to-end speedup. The earlier v1 capture's 23–29/31–42/108–110 ms timings were from a pilot with less stable process conditions and are superseded for the final latency statement, while remaining preserved as pilot evidence.

## Residual helper work

A post-hoc analysis of the same source-locked traces groups events by helper-family subject. At 10,000 decoys, the GenInfer index removes 40,076 visits, but ShapeDecode, TransformDecode, and DimInfer still account for 120,228 full-population visits. Thus this index removes one quarter of the measured helper population enumeration in this route; the other three quarters are unchanged. At 0 and 1,000 decoys, the same 25% fraction is removed.

| Decoys | ShapeDecode visits | TransformDecode visits | DimInfer visits | GenInfer visits, scan → indexed | Total visits, scan → indexed |
|---:|---:|---:|---:|---:|---:|
| 0 | 38 | 76 | 114 | 76 → 0 | 304 → 228 |
| 1,000 | 2,038 | 4,076 | 6,114 | 4,076 → 0 | 16,304 → 12,228 |
| 10,000 | 20,038 | 40,076 | 60,114 | 40,076 → 0 | 160,304 → 120,228 |

Search-candidate work remains 14,610 units in each arm: ShapeDecode 2, TransformDecode 76, DimInfer 4,932, and GenInfer 9,600. These counters are named loop work units, not equivalent operation counts or CPU time. The post-hoc grouping is reproducible from the [helper-residual analysis](../../../evaluation/reports/geninfer_scope_helper_residual_v1_analysis_20261005.json) and its [analyzer](../../../evaluation/substrate_capability/analyze_geninfer_scope_helper_residual_v1.py); helper-family subject IDs are defined in [`access_trace.rs`](../../../runners/dsl/src/access_trace.rs) and described in the [counter contract](SUBSTRATE_DYNAMIC_HELPER_WORK_COUNTERS_V1_IMPLEMENTATION_20261005.md). This identifies the remaining measured work categories, but does not establish their share of wall time.

At 10k decoys, graph serialization and restore medians are about 86/69 ms, much larger than the ~0.5/1.0 ms index build/rebuild. Process high-water RSS after closure is 156.3 MiB scan and 157.2 MiB indexed. HWM is cumulative and cannot attribute memory to the index. Fork and the 32-node scope-mutation timings are similar at this small replicate count; they do not resolve a stable per-operation index tax. Graph restore is only graph serialization/restore, not a complete persisted Substrate checkpoint.

## Gate decision

Mechanism correctness is established for this synthetic live route: index membership survives insertion, branch mutation, full shared-page Substrate fork, graph restore plus re-declaration, and GenInfer execution. Helper-work attribution establishes that scope indexing eliminates the repeated typed codebook enumeration while preserving parsed parts and search candidates. The end-to-end closure benefit remains unproven because full closure time does not measurably fall. Keep index admission opt-in and continue measuring other dominant closure work, larger/representative codebooks, and task-natural frame provenance before treating frame locality as a tractability result.

Protocol: [v1 preregistration](SUBSTRATE_GENINFER_SCOPE_INDEX_LIFECYCLE_V1_PREREG_20261005.md), [v1.1 amendment](SUBSTRATE_GENINFER_SCOPE_INDEX_LIFECYCLE_V1_1_AMENDMENT_20261005.md). Runner and analyzer: [capture](../../../evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1.py), [independent analysis](../../../evaluation/substrate_capability/analyze_geninfer_scope_index_lifecycle_v1_1.py). Final artifacts: [source lock](../../../evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_1_lock_20261005.json), [raw capture](../../../evaluation/reports/geninfer_scope_index_lifecycle_v1_1_20261005.json), and [analysis](../../../evaluation/reports/geninfer_scope_index_lifecycle_v1_1_analysis_20261005.json). Superseded v1 and v1.1-initial captures are retained in the reports directory with their lock/analysis files.
