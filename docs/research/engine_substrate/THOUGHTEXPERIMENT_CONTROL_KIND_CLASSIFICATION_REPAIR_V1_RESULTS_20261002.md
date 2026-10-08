# Control-kind classification repair v1 — results

**Independent review: 14/14 gates pass.** Three fresh source/native-locked workers generated the same six unique candidate descriptors. The original `classify_kind_family` rule correctly classified all four names; the comparison-flipped fault failed all four. Every candidate was evaluated on both training names and both disjoint held-out names in separate substrate instances.

| Candidate | Training cases correct (2) | Held-out cases correct (2), each worker |
|---|---:|---:|
| `flip_comparison` | 2/2 | 2/2 |
| `add_match_guard(control)` | 0/2 | 0/2 |
| `swap_term_leaf:family->name_lc` | 0/2 | 0/2 |
| `swap_term_leaf:family->spec` | 0/2 | 0/2 |
| `swap_term_leaf:family->word` | 0/2 | 0/2 |
| `swap_term_leaf:name_lc->family` | 0/2 | 0/2 |

This is a fourth independently task-shaped candidate-utility context, distinct from shape-axis deduplication, recurrence-offer idempotence, and grid-navigation polarity repair. It shows that a graph-authored lexical classifier can be restored by one candidate from a fixed generated set and transfer across held-out names. The task is a small authored lexical family: expected labels derive from the supplied signal table, and the fault operator is explicitly known to the fixture author. It does not establish natural language coverage, autonomous diagnosis, outcome-conditioned ranking in this family, or general self-improvement.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CONTROL_KIND_CLASSIFICATION_REPAIR_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_control_kind_classification_repair_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json)
- [Independent review](../../../evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_analysis_review_20261002.json)
