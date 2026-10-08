# Multi-route frame and native access capture v1

Date: 2026-10-06  
Status: prospective, fixed-protocol panel; five repository-authored live conversation routes with two fresh full-seed replicates each.

## Question and scope

Does the previously fixed outcome-blind ingress frame remain small across the five live-conversation routes, and how much post-checkpoint native rule access touches the frame, its direct boundary, and the rest of the graph? This is an operational measure of one locality claim. It does not establish a factor interface, dependency completeness, a cheap separator, natural-task prevalence, or a speedup.

## Fixed frame and checkpoint

Use exactly the ownership procedure and hook from `SUBSTRATE_PREOUTCOME_TASK_FRAME_CAPTURE_V1_PREREG_20261005.md`: capture after `_record_live_communication_state` returns, before first native closure; own inbound Message, its `has_mention` Mention nodes, incident linked CommunicationInterpretation nodes (`has_interpretation`/`interprets`), and linked DiscourseEvent nodes (`represents_message`/`for_message`). No outcomes, answer, Goal, held knowledge, receipt, or reply may inform the frame. Record graph size, frame and direct external boundary counts/types, crossing incidences, and min-fill upper bound on the induced state-graph projection.

Reset native runtime access tracing at the checkpoint and collect until the end of `converse`. Join RuleUIDs to access-set metadata; classify node and peer references as frame, direct external boundary, outside cut, or node-free. Preserve dropped rows and unmapped IDs. This native trace does not account for every host-side read and cannot establish semantic necessity.

## Workload

Replay the existing `live_conversation_task_graph_harvest_v2.py` schedule: scene description, unknown-word clarification, held self-knowledge answer, concern authoring, and self-report action, each on two fresh workers. Preserve its route task-oracle checks. The panel is selected and repository-authored; repeated workers test reproducibility, not population prevalence. Known baseline task utility failures remain visible and are not recast as locality failures.

## Integrity and reporting gates

- Lock this protocol, capture runner, harvest runner and its inputs, frame-width helper, native extension, and schedule before capture; verify the lock after.
- Exactly one pre-outcome frame and post-checkpoint trace per worker (10 total), no dropped access rows, no unmapped RuleUIDs, and source-stable task results.
- Report per-route replicates and distributions, retaining task utility and structural validity as separate outcomes.
- Frame IDs and counts are descriptive. Do not infer a factor scope or separator from the state-graph projection or trace-role counts.
- No timing claim: graph instrumentation and trace collection are inside the conversation call. Do not compare measured costs to uninstrumented runs.

## Decision rule

This panel can show whether the already-used operational projection reproduces across these five routes and whether native accesses are broad beyond it. If broad accesses recur, the next gate is static rule read/write dependency reconciliation and host-side scan attribution, followed by a partitioned/monolithic parity experiment. No tractability claim advances on this capture alone.
