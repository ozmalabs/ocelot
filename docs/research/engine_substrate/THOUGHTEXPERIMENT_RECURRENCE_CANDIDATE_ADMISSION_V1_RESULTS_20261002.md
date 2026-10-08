# Recurrence candidate-admission audit v1 — results

**Independent review: 12/12 gates pass.** Three fresh source/native-locked workers produced the same eight unique candidate descriptors from the unchanged `_default_candidates` generator. Every candidate was scored on a fresh training episode and a disjoint fresh held-out episode; both episodes required one offer for each of two due candidates and zero rule work at fixed point.

| Candidate | Training pass | Held-out pass (3 workers) |
|---|---:|---:|
| `dedup_identity_fix` | 3/3 | 3/3 |
| `episode_scoped_offer_guard` | 0/3 | 0/3 |
| `drop_match_edge` | 0/3 | 0/3 |
| `add_match_guard(control)` | 0/3 | 0/3 |
| `swap_term_leaf:capability_key->latest_segment_ordinal` | 0/3 | 0/3 |
| `swap_term_leaf:capability_key->persistence` | 0/3 | 0/3 |
| `swap_term_leaf:capability_key->structural_signature` | 0/3 | 0/3 |
| `swap_term_leaf:latest_segment_ordinal->capability_key` | 0/3 | 0/3 |

This resolves the earlier candidate-count ambiguity: the v2 transfer study did enumerate eight unchanged-generator variants, but it rehearsed only the first two before stopping on success. The new audit evaluates the complete candidate surface and confirms stable descriptors, a successful repair, and seven unsuccessful alternatives on held-out cases. Recurrence therefore satisfies the task-family candidate-diversity and outcome-separation checks. This does not make its one successful candidate family broad, show ranker utility, or provide full experiment cost. A fourth independent task family and the confirmatory blinded panel remain outstanding.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_ADMISSION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_admission_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json)
- [Independent review](../../../evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_analysis_review_20261002.json)
