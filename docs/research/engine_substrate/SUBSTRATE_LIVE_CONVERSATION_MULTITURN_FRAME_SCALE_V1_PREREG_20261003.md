# Live conversation multi-turn frame scaling v1 preregistration

Date: 2026-10-03  
Status: preregistered before implementation/capture.  
Motivation: [single-request task-graph census and ownership audit](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V1_RESULTS_20261003.md)

## Question

When one substrate instance completes repeated live self-report requests, do task Goal/Event frames remain explicitly owned as frames accumulate, and how do graph size, direct cross-frame dependencies, shared-boundary incidence, interaction width, matcher work, and wall time change?

## Workload and schedule

For each fresh full-seed process, replay the exact production-route prompt `report your organisation` for N = 1, 2, 4, or 8 sequential turns through `WorldAdapter.converse`, with no graph reset between turns. Run three independent workers per N, for 12 workers total. Preserve the ordinary live conversation setup and add no synthetic nodes or ownership edges. Record per-turn reply, newly created Goals, lifecycle status, and action route. At the final turn, capture the exact graph and its digest. Record whole-process peak RSS and task/boot timing as descriptive fields.

This is a repeated authored task sequence selected because the v1 identity audit verified that this live route creates a resolved `report_self` Goal explicitly linked to its inbound Message; an exploratory two-turn replay confirmed distinct Goals and Message identities persist together. It is not a natural conversation distribution or a representative workload sample.

## Independent frame reconstruction

The runner emits no frame labels. The analyzer derives each frame root from every inbound interlocutor Message whose text equals the locked prompt, using node identity (not event order) to distinguish repeated turns. A Goal is assigned only through its explicit `comprehends` edge to one such Message. A DiscourseEvent is assigned only through its explicit `for_goal` or Goal-to-event `originated_in` edge, a Goal's `origin_event` node reference, or its `represents_message` edge to a frame-root Message. Conflicting ownership makes a node shared/unowned. All other nodes remain unowned; report both total unowned nodes and the subset directly incident to frame nodes.

Compute and report graph/node-type totals, frames and frame-owned types, unowned Goal kinds, owner conflicts, direct cross-frame edge counts/types, boundary incidence and unique incident boundary nodes, the frame-interaction graph, and exact treewidth for up to eight frames. Also report per-turn Goal creation/resolution, graph digest stability, native Candidate/Term work if exposed by the live route, and task/boot wall and CPU. Do not infer missing closure work from a zero native counter when the route has no counter instrumentation.

## Gates and claim boundary

Require 12 unique fresh PIDs, exactly three workers at each N, locked source stability, one final graph per worker, exact replicate graph digest equality at each N, exactly N prompt Messages, and exactly N distinct `report_self` Goals each linked to its own prompt Message and resolved through the expected lifecycle. Any miss is retained as a capability/integrity result; do not drop or repair the case after capture. The independent analyzer reconstructs all ownership and topology from raw nodes/edges.

The result measures persistence and graph scaling for one repeated live action route only. Repetition may create regular structure absent from general tasks; no natural frame-locality or general tractability claim follows. The next gate should use independently authored, semantically distinct multi-turn tasks with separate oracles after this identity and persistence path passes.
