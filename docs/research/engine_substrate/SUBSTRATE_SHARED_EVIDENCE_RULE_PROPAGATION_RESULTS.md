# Shared evidence native-rule propagation results

## v1.2 result

The locked 36-worker run passed all gates. At N=2/4/8, native rules read shared `BenchEvidence` attributes and write two frame-local `BenchFrameLocalState` nodes. Across activation, active-value change, and retraction, the full and round-robin scoped arms reached their terminal conditions and produced identical, independently expected output values in all 12 pairs. The independent analyzer verified locked source hashes, every checkpoint, and the intentional omission signature.

| Frames | Evidence boundaries | Full candidate pairs | Scoped candidate pairs | Full Term evaluations | Scoped Term evaluations | Full median total wall | Scoped median total wall |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 0 | 0 | 0 | 0 | 0.068 ms | 0.035 ms |
| 2 | 1 | 20 | 56 | 176 | 472 | 0.123 ms | 0.077 ms |
| 4 | 3 | 60 | 360 | 528 | 3,072 | 0.131 ms | 0.171 ms |
| 8 | 7 | 140 | 1,736 | 1,232 | 14,896 | 0.157 ms | 0.518 ms |

The omitted-boundary arm is a required sensitivity control, not a competing valid scheduler. Omitting both scopes incident to boundary 0 left exactly its two outputs stale at activation for every N>1; every other output matched, and all outputs returned to the oracle values after later value change/retraction. This demonstrates the input requires both incident scope visits under this membership layout. It does not establish automatic engine notification: the runner supplies the scope visitation order.

Scoped operation count and timing rise faster than full closure in this small chain. At N=8 the scoped arm records 12.4× the candidate enumerations, 12.1× the Term evaluations, and about 3.3× total wall time. Treat these as descriptive measurements for this two-rule family and fixed N≤8 graph, not an asymptotic law or a natural workload estimate. N=1 is an empty-boundary control and is excluded from ratios.

## Preserved harness corrections

The v1 raw report is retained: its coordinator called full-graph `run_rules_report` after scoped settlement, which repaired the omitted state and invalidated the negative control. V1.1 removed that probe but omitted only one endpoint scope; because `run_rules_scoped` admits bindings that touch any owned node, the other endpoint's scope could still fire the shared binding. V1.2 omits both incident scopes and checks the exact two-state stale signature. Each version has its own locked protocol/runner and raw report; no failed result was overwritten.

## Limits and next work

This validates two benchmark-authored native rules, one shared input per adjacent frame pair, fixed topology, caller-driven round-robin visitation, and an explicit active-bit retraction. It does not prove general scheduler completeness, dynamic edge insertion/deletion behavior, arbitrary interacting rules, or natural frame locality. Next expand to independently generated topologies and fan-out patterns, then test boundary graph mutation and compare any event-notification mechanism against full closure while retaining omitted-notification controls.

Artifacts: [v1.2 protocol amendment](SUBSTRATE_SHARED_EVIDENCE_RULE_PROPAGATION_V1_2_AMENDMENT_20260925.md), [runner](../../../scripts/substrate_shared_evidence_rule_propagation_v1_2.py), [independent audit](../../../scripts/analyze_substrate_shared_evidence_rule_propagation_v1_2.py), [raw report](../../../evaluation/reports/substrate_shared_evidence_rule_propagation_v1_2_20260925.json), and [lock](../../../evaluation/substrate_capability/shared_evidence_rule_propagation_v1_2_lock_20260925.json). Preserved earlier versions: [v1 preregistration](SUBSTRATE_SHARED_EVIDENCE_RULE_PROPAGATION_PREREG_20260925.md), [v1 raw report](../../../evaluation/reports/substrate_shared_evidence_rule_propagation_20260925.json), [v1.1 amendment](SUBSTRATE_SHARED_EVIDENCE_RULE_PROPAGATION_V1_1_AMENDMENT_20260925.md), and [v1.1 raw report](../../../evaluation/reports/substrate_shared_evidence_rule_propagation_v1_1_20260925.json).
