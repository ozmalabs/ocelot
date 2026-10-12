# Thoughtexperiment Omniglot matcher selection v1.1 — results

**Outcome: 12/12 corrected independent analysis checks pass.** Across three workers, the graph Term selected `pointset` as the unique training maximum every time. The training episodes use the Omniglot background alphabet split; evaluation episodes were generated only after orders froze and use the disjoint evaluation split. The orders artifact contains no evaluation specs, labels, or predictions. Tie and all-wrong controls abstained in all six cases; CandidateProposal/CandidateEvidence nodes remained in the snapshot branch, and one compact ExperimentResidual returned to primary per worker.

Each worker has 40 episodes, 20 ways, and 800 query labels per matcher per split. Training PointSetDist accuracy was 68.6%, 71.4%, and 67.0%. On the disjoint evaluation alphabets, the selected matcher scored 62.5%, 66.8%, and 60.4%; it tied the held-out hindsight-best matcher in every worker, with zero observed regret. Across all workers and 20 evaluation alphabets, PointSetDist scored 63.2% (alphabet-cluster bootstrap 95% interval 58.0–68.6%), ordered DTW 52.0% (48.0–55.8%), and deformable matching 51.0% (44.7–57.3%), against 5% chance. The interval resamples the 20 alphabet clusters and is descriptive for this fixed dataset, not a population guarantee.

| Measure | Median per worker | Range |
|---|---:|---:|
| Background feature preparation | 770 ms | 741–873 ms |
| Evaluation feature preparation | 817 ms | 779–862 ms |
| Snapshot creation | 30 µs | 28–73 µs |
| Selection branch fork | 8.5 µs | 8.0–19.1 µs |
| Graph evidence selection | 25.1 ms | 21.5–30.1 ms |
| Residual return | 0.086 ms | 0.081–0.094 ms |
| Prediction Term evaluations | 14,400 total | 7,200 per split |

The result supports cross-split selection among three supplied matchers using real handwritten character data. It does not show autonomous matcher invention or general vision. The 20 alphabet clusters and three worker seeds bound uncertainty. The 12/12 analysis uses a post-capture analyzer correction: the frozen analyzer expected held-out specs in orders, contrary to the sealed-order design; v1.2 reads them from the later scores file and verifies their absence from orders. The v1 pilot is separately retained as a diagnostic capture because it preloaded evaluation features during training and omitted fork timing ([pilot amendment](THOUGHTEXPERIMENT_OMNIGLOT_MATCHER_SELECTION_V1_AMENDMENT_20261002.md), [analysis amendment](THOUGHTEXPERIMENT_OMNIGLOT_MATCHER_SELECTION_V1_1_ANALYSIS_AMENDMENT_20261002.md)).

## Artifacts

- [Preregistration v1.1](THOUGHTEXPERIMENT_OMNIGLOT_MATCHER_SELECTION_V1_1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_omniglot_matcher_selection_v1_1.py)
- [Source/native/data lock](../../../evaluation/substrate_capability/thoughtexperiment_omniglot_matcher_selection_v1_1_lock_20261002.json)
- [Training orders](../../../evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_1_scores_20261002.json)
- [Frozen analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_omniglot_matcher_selection_v1_1.py)
- [Corrected analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_omniglot_matcher_selection_v1_2.py)
- [Analysis](../../../evaluation/reports/thoughtexperiment_omniglot_matcher_selection_v1_2_analysis_20261002.json)
