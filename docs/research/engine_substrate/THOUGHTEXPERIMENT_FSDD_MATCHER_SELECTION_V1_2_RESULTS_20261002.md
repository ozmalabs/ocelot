# Thoughtexperiment FSDD matcher selection v1.2 — results

## Result

This is a repaired real-data audio matcher-selection experiment on 3,000 Free Spoken Digit Dataset recordings from six speakers. It scores 200 training and 200 held-out utterances in each of three speaker-disjoint folds against the same 200-example training gallery. The three supplied native graph Terms are ordered DTW, PointSetDist, and matched-filter XCorrPeak. The corrected independent analyzer reports 9/12 gates passing. The end-to-end selection gate fails in fold 0: ordered DTW and PointSetDist tie at 169/200, and the graph selector correctly abstains. In folds 1 and 2 it uniquely selects ordered DTW from training results.

| Fold / held-out speakers | Training accuracy (DTW / PointSet / XCorr) | Selection | Held-out accuracy (DTW / PointSet / XCorr) |
|---|---:|---|---:|
| 0 / george, jackson | 84.5% / 84.5% / 75.0% | abstained on exact tie | 46.0% / 35.0% / 26.0% |
| 1 / lucas, nicolas | 89.5% / 87.0% / 82.0% | ordered DTW | 43.0% / 26.0% / 32.0% |
| 2 / theo, yweweler | 83.5% / 82.0% / 71.5% | ordered DTW | 64.5% / 55.0% / 49.5% |

Ordered DTW averages 51.2% over all 600 held-out queries, PointSetDist 38.7%, and XCorrPeak 35.8%, against 10% chance. In the two folds with a selected Term, ordered DTW is the held-out best of the three in both (53.8% pooled across 400 queries, with zero regret). Fold 0 has no selected system, so selection accuracy and selected-system regret are not applicable there; its held-out hindsight best is 46%. These speaker-level results are descriptive across only six speakers and three fixed folds, not a population estimate.

All three Terms used identical query IDs and gallery digests. The analysis verified all 600×200 query-gallery comparison cells per phase, valid digit predictions, the six-speaker partition, no held-out identity in frozen orders, graph-evidence counts, correct unique selection where a unique maximum existed, tie/all-wrong abstention controls, branch isolation, and compact residual return. The three folds returned one residual each; candidate/evidence nodes stayed on the experiment branches. The 12-gate report marks three end-to-end conditions false: a unique maximum was not selected in every fold, a selected system therefore does not exceed chance in every fold, and selected-system regret cannot meet the per-fold bound when selection abstains. All three are capability outcomes, not integrity failures.

## Cost profile

The full three-matcher training pass makes 600 native Term calls per fold and 120,000 query-gallery comparisons. Held-out scoring also makes 600 Term calls and 120,000 comparisons per fold. Across these 10-way tasks, the median fold's training feature preparation took 769 ms; held-out feature preparation took 846 ms. Held-out gallery construction took 84–94 ms per Term, and matcher wall times were 516–1,075 ms per Term. Training graph selection took 4.9–9.8 ms; branch fork took 7.7–16.7 µs; residual return took 0.16–0.27 ms. Costs are local measurements of this harness and graph shape, not general CPU scaling evidence.

## Capture history and limitations

The original v1 score capture is retained as an invalid pilot: it omitted the gallery during held-out scoring, so all predictions were `None`. The v1.1 attempt retained a fresh training order but failed before reading held-out audio due to a `Path` indexing error. The v1.2 preregistration explicitly discloses both, uses unseen held-out recording indices 10–19, and repairs the gallery loading path. The v1.2 lock fixes the runner, analyzer, protocol, adapter/engine sources, loaded native binary, and hashes for all 3,000 WAVs. Frozen orders omit held-out recording identities; the corrected score stage loads the frozen training gallery and the new held-out queries only. The locked v1.2 analyzer represented an abstained fold as zero selected accuracy and numeric regret; a post-capture v1.3 analysis correction records both as not applicable for that fold. The 9/12 gate count and three failed selection gates are unchanged; the correction changes reporting semantics only ([analysis amendment](THOUGHTEXPERIMENT_FSDD_MATCHER_SELECTION_V1_3_ANALYSIS_AMENDMENT_20261002.md)).

The experiment establishes substrate-owned selection among three provided Terms under graph-resident evidence aggregation, including a useful abstention boundary and transfer of two selections to held-out speakers. It does not establish autonomous matcher invention, broad speech recognition, speaker-population generalization, or self-improvement. Training candidates, Terms, labels, folds, features, and evaluation are supplied by the harness. The two successful transfer folds reuse the same corpus and one selected matcher family.

## Reproduction artifacts

- [v1.2 preregistration](THOUGHTEXPERIMENT_FSDD_MATCHER_SELECTION_V1_2_PREREG_20261002.md)
- [v1.2 runner](../../../evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1_2.py)
- [v1.2 lock](../../../evaluation/substrate_capability/thoughtexperiment_fsdd_matcher_selection_v1_2_lock_20261002.json)
- [frozen training orders](../../../evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_2_orders_20261002.json)
- [held-out scores](../../../evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_2_scores_20261002.json)
- [independent analysis](../../../evaluation/reports/thoughtexperiment_fsdd_matcher_selection_v1_3_analysis_20261002.json)
- [post-capture analyzer correction](../../../evaluation/substrate_capability/analyze_thoughtexperiment_fsdd_matcher_selection_v1_3.py)
