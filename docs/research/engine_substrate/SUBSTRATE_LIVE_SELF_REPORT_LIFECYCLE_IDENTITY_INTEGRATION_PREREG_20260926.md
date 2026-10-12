# Live self-report lifecycle identity integration preregistration

**Question:** can the existing live `self_report` route emit a complete Goal-specific lifecycle that survives repeated same-recipient turns, and do native lifecycle rules reject missing or misdirected Goal identity?

## Integration under evaluation

Use the Goal handle already returned by `conversation_action._mint_goal`. For a live self-report, record `selection`, then `execution`, then either `action_result` or `action_failure`, each through discourse-state `record_event` with an explicit event-to-Goal `for_goal` edge. Ensure the Goal has proposed lifecycle state and is active in the originating discourse state before the first event. Run native closure after each event. Extend the transition rules so selection, execution, result, and failure all require `event --for_goal--> goal`. A faculty exception/empty result records failure and moves an executing Goal to `blocked`; a non-empty held-faculty result records success and resolves it. Other action paths remain outside this integration.

## Confirmatory positive arm

In three fresh full-seed processes, run two identical `report your organisation` instructions for the same recipient. Require exactly two source Goals, each with exactly its own inbound Message and origin event; per Goal require exactly one lifecycle event of each successful kind, all three linked by `for_goal` to that Goal; require the ordered transition projection proposed → selected → executing → resolved, exact `transitioned_by` provenance, closed-goal membership, stable recipient, distinct identities, and a non-empty held-faculty reply. The other Goal must have no lifecycle events from this turn. Record timing and the full event/Goal projection.

## Identity and failure controls

Use fresh substrates with the same production rules and two active same-recipient Goals with distinct origin events. Exercise:

1. **Correct-link control:** one selection event linked to Goal A; only A may transition.
2. **Omitted-link control:** a later selection event without `for_goal`; neither Goal may transition from that event.
3. **Swapped-link control:** an event authored for A but linked to B; only B may consume it. The mismatch between the event's declared payload target and edge target must be visible to the oracle; the native rule's authority is the explicit edge.
4. **Duplicate-result control:** two action-result events for one already resolved Goal; one terminal transition only, no duplicate close or second-owner mutation.
5. **Faculty-failure control:** force the held faculty to raise; require selection/execution/action_failure provenance and terminal `blocked`, with no action_result or `resolved` transition.

The injected control payload target is an oracle label, not a second matching authority. Exact graph projection, owner assignment, event counts, and terminal-state gates are independently reconstructed from raw graph data. A source/build fingerprint must remain constant at parent start, every worker start/end, and parent end; source drift invalidates confirmation and the capture is preserved.

## Boundaries

This does not establish event production for scene, planning, external-I/O, or other action routes; safe effect authorization; reliability across all failure sites; natural-workload prevalence; or scaling beyond the two-goal fixture. The purpose is to close and measure one real held-faculty route and the native identity guard before widening the producer surface.
