# Live conversation task-graph harvest v2 preregistration

Date: 2026-10-04

## Question

Do explicit prompt-to-Goal/Event ownership and task-cut measurements replicate
across the five existing authored conversation routes on the current worktree
and current native engine?

## Workload and provenance

Replay the fixed panel of scene description, held self-knowledge answer,
self-report action, unknown-word clarification, and concern authoring. Use two
fresh full-seed workers per task, including known unsuccessful task outcomes.
Capture each final native graph, task behavior, resource/time fields, and exact
source/runtime provenance. Require the engine provenance guard in the parent
and each worker. The source lock binds this protocol, capture and independent
analyzer, runtime input/source closure, and current native build identity.

## Ownership reconstruction

The independent analyzer uses only serialized graph identity and explicit
relations: an inbound prompt Message defines a root; a Goal is assigned only
when a `comprehends` edge links it to that root; a DiscourseEvent is assigned
only through `for_goal` or the Goal's `origin_event`. Conflicted and all other
nodes remain shared/unowned. Do not use creation order, event index, temporal
adjacency, semantic similarity, or task success to assign ownership. Require
exact final-graph digest agreement between both fresh workers for each task.
Report task outcome separately from frame structure.

## Limits

This is the same five repository-authored prompts, not an expanded natural-task
sample. Replication tests source-current stability and whether explicit graph
links support ownership on these tasks; it does not validate labels against
independent human adjudication, establish multi-frame cheap-cut prevalence, or
measure partitioned execution cost. A second blind annotation pass remains a
separate validation gate.
