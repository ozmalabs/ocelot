# Omniglot background-alphabet one-shot transfer v1 results (2026-09-29)

## Integrity and task

A fresh source/runtime/data-locked run covers 100 20-way episodes on the Omniglot background split: 2,000 labeled queries per recognizer, three fixed graph-Term systems, and one uniform-random control. Of 30 background alphabets, 26 have at least 20 classes and enter the sampler. All 20 evaluation alphabets are disjoint from the 30 background alphabets. The analyzer passes all 7 gates: complete paired matrix; lock agreement; current source/runtime/data and reference-panel match; explicit split disjointness; in-run source stability; episode/writer/shared-input integrity; and independent score reconstruction.

## Accuracy and comparison

| Recognizer | Correct | Accuracy | 95% alphabet-cluster interval | Chance |
|---|---:|---:|---:|---:|
| Ordered DTW (`DtwTo`) | 1,146 / 2,000 | 57.30% | 49.65–63.61% | 5% |
| Point-set distance (`PointSetDist`) | 1,340 / 2,000 | 67.00% | 57.00–75.40% | 5% |
| Deformable fit (`DeformDist`) | 1,039 / 2,000 | 51.95% | 42.22–60.82% | 5% |
| Uniform-random control | 88–111 / 2,000 | 4.40–5.55% | — | 5% |

Point-set distance remains the strongest method on this split: it leads ordered DTW by 9.70 percentage points (paired alphabet-cluster interval 4.06–15.19 points) and deformable fit by 15.05 points (11.17–19.62 points).

The prior evaluation-split panel scored PointSetDist at 66.8%; the background panel scores 67.0%. An exploratory unpaired alphabet-cluster bootstrap gives a background-minus-evaluation difference of +0.20 points, with a wide 95% interval from −10.81 to +9.50 points. The same exploratory intervals for DTW and deformable fit are −4.16 to +12.16 and −13.31 to +8.37 points. These cross-split comparisons were calculated after each panel's analysis and are descriptive rather than preregistered confirmatory contrasts. They do not establish equivalence or rule out moderate split effects.

## Cost and limits

Median per-episode wall/CPU time is 12.04/12.03 ms for ordered DTW, 16.43/16.39 ms for point-set distance, and 16.23/16.23 ms for deformable fit. Shared preparation took 1.43 s for 3,533 trajectories; the full run took 5.82 s wall / 5.81 s CPU including source-stability hashing. Peak RSS was about 64 MB.

This is positive evidence of one-shot recognition on a disjoint alphabet set with no model training. It demonstrates application of existing graph Terms through the Omniglot host adapter; it does not establish learning of new visual concepts, adaptation to a task, semantic scene recognition, or broad cross-domain capability. The two panels share one dataset family and the same adapter, writer protocol, and frozen Terms.

## Next work

Measure transfer on a separately sourced task family. For Omniglot, preregister an exemplar-count sweep and direct native Term/operator work counters; keep task accuracy, candidate count, trajectory cost, and host-side preprocessing distinct. Preserve alphabet-clustered uncertainty and acquire more independent alphabet families before claiming small performance differences between splits.

## Reproduction artifacts

- [v1 preregistration](SUBSTRATE_OMNIGLOT_ONE_SHOT_BACKGROUND_V1_PREREG_20260929.md)
- [Capture runner](../../../scripts/substrate_omniglot_one_shot_background_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_omniglot_one_shot_background_v1.py)
- [Raw capture](../../../evaluation/reports/omniglot_one_shot_background_v1_20260929_raw.jsonl)
- [Analysis](../../../evaluation/reports/omniglot_one_shot_background_v1_20260929_analysis.json)
- [Source/runtime/dataset/reference-panel lock](../../../evaluation/substrate_capability/omniglot_one_shot_background_v1_20260929_lock.json)
- [Exploratory cross-split comparison](../../../evaluation/reports/omniglot_one_shot_alphabet_split_comparison_v1_20260929.json) and [reproduction script](../../../scripts/compare_omniglot_one_shot_alphabet_splits_v1.py)
- [Evaluation-split v1.2 result](SUBSTRATE_OMNIGLOT_ONE_SHOT_CURRENT_V1_2_RESULTS_20260929.md)
