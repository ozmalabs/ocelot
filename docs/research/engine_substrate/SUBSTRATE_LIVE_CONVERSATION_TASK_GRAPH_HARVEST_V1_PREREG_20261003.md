# Live conversation task-graph harvest v1 preregistration

Date: 2026-10-03  
Status: preregistered before graph-capture implementation and run.  
Workload source: [live conversation capability panel v1](SUBSTRATE_LIVE_CONVERSATION_CAPABILITY_PANEL_V1_RESULTS_20260927.md)

## Question

What graph sizes, explicit task ownership, and cross-task/boundary connections arise when the substrate executes the existing live conversation panel routes on current locked source?

## Workload and provenance

Replay the same five locked panel conditions—scene description, held self-knowledge answer, self-report action, unknown-word clarification, concern authoring—with two fresh full-seed workers per condition, using the panel's fixed prompts, scene, task oracles, and schedule. Capture each worker's final native graph along with the existing route/task evidence. This is a replay of repository-authored evaluation prompts through `WorldAdapter.converse`; it is not a sample of private user conversations or an estimate of natural-task prevalence. Include the known failed concern route rather than conditioning graph analysis on task success.

## Independent ownership labeling

The runner stores the raw graph without adding task-owner labels. The analyzer derives them independently from serialized graph identity:

1. Each inbound interlocutor Message whose text equals the locked prompt defines a request frame root.
2. A Goal belongs to that frame only when the graph's `comprehends` relation links it to the root Message. A Goal linked to multiple prompts is shared/unowned; an unlinked Goal remains unowned.
3. A DiscourseEvent belongs to the frame of a Goal when it has an explicit `for_goal` edge to that Goal or is referenced by that Goal's `origin_event` attribute. Conflicting owner frames make the event shared/unowned.
4. Do not infer ownership from node creation order, event index, temporal adjacency, or semantic similarity. All remaining nodes are boundary/unowned nodes.

The analyzer reports frames, owned nodes by type, owner conflicts, direct cross-frame edges, boundary incidence per frame, frame-interaction edges, and exact treewidth of that small interaction projection when computable. It separately reports whole-graph size, task outcome, route, and whether the frame rule has sufficient positive evidence to assign any Goals/Events.

## Integrity and claim boundary

Require ten unique fresh worker PIDs, two workers per condition, source-lock stability, complete final-graph snapshots, and exact graph-digest parity across each condition's replicates. The independent analyzer reconstructs frame ownership from raw node/edge identities and verifies all reported counts. Task contract success is an outcome, not a workload inclusion gate.

This measures production-route-generated graphs for five authored prompts on one repository state. It can expose gaps between expected ownership and actual runtime graph links. It cannot establish natural task distributions, broad frame locality, or a tractability theorem. The next gate is to add independently sourced task episodes only after acquiring explicit data-use authorization and an annotation protocol; do not present this authored prompt panel as natural conversation evidence.
