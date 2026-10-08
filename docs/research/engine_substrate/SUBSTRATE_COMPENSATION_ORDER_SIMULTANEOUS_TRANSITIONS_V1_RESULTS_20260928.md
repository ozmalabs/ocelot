# Compensation order and simultaneous transition probe v1 — results

All seven gates pass in three fresh workers across four cells each. Both compensation representations produce the preregistered states in every phase and under both rule insertion orders:

| Phase | Frame 0 | Frame 1 | Frame 2 |
|---|---|---|---|
| Initial r0 | negative | negative | negative |
| Establish r1 | positive | negative | negative |
| Simultaneous update | negative | positive | negative |

Final projections are identical across `positive_first` and `compensator_first` for both `set_attr_if_different` compensation and `del_edge` retraction, and replicate exactly across workers. This is evidence that explicit compensators work for these independent, mutually exclusive predicates, including simultaneous opposite transitions.

Callback work is insertion-order-sensitive even when outputs are not. In the initial phase, compensating-attribute arms make 12 calls with positive-first and 9 with compensator-first; retractable-edge arms make 6 in either order. During the first positive transition, compensating-attribute arms make 9 positive-first and 12 compensator-first; retractable-edge arms make 9 and 12 respectively. The final simultaneous phase makes 12 calls in every cell. The differences reflect rule/fixpoint scheduling cost for this fixture, not semantic divergence. They make rule order relevant to work estimates even where pure, stable predicates yield the same graph.

The tested predicates are disjoint by construction. This does not establish confluence for overlapping rules that write conflicting facts, stateful callback order-independence, or automatic truth maintenance. Source and native identities, captures, and analysis are linked below.

Artifacts: [preregistration](SUBSTRATE_COMPENSATION_ORDER_SIMULTANEOUS_TRANSITIONS_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_compensation_order_simultaneous_transitions_v1.py), [analyzer](../../../scripts/analyze_compensation_order_simultaneous_transitions_v1.py), [raw capture](../../../evaluation/reports/compensation_order_simultaneous_transitions_v1_20260928.json), [lock](../../../evaluation/substrate_capability/compensation_order_simultaneous_transitions_v1_lock_20260928.json), [analysis](../../../evaluation/reports/compensation_order_simultaneous_transitions_v1_analysis_20260928.json).
