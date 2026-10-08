# Live self-identity single-Goal integration v2 (2026-09-26)

## Result

The self-report action faculty now adopts the unique graph-authored `report_self` Goal already bound to the reflexive instruction. It fills in predicate, object, and self target on that Goal, then records the existing selection→execution→action_result lifecycle against the same identity. When no unique event-bound `report_self` Goal exists, the established Goal-minting path remains in place.

Three fresh workers pass all 18 preregistered checks, including source stability and repeated signatures:

- `describe yourself` and `tell me about yourself` each create exactly one event-bound `report_self` Goal, targeted to `self_identity`, resolved with all three correctly linked lifecycle transitions.
- `describe who you are` remains a table/meta question; `who are you` remains a direct meta question. Neither creates an action Goal.
- `summarise the report` returns the external-instruction floor and creates no self-report Goal.

The produced identity text remains `I am Jabberwock.` on the tested action and question routes. The negative control shows that the adoption path does not claim this tested external-object instruction.

## Interpretation and limits

This closes the duplicate unresolved Goal observed in v1 for the two reflexive self-report prompts and supplies current-source replication evidence. A separate one-worker readback inspected the exact outbound and production records for `describe yourself`: the graph rule leaves an unreceipted candidate Message (`I am Jabberwock, a graph-native agent running in Rust...`), while the released production receipt commits the action faculty's shorter `I am Jabberwock.` surface against the adopted Goal. Thus only the action reply is recorded as released; the graph-authored candidate remains in the graph as unused state. The measurement covers two action phrasings, two question phrasings, and one external-object negative control on one fixed-order conversation per fresh worker. It is not a broad language, answer-quality, tractability, or scale result.

## Artifacts

- Pre-run protocol: [v2 preregistration](SUBSTRATE_LIVE_SELF_IDENTITY_SINGLE_GOAL_V2_PREREG_20260926.md)
- Runner: [`substrate_live_self_identity_route_probe_v2.py`](../../../scripts/substrate_live_self_identity_route_probe_v2.py)
- Source lock: [full closure](../../../evaluation/substrate_capability/live_self_identity_single_goal_v2_lock_20260926.json)
- Raw capture and gates: [three fresh workers](../../../evaluation/reports/substrate_live_self_identity_single_goal_v2_20260926.json)
- Prior duplicate observation: [v1 route probe](SUBSTRATE_LIVE_SELF_IDENTITY_ROUTE_PROBE_V1_RESULTS_20260926.md)
