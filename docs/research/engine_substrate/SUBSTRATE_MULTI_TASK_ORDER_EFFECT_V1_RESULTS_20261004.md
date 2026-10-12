# Multi-task order-effect v1 results

Ten fresh full-seed workers replayed five cyclic rotations of the authored
five-task sequence, with two workers per order. Source locks, distinct worker
PIDs, all 50 prompt IDs, and per-order normalized graph and behavior
replication pass. The independent analyzer recomputes every prompt's Goal and
event projection from the retained graphs and reproduces all contract rows.
Raw graph structure repeats within each order after excluding only `ts` and
`runtime_s`; graph size varies across orders from 25,403 to 25,457 nodes and
12,217 to 12,325 edges.

The adapted existing task contracts pass 30/50 requests. Results are identical
at every sequence position: 6/10 pass at positions 0 through 4. Unknown-word
clarification, self-knowledge answer, and self-report action pass 10/10 each.
Scene description and concern authoring pass 0/10 each, regardless of order.
Scene description produces the wrong `report_self` Goal and the reply “I am
Jabberwock.” Concern authoring repeatedly asks what “two” means; no
`act_on_instruction` action result is recorded for that prompt. The failures
therefore remain stable across the five cyclic orders, while position
stratification in this small panel is uninformative. Goal-linked ownership
remains sparse: only scene description and self-report action have Goals,
with both typed `report_self`.

Across the ten graph captures, 24 edges cross between the disjoint conservative
prompt owner sets. Every crossing edge is `responds_to`; counts are 3 per
replicate in orders 0 and 1, and 2 per replicate in orders 2–4. These are
dialogue links and show that the projected task sets do not form edge-disjoint
frames. The analysis is descriptive: five cyclic orders of one authored panel,
two replicates per order, and no independent human labels. It establishes
repeatable task-specific failures under these routes, not causal absence of
order effects, natural-task prevalence, complete factor scopes, or partition
tractability.

The scene-description contract is necessarily a one-sided failure result: the
runner did not instrument the legacy contract's `_ensure_describe` rule-delta
condition. However, all ten scene runs violate both the expected exact reply
and expected `describe_scene` Goal conjuncts, so none can satisfy the full
legacy conjunction. Other task predicates are captured directly as listed in
the preregistration.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_MULTI_TASK_ORDER_EFFECT_V1_PREREG_20261004.md)
- [Amendment](SUBSTRATE_MULTI_TASK_ORDER_EFFECT_V1_AMENDMENT_20261004.md)
- [Capture runner](../../../evaluation/substrate_capability/multi_task_order_effect_v1.py)
- [Source lock](../../../evaluation/substrate_capability/multi_task_order_effect_v1_lock_20261004.json)
- [Compressed capture](../../../evaluation/reports/multi_task_order_effect_v1_20261004.json.gz)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_multi_task_order_effect_v1.py)
- [Independent analysis](../../../evaluation/reports/multi_task_order_effect_v1_analysis_20261004.json)

Reproduce by recreating the source lock for a new capture, then running
`python3 evaluation/substrate_capability/multi_task_order_effect_v1.py` and
`python3 evaluation/substrate_capability/analyze_multi_task_order_effect_v1.py`.
