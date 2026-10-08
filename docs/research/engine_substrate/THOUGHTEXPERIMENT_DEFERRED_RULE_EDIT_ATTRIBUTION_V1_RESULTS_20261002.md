# Thoughtexperiment deferred RuleEdit attribution v1 results — failed fixture

The source-locked three-worker capture preserved a useful negative result. In every worker the producer queued one deferred `SetRuleClause`, but the drain refused it: the fixture supplied a bare Boolean as the proposed `where` clause, while the rule patch parser expects a serialized Term tree. The deferred event was correctly attributed to `edit_target_clause` and marked `progressed=false`; the target rule's exported definition and graph remained unchanged. Ordinary, attributed, and exact-snapshot reports agreed, but the intended edit did not occur, so the capability gate failed.

This capture is retained as the original v1 record. The corrected v1.1 fixture supplies the serialized `Lit(true)` clause and is independently locked and analyzed. No claim of successful RuleEdit attribution or self-modification should be based on v1.

See [the v1 preregistration](THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_ATTRIBUTION_V1_PREREG_20261002.md), [raw capture](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_attribution_v1_20261002.json), and [failed analysis](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_attribution_v1_analysis_20261002.json).
