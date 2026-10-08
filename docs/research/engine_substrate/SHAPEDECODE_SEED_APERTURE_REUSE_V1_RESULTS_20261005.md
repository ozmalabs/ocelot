# ShapeDecode seed aperture reuse census v1 — results

The locked-source static census found **44 name-scoped ShapeDecode Terms in 11 checked-in seed files**, using 13 codebook types. The independent analyzer recomputed each occurrence and every seed hash; all 5 checks passed.

| Static context | Calls |
|---|---:|
| Nested under `MaxOver.value` | 3 |
| Nested under `Argmax.value` | 3 |
| Nested under `Filter.predicate` | 16 |
| Other contexts | 22 |

Six of the 44 calls use `ShapeSignature`. The others target application-specific codebooks such as embodied capability memories, motor programs, and vision comparator signatures. Therefore the cache implementation's per-codebook-type keying is relevant beyond the cross-frame fixture. The `MaxOver`, `Argmax`, and `Filter.predicate` contexts identify 22 syntactic opportunities for repeated scoped lookup inside one Term evaluation. The remaining 22 calls include direct lookups and other nesting; they may incur a cache miss without a reuse hit.

## Limits

This is a source census, not a runtime census. It establishes neither seed activation nor rule firing, and it does not count Python-constructed Terms. A syntactic aggregation context does not prove that a runtime candidate set is nonempty or that a cache hit occurs. It provides a principled source list for a production-derived benchmark panel; it does not estimate prevalence in natural tasks or predict performance.

## Artifacts

- [Protocol](SHAPEDECODE_SEED_APERTURE_REUSE_V1_PROTOCOL_20261005.md)
- [Census runner](../../../evaluation/substrate_capability/audit_shapedecode_seed_aperture_reuse_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_shapedecode_seed_aperture_reuse_v1.py)
- [Raw census](../../../evaluation/reports/shapedecode_seed_aperture_reuse_v1_20261005.json)
- [Analysis](../../../evaluation/reports/shapedecode_seed_aperture_reuse_v1_analysis_20261005.json)
