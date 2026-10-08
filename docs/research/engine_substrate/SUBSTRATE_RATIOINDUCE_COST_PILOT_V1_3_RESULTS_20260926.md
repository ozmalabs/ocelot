# RatioInduce direct-cost pilot v1.3 — results (2026-09-26)

## Result class and provenance

**Pilot only.** This is a direct-call scaling measurement, not a confirmatory tractability claim. The primary capture is [raw v1.3 JSON](../../../evaluation/reports/substrate_ratioinduce_cost_pilot_v1_3_20260926.json), produced by [runner](../../../scripts/substrate_ratioinduce_cost_pilot_v1_3.py); deterministic checks and summaries are in [analysis JSON](../../../evaluation/reports/substrate_ratioinduce_cost_pilot_v1_3_analysis_20260926.json) and [analyzer](../../../scripts/analyze_substrate_ratioinduce_cost_pilot_v1_3.py). Engine provenance: `f5543ca01527`, the local `_native.abi3.so` build. Raw includes git commit, dirty-tree flag, native binary hash, source/protocol hashes, Python/platform/CPU count, peak process RSS, each per-call wall/CPU sample, and structural output checks.

The preregistration is [here](SUBSTRATE_RATIOINDUCE_COST_PILOT_PREREG_20260926.md). Two failed harness captures were retained separately and excluded: v1 used an empty typed signature; v1.1 declared more coordinate dimensions than its lower-D fixtures contained. Amendments [v1.1](SUBSTRATE_RATIOINDUCE_COST_PILOT_V1_1_AMENDMENT_20260926.md), [v1.2](SUBSTRATE_RATIOINDUCE_COST_PILOT_V1_2_AMENDMENT_20260926.md), and [v1.3](SUBSTRATE_RATIOINDUCE_COST_PILOT_V1_3_AMENDMENT_20260926.md) state each correction. Only v1.3 is summarized below; its 11 cells and three per-D untimed warm-ups all pass.

## Measurements

Seven timed direct `Substrate.evaluate(RatioInduce)` calls/cell; population values were materialized before timing. Medians and nearest-rank p90 are shown. The passed structural counter is `N × (D−1)` ratio-verification checks.

| Sweep | N frames | Relations/frame | D coordinates | Input relations | Median wall | p90 wall | Checked |
|---|---:|---:|---:|---:|---:|---:|---:|
| Frames | 2 | 16 | 2 | 32 | 0.0170 ms | 0.0220 ms | 2 |
| Frames | 8 | 16 | 2 | 128 | 0.0587 ms | 0.0636 ms | 8 |
| Frames | 32 | 16 | 2 | 512 | 0.2087 ms | 0.2609 ms | 32 |
| Frames | 128 | 16 | 2 | 2,048 | 0.8372 ms | 1.5039 ms | 128 |
| Relations/frame | 16 | 4 | 2 | 64 | 0.0328 ms | 0.0492 ms | 16 |
| Relations/frame | 16 | 16 | 2 | 256 | 0.1070 ms | 0.1096 ms | 16 |
| Relations/frame | 16 | 64 | 2 | 1,024 | 0.4389 ms | 0.6612 ms | 16 |
| Relations/frame | 16 | 256 | 2 | 4,096 | 1.5840 ms | 2.4873 ms | 16 |
| Dimensions | 16 | 16 | 2 | 256 | 0.1058 ms | 0.1300 ms | 16 |
| Dimensions | 16 | 16 | 3 | 256 | 0.1273 ms | 0.1342 ms | 32 |
| Dimensions | 16 | 16 | 4 | 256 | 0.1362 ms | 0.1451 ms | 48 |

At fixed 16 relations/frame, N grows 64× (2→128) and median time grows 49.16×. At fixed 16 frames, P grows 64× (4→256) and median time grows 48.22×. Both are consistent with roughly input-linear work on this positive fixture. Increasing D from 2 to 4 at fixed total relation count raises median 1.29×; the range is too small to characterize high-dimensional cost. At the largest cell, 4,096 relations, median direct call is 1.584 ms, with p90 2.487 ms. Process peak RSS is a single process high-water mark, not a per-cell allocation measure.

## Interpretation and limits

The observed work is consistent with scanning the population's integer coordinate values plus frame/dimension ratio checks. It supports a narrow statement: **the direct native operator is inexpensive through 128 frames × 256 relations/frame × 2 coordinate dimensions for an already materialized exact common-ratio population on this build and host.**

This does not establish total operating cost or production tractability. Timing includes Python-to-native evaluation/conversion but excludes population construction, upstream feature extraction, graph closure, partition/population maintenance, rule scheduling, mint/redecode, held-out reuse, and memory attributable to one call. Only one exact positive family is used; no noisy, inconsistent, missing, high-D, false-positive, or natural-task distribution is covered. The separate semantic correction remains decisive: the operator detects within-frame ratios, its non-power-of-two emitted matrix fails the apply-semantics probe, and it does not output the inter-frame scale factors. Cheap detection cost does not imply the desired learning capability exists.

## Next gate

Resolve the operator's task semantics and emitted representation before investing in production integration. Once a valid output contract exists, extend this cost protocol with null/abstention arms, noisy quantization, inter-frame scale estimation, and complete seed-level acquisition/reuse cost. Keep semantic correctness as a hard gate: no cost result can promote the present candidate matrix as a faithful ratio map.
