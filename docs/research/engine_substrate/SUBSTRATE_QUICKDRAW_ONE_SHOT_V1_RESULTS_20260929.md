# QuickDraw one-shot shape recognition v1 results

## Integrity and task

The locked panel completed 100 episodes, each with eight fixed single-stroke shape classes, one support drawing per class, and five disjoint queries per class. The three frozen native graph-Term recognizers share the same 40 queries per episode, for 4,000 queries per method. The analyzer passes all six gates: one header/footer, complete 300-worker matrix, locked and current source/data agreement, in-run source stability, valid episode/worker contents and independently reconstructed scores, and exact shared episodes across systems.

The local files contain 1,168–3,377 valid drawings per class; one malformed truncated line is skipped in each file. The single-stroke filter retains 780–2,969 per class (10,935 total). Feature preparation takes 1.39 s wall / 1.39 s CPU. The full capture takes 4.76 s wall and 4.75 s CPU; peak process RSS is about 159 MiB.

## Recognition performance

| Recognizer | Correct | Accuracy | 95% class-cluster interval | Chance |
|---|---:|---:|---:|---:|
| Ordered DTW (`DtwTo`) | 1,483 / 4,000 | 37.08% | 30.95–43.23% | 12.5% |
| Point-set (`PointSetDist`) | 1,828 / 4,000 | 45.70% | 33.90–57.93% | 12.5% |
| Deformable (`DeformDist`) | 1,436 / 4,000 | 35.90% | 25.12–47.30% | 12.5% |
| Uniform-random control | 508–517 / 4,000 | 12.70–12.93% | — | 12.5% |

Point-set accuracy is above chance for this fixed eight-class panel. It leads deformable fit by 9.80 percentage points (paired class-cluster interval 3.50–17.28 points). Its 8.63-point lead over ordered DTW is less certain (−1.18 to 20.00 points). All methods are substantially below the Omniglot panel's corresponding scores; the protocols, class sets, and data sources differ, so that cross-panel gap is descriptive rather than a controlled domain comparison.

Median worker time per 40-query episode is 12.52 ms for DTW, 16.30 ms for point-set, and 15.83 ms for deformable fit. The worker time includes graph setup and query evaluation. Dataset parsing and feature extraction are reported separately.

## Limits

This is an independent task family for applying held recognition structure. It is not novel-class learning: every episode uses the same eight class labels, each supplied with a support exemplar. The local QuickDraw records have drawing IDs but no contributor IDs, so the split is not writer-disjoint. The one-stroke restriction excludes much of the retained data for some classes, especially hexagon and octagon. The evaluated route includes Python file parsing and trajectory conditioning, then graph-Term scoring in the native substrate; it is not end-to-end image perception. Class-cluster uncertainty spans only eight classes. These limits preclude a population-level QuickDraw or general-vision claim.

The result advances the task-family coverage beyond Omniglot, but does not close that domain's higher One-shot accuracy or establish semantic vision. The next visual capability gate should use writer/creator-separated data with independent task labels, then measure held-out class combinations and acquisition/application cost.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_QUICKDRAW_ONE_SHOT_V1_PREREG_20260929.md)
- [Runner](../../../scripts/substrate_quickdraw_one_shot_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_quickdraw_one_shot_v1.py)
- [Raw capture](../../../evaluation/reports/quickdraw_one_shot_v1_20260929_raw.jsonl)
- [Analysis](../../../evaluation/reports/quickdraw_one_shot_v1_20260929_analysis.json)
- [Source/runtime/data lock](../../../evaluation/substrate_capability/quickdraw_one_shot_v1_20260929_lock.json)
- [Capability and tractability plan](SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md)
