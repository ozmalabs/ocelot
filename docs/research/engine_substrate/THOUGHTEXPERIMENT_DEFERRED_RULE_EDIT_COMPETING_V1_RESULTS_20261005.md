# Thoughtexperiment deferred competing rule edits v1 results

All preregistered gates pass in three source-locked workers and nine isolated runs (three per scenario). The queue drains in producer order, preserves each producer's effect index, and reports a separate target-rule receipt for each queued edit. Both successful edits commit sequentially, advancing target revision 0→1→2. The primary graph, rules, and revisions stay unchanged during all observation and omission branches.

| Scenario | Deferred events | Rule changes | Held-out omission outcomes | Result |
|---|---:|---:|---|---|
| Competing: A writes true, B writes false | 2 | 2 commits, revisions 1 then 2 | Omit A: marker absent; omit B: marker present | B is uniquely necessary for the final behavior |
| Duplicate: A and B both write false | 2 | 2 commits, revisions 1 then 2 | Omit either: marker absent | Neither edit is individually necessary |
| Ambiguous target: two active rules share the target name | 2 | 0 commits | Omit either producer edit: marker present | Both writes are refused; no unique edit to attribute |

The output includes explicit source origins and committed change receipts for successful writes. In the ambiguous-name case, producer origins remain visible and the absence of receipts, unchanged target revision, non-progressed events, and held-out branches jointly indicate refusal. This refusal is inferred from the event and graph state; the deferred receipt schema does not yet carry an explicit ambiguity code.

Median isolated policy-path times were 0.859 ms for competing writes, 1.092 ms for duplicate writes, and 0.998 ms for ambiguous targets. These tiny authored-fixture values are exploratory and exclude process startup. This is evidence that the thoughtexperiment harness can preserve and evaluate multiple deferred sources, detect non-unique necessity, and abstain when name resolution is ambiguous. It does not show that the substrate autonomously diagnoses a natural failure or chooses a repair.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_COMPETING_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_competing_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_competing_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_competing_v1_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_competing_v1_20261005.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_competing_v1_analysis_20261005.json)
