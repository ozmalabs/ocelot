# Vision-eye coordinate baselines — post-hoc results

This analysis reuses the source-locked v1 and v2.1 phase-0 captures; it is post-hoc and introduces no new training runs. The independent analyzer reconciles 1,800 probe rows and reproduces the published substrate scores in every morphology/version/location group.

## Baselines

The **active-pixel centroid** computes the mean row and column of each binary stimulus mask, then assigns the nearest trained-site region. For every probe in both panels, the centroid exactly equals the stimulus coordinate. Held-out centroid region classification is 288/288 for each morphology in each panel, and the baseline recovers exact coordinates on all 288/288 held-out probes.

The **training-mask Hamming nearest-neighbor** compares each probe mask with the nine training-site masks of the same morphology and selects the nearest set. When several templates tie, this report counts the set as correct if it contains a site in the true nearest region, and reports ties explicitly. It achieves set-valued 288/288 held-out regional coverage in all four version/morphology groups. The tie rate is 288/288 for v1 cross, 0/288 for v1 square, and 126/288 for each v2.1 morphology. Thus the Hamming result is weak evidence where ties are common, especially for v1 cross.

| Panel | Morphology | Substrate held-out region | Centroid baseline | Hamming set-valued baseline | Hamming ties |
|---|---|---:|---:|---:|---:|
| v1 | Square | 288/288 | 288/288 | 288/288 | 0/288 |
| v1 | Cross | 33/288 | 288/288 | 288/288 | 288/288 |
| v2.1 | Square | 288/288 | 288/288 | 288/288 | 126/288 |
| v2.1 | Cross | 210/288 | 288/288 | 288/288 | 126/288 |

## Interpretation and next gate

The perfect centroid baseline shows that absolute retinal position is directly readable from the input pixels. These probes test whether trained WUnit fields reproduce a retinotopic map and generalize its region labels; they do not establish visual feature recognition or learning a position-invariant concept. The known training-site grid is used to score nearest-region performance, and the stimulus mask itself exposes exact coordinates.

Keep this result as a benchmark diagnostic. A stronger learning gate should add controlled input corruption or partial occlusion and compare learned-map output with centroid and mask-neighbor controls, while preserving matched labels and held-out positions. Report coverage, abstentions, wrong-region errors, exact coordinate error, training work, and inference cost. Any claim about object/shape recognition requires a separate task whose label cannot be recovered from absolute position alone.

## Artifacts

- [Analyzer](../../../evaluation/substrate_capability/analyze_vision_eye_phase0_coordinate_baselines_posthoc_v1.py)
- [Source-linked report](../../../evaluation/reports/vision_eye_phase0_coordinate_baselines_posthoc_v1_20261005.json)
- [v1 capture and analysis](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V1_RESULTS_20261005.md)
- [v2.1 capture and analysis](SUBSTRATE_VISION_EYE_PHASE0_DENSE_MAP_MORPHOLOGY_TRANSFER_V2_1_RESULTS_20261005.md)
