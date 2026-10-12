# Vision-eye corruption replay — post-hoc v1.2 results

## Result

All seven v1.2 gates pass on the v2.1 captured weights. The analysis covers 288 held-out probes per morphology at six conditions: clean, 25/50/75% active-pixel dropout, and background additions equal to 25/50% of original mask area. Corruption masks are deterministic and shared across the frozen-weight, centroid, and Hamming scorers. Clean learned-map scores reconcile exactly to the published 288/288 square and 210/288 cross results.

| Morphology | Condition | Frozen-weight map | Centroid region | Hamming set-valued region |
|---|---|---:|---:|---:|
| Square | Clean | 288/288 | 288/288 | 288/288 |
| Square | 25% dropout | 273/288 | 288/288 | 280/288 |
| Square | 50% dropout | 237/288 | 281/288 | 259/288 |
| Square | 75% dropout | 192/288 | 240/288 | 226/288 |
| Square | +25% background | 286/288 | 187/288 | 287/288 |
| Square | +50% background | 274/288 | 163/288 | 282/288 |
| Cross | Clean | 210/288 | 288/288 | 288/288 |
| Cross | 25% dropout | 205/288 | 288/288 | 288/288 |
| Cross | 50% dropout | 176/288 | 270/288 | 288/288 |
| Cross | 75% dropout | 108/288 | 234/288 | 288/288 |
| Cross | +25% background | 195/288 | 188/288 | 222/288 |
| Cross | +50% background | 209/288 | 171/288 | 235/288 |

The frozen learned map is much more resilient than the centroid under added background noise, especially for square patches, while centroid localization is stronger under active-pixel dropout. These are descriptive comparisons on synthetic, translated masks. Hamming coverage is set-valued: ties count as covered when any tied template belongs to the correct region. Exact score ties also occur in the frozen model replay; its reported region accuracy maps all tied WUnit winners through their learned receptive-field centers as a set. The counts therefore do not specify how the live scheduler resolves an ambiguous corrupted input.

## Scope and limits

This is deterministic analytical forward replay of captured weights. It uses the validated weight-sum/argmax equation but does not rerun Rust scheduling, host mutation, or online learning. Input position is still directly represented by active-pixel coordinates, and the corruption families are synthetic. No natural-image or semantic-recognition claim follows. Square and cross conditions also differ in active-cell count.

The v1 and v1.1 analyses failed clean reconciliation and are preserved as superseded diagnostics; see the [v1.1 amendment](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_1_AMENDMENT_20261005.md) and [v1.2 amendment](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_2_AMENDMENT_20261005.md). Only the v1.2 report is interpretable.

## Artifacts

- [Corrected protocol](SUBSTRATE_VISION_EYE_CORRUPTION_REPLAY_POSTHOC_V1_2_PROTOCOL_20261005.md)
- [Analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_corruption_replay_posthoc_v1_2.py)
- [Machine report](../../../evaluation/reports/vision_eye_corruption_replay_posthoc_v1_2_20261005.json)
- [v2.1 learned-map results](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_RESULTS_20261005.md)
