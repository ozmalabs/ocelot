# Thoughtexperiment deferred `SetRuleClause` diagnosis v1 results

## Result

The source-locked capture passed all independent analysis gates: three workers had distinct PIDs, twelve isolated runs had distinct PIDs, all source/native hashes matched the lock, and every primary graph and rule revision remained unchanged. Each causal fixture produced exactly one deferred `repair_apply_rule_clause` event, attributed queue entry 1 to effect index 1, and recorded one committed `where` edit on `target_rule` with revision 0→1 and a changed content hash.

The held-out probe verifies causal necessity in this fixture: omitting effect 1 lets the probe marker fire; retaining it commits `Lit(false)` and suppresses the marker. Target trace and rule-change receipt each select effect 1 and require one omission branch. Blind effect order and pre-state rematching both also find effect 1, requiring two branches. In the no-cause control (`applied=1`), rematching, target trace, and rule-change receipt abstain; blind order still explores its four candidates but none produces a necessity witness.

| Policy | Isolated runs | Branch attempts | Median wall time |
|---|---:|---:|---:|
| Blind effect order | 3 | 2 | 1.429 ms |
| Pre-state rematch | 3 | 2 | 0.972 ms |
| Deferred target trace | 3 | 1 | 0.788 ms |
| Deferred rule-change receipt | 3 | 1 | 0.653 ms |

These times cover the measured policy path and branch loop in a tiny authored fixture; they do not include process startup, source locking, seed authoring, or general workload setup and are not a speedup claim. The capture establishes exact producer-to-queue-to-target-rule-change attribution for this one production seed rule and one uniquely sourced edit. It does not test competing edits, ambiguity, queue reordering, other rule-edit families, natural repair frequency, learned diagnosis, or general self-improvement. The control policy’s abstention and the branch oracle are harness-defined.

## Reproduction artifacts

- Preregistration: [protocol](THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_DIAGNOSIS_V1_PREREG_20261005.md)
- Runner: [thoughtexperiment_deferred_rule_edit_diagnosis_v1.py](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_diagnosis_v1.py)
- Analyzer: [analyze_thoughtexperiment_deferred_rule_edit_diagnosis_v1.py](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_rule_edit_diagnosis_v1.py)
- Source lock: [lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_rule_edit_diagnosis_v1_lock_20261005.json)
- Capture: [capture](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_diagnosis_v1_20261005.json)
- Analysis: [analysis](../../../evaluation/reports/thoughtexperiment_deferred_rule_edit_diagnosis_v1_analysis_20261005.json)
