# Zero-aware query and finite behavioral-equivalence v1 results

## Result

This source-locked follow-up reuses the same 25 training panels and candidate
Terms as primitive-menu help v1.1. It replays the original nonzero query
domain and pairs it with new selection/challenge pools containing zero-valued
and boundary cases. Independent analysis passes all seven gates, including
exact replay of the old-domain v1.1 entropy transcript, disjoint query/training/
holdout schedules, query transitions, finite behavior classes, rescore of all
survivors on 6,560 zero-inclusive fractional cases, and source binding.

| Task | Original median labels / abstentions | Zero-aware median labels / abstentions | Exact survivor sets (original → zero-aware) | Help calls (original → zero-aware) |
|---|---:|---:|---:|---:|
| Additive | 2 / 0 | 2 / 0 | 5/5 → 5/5 | 0 → 0 |
| Product | 2 / 0 | 2 / 0 | 5/5 → 5/5 | 0 → 0 |
| Ordering | 3 / 0 | 4 / 0 | 5/5 → 5/5 | 0 → 0 |
| Inequality | 1 / 5 | 4 / 0 | 0/5 → 5/5 | 5 → 0 |
| Opposition | 1 / 5 | 1 / 5 | 5/5 → 5/5 | 5 → 5 |

“Exact survivor set” means every remaining candidate in that panel is exact on
the finite 6,560-case holdout. The zero-aware inputs remove the inequality
alias: the original candidate set had one exact and one false survivor in each
panel, indistinguishable over its nonzero probes. Zero cases expose their
different predictions; entropy selection resolves all five panels, at a cost
of three additional median labels. For opposition, four syntactically distinct
survivors remain in each panel, but form one behavioral class over the
selection/challenge domain and all are exact on the expanded holdout.

The current help trigger still requests five hints on opposition in both
domains. The captured behavior classes show why a finite class return could
avoid this spend, but the experiment did not deploy a downstream consumer that
acts on class return; report it as a measured decision opportunity, not an
implemented policy benefit. Conversely, inequality's original-domain class
looked behaviorally singular while containing a false model on the expanded
holdout. A finite equivalence class is therefore only as useful as the probe
domain that defines it.

## Interpretation and limits

This is evidence that zero-aware queries can distinguish one concrete
nonzero-domain alias and that finite behavioral grouping separates that case
from harmless syntactic multiplicity on these tasks. The test reuses the same
authored task families and candidate Terms as v1.1; it does not establish
natural-task prevalence, universal semantic equivalence, or a generally
calibrated help policy. The teacher remains a harness callback. Holdout labels
are used only after policy execution.

Next implement a policy comparison that chooses among (1) querying a
zero-aware challenge domain, (2) returning a finite equivalence class with its
probe coverage attached, and (3) requesting external help. Repeat with
independently sampled and structurally distinct task families, include boundary
and zero patterns without target-specific leakage, and measure harmful
ambiguity, unnecessary help, labels, synthesis work, wall/CPU cost, and
coverage-qualified generalization.

## Reproduction artifacts

- [Preregistration](PRIMITIVE_SEMANTIC_EQUIVALENCE_V1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/primitive_semantic_equivalence_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_primitive_semantic_equivalence_v1.py)
- [Source and schedule lock](../../../evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json)
- [Capture](../../../evaluation/reports/primitive_semantic_equivalence_v1_20261003.json)
- [Independent analysis](../../../evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json)
