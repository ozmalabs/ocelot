# Accepted proposition polar-conflict v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_ACCEPTED_PROPOSITION_POLAR_CONFLICT_V1_PREREG_20261003.md)  
Runner: [`accepted_proposition_polar_conflict_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_polar_conflict_v1.py)  
Lock: [`accepted_proposition_polar_conflict_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_polar_conflict_v1_lock_20261003.json)  
Raw capture: [`accepted_proposition_polar_conflict_v1_raw_20261003.json`](../../../evaluation/reports/accepted_proposition_polar_conflict_v1_raw_20261003.json)

## Result

Integrity passed: all 15 graph instances completed and all nine source/runtime hashes remained stable. The two unique-claim controls passed 6/6 (affirmed claim -> `yes`; negated claim -> `no`). The retracted-conflict control passed 3/3: the retracted negative claim was excluded and the remaining accepted affirmative claim produced `yes`.

Both accepted contradictory claims were individually linked by `PolarRelationSupportEvidence`, but each graph produced exactly one `yes` plan. This happened in all 3/3 `affirmed_first` and all 3/3 `negated_first` graphs. The result was order-invariant across these insertions but failed the preregistered conflict-abstention oracle in 6/6 graphs. It appears the affirmative plan rule wins the competing plan mint; no explicit conflict outcome was emitted.

| Condition | Behavior result | Plans |
|---|---:|---|
| Unique accepted affirmed | 3/3 | `yes` |
| Unique accepted negated | 3/3 | `no` |
| Two accepted contradictory claims, affirmed inserted first | 0/3 conflict gates | `yes` each |
| Same conflict, negated inserted first | 0/3 conflict gates | `yes` each |
| Accepted affirmed + retracted negated | 3/3 | `yes` |

The distinction is useful: native support correctly records both conflicting sources, and retracted evidence is excluded, but final answer selection is not conflict-aware. Stable output under two construction orders does not make the answer correct; it is systematically affirmative for this fixture. The rule harness does not establish broader graph-order independence.

## Next gate

Before extending proposition recall to wh-questions, add a preregistered conflict audit for duplicate claims, opposite polarity, commitment changes, and more than two sources. A future rule design needs an explicit conflict/abstention outcome with precedence over both affirmative and negative answer-plan rules. Then retest lifecycle-applied uptake and source-event lineage; this panel manually supplied accepted statuses and did not measure trusted uptake.
