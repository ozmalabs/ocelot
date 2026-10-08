# Full-Substrate GenInfer scope-index lifecycle v1 results

Date: 2026-10-05. The 18 fresh-worker capture passes the independent analyzer's 11 gates. All nine paired scan/index comparisons produce identical `recognized_transformed` results, receipts, acquired generators, and `run_rules()` work count (9). Fork creation matches parent graph state; branch mutation preserves primary isolation and indexed bucket parity; graph restore and post-restore index re-declaration preserve exact graph/member identity.

This is a synthetic route-level scaling probe, not a natural-task study. It starts from `boot_core()` and the native `shape_decode_loop`, uses two locked linear transformations, and adds unrelated `ShapeSignature` decoys with empty signatures. The scopes and decoys are supplied by the harness. Protocol: [preregistration](SUBSTRATE_GENINFER_SCOPE_INDEX_LIFECYCLE_V1_PREREG_20261005.md). Runner: [capture harness](../../../evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1.py). Independent checker: [analyzer](../../../evaluation/substrate_capability/analyze_geninfer_scope_index_lifecycle_v1.py).

## Paired closure timing

Times are per worker; each cell has three fresh processes. “Indexed / scan” is the ratio of the two cell medians. Ratios above 1 indicate the index arm was slower in this panel.

| Unrelated decoys | ShapeSignature population | Scan closure median | Indexed closure median | Indexed / scan | Index build median | Index restore rebuild median |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 19 | 23.14 ms | 29.02 ms | 1.25× | 0.004 ms | 0.006 ms |
| 1,000 | 1,019 | 31.42 ms | 42.29 ms | 1.35× | 0.106 ms | 0.135 ms |
| 10,000 | 10,019 | 107.76 ms | 109.74 ms | 1.02× | 0.991 ms | 1.014 ms |

Indexed closure was slower in seven of the nine pairs. At 10,000 decoys the arms are close, with the indexed arm slower in two pairs and faster in one. The index does remove whole-population lookup work in the previously measured trace, but this full closure route does not show a closure speedup. Other rule matching and graph-wide work appear to dominate these end-to-end timings; that explanation is consistent with the results but was not separately attributed in this run.

## Lifecycle measurements

| Decoys | Task insertion scan / indexed | Full shared-page Substrate fork scan / indexed | 32 scope mutations scan / indexed | Graph serialize scan / indexed | Graph restore scan / indexed |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.344 / 0.289 ms | 0.303 / 0.284 ms | 0.0008 / 0.0013 ms | 2.36 / 3.42 ms | 3.36 / 3.40 ms |
| 1,000 | 0.407 / 0.404 ms | 0.365 / 0.395 ms | 0.171 / 0.100 ms | 18.80 / 11.78 ms | 12.69 / 12.59 ms |
| 10,000 | 0.439 / 0.476 ms | 0.776 / 0.517 ms | 0.190 / 0.142 ms | 118.18 / 134.92 ms | 109.51 / 102.89 ms |

Lifecycle phase timings are noisy at these small sample counts and no consistent timing tax should be inferred from small scan/index differences. The 10k population has about a 1 ms index build and re-build cost. Process high-water RSS after closure was 129.6 MiB for scan and 156.8 MiB for indexed at 10k; HWM is cumulative across boot, branch creation, graph serialization/restore, and closure, so this is descriptive and not an allocation attribution.

## Gate assessment

The index mechanism is correct across the tested task, branch, mutation, and graph restore paths. The earlier operation-count improvement does not translate into an observed full-closure gain through 10,000 unrelated codebook nodes. Keep index use opt-in. The next evaluation should attribute non-helper closure work and repeat on larger populations and representative production codebooks with more workers, separate traced/untraced controls, and memory attribution. A scope producer that is independently valid remains a separate structural prerequisite.

Artifacts: [source lock](../../../evaluation/substrate_capability/geninfer_scope_index_lifecycle_v1_lock_20261005.json), [raw capture](../../../evaluation/reports/geninfer_scope_index_lifecycle_v1_20261005.json), and [independent analysis](../../../evaluation/reports/geninfer_scope_index_lifecycle_v1_analysis_20261005.json).
