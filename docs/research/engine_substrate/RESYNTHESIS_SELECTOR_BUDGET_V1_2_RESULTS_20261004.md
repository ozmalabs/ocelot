# Resynthesis selector-budget v1.2 — results

The v1.2 source-locked replay passes all five independent checks: provenance,
20-panel pairing, active-selector transcript replay, query membership and
training/holdout disjointness, and holdout outcome recomputation. Earlier v1 and
v1.1 captures are diagnostic because their analyzers respectively failed to
skip untriggered panels and treated the registered selection pool as forbidden.

The study continues selection on the fixed search candidate pools from the
six triggered panels, using the remaining preregistered selection order. At
caps 8, 16, 32, and full pool, both arms have identical outcomes: the
no-residual control accepts five exact candidates and requests help on one;
the one-residual arm also accepts five exact candidates and requests help on
one. Neither makes a false acceptance. Median cumulative labels are four for
the control and three for the residual arm. In the unresolved absolute-value
panel, both arms stop after four labels with the same three surviving Terms;
the selector cannot find a disagreement on any remaining pool input. No
additional query is issued, so larger label caps do not affect the outcome.

This isolates a query-pool discrimination limit rather than a binding label
cap: the remaining rows do not split the three candidates. It does not prove
those candidates equivalent on the task domain, nor establish that additional
oracle queries from a better proposal policy would be useless. Search and
candidate identities are inherited from v1.2; this extension performs no new
synthesis. Next measure candidate-directed query construction on the ambiguous
panel and test whether it separates the survivors on new inputs, with query
and candidate-evaluation costs charged. The assay remains a six-panel numeric
study, not a general inference claim.

Artifacts: [preregistration](RESYNTHESIS_SELECTOR_BUDGET_V1_PREREG_20261004.md), [v1.1 amendment](RESYNTHESIS_SELECTOR_BUDGET_V1_1_AMENDMENT_20261004.md), [v1.2 amendment](RESYNTHESIS_SELECTOR_BUDGET_V1_2_AMENDMENT_20261004.md), [runner](../../../evaluation/substrate_capability/resynthesis_selector_budget_v1_2.py), [independent analyzer](../../../evaluation/substrate_capability/analyze_resynthesis_selector_budget_v1_2.py), [source lock](../../../evaluation/substrate_capability/resynthesis_selector_budget_v1_2_lock_20261004.json), [capture](../../../evaluation/reports/resynthesis_selector_budget_v1_2_20261004.json), and [analysis](../../../evaluation/reports/resynthesis_selector_budget_v1_2_analysis_20261004.json).
