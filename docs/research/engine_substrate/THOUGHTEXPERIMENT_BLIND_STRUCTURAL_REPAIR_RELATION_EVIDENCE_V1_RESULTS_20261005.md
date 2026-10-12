# Blind structural repair relation evidence v1 results

The source-locked capture and independent analyzer pass across three fresh
workers. Worker candidate IDs, counts, relation signatures, and target-in-pool
decisions agree; no candidate pool is truncated and accounting reconciles.

Adding relation signatures derived from training graph neighborhoods places
the missing-edge target in the proposal pool. Paired exact target proposal
coverage rises from v2's 4/5 (80%) to 5/5 (100%) on the same five authored
rule pairs. Six relation-extension candidates are added in total: two in the
dropped-edge case and one distractor extension in each other case. Total pool
size is 46 with a median of 11. Median enumerator time is 0.820 ms in this
capture; this tiny-panel value is descriptive and should not be compared as a
stable throughput estimate against earlier runs.

The training graph neighborhood contains both `has_context` and `has_tag`
edges at each output node. In the four cases where the relation endpoint is
already bound, `has_tag` yields one extra extension candidate. In the
dropped-edge case, both relations lead to unbound nodes, yielding two
candidates; alpha-equivalent canonicalization recognizes the `has_context`
extension as the target. This makes the proposal inclusion result interpretable
while also exposing the selection problem: the generator offers a relevant
relation alongside a distractor and has no evidence here that can rank them.

This is controlled graph-evidence-to-proposal translation on the same
authored panel, not an independent generalization result. The relation
evidence is harness supplied; candidate ranking, behavioral rehearsal,
held-out utility, canary, and commit were not measured. The next gate must
provide actual training examples, measure whether observed relations improve
behavior on a disjoint canary, and include no-repair and irrelevant-relation
controls so the graph selector must decide among the structural extensions.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_RELATION_EVIDENCE_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_blind_structural_repair_relation_evidence_v1.py)
- [Rule fixture](../../../evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json)
- [Graph neighborhood fixture](../../../evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_lock_20261005.json)
- [Raw capture](../../../evaluation/reports/blind_structural_repair_relation_evidence_v1_20261005.json)
- [Analysis](../../../evaluation/reports/blind_structural_repair_relation_evidence_v1_analysis_20261005.json)
