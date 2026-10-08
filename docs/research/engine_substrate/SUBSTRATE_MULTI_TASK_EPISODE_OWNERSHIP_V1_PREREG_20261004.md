# Multi-task episode ownership v1 preregistration

Date: 2026-10-04

## Question

When the five authored task prompts are replayed sequentially in one fresh
substrate graph, do prompt-linked Goals and lifecycle events remain explicitly
associated with their triggering messages, and how many graph edges cross the
resulting explicit task-owner sets?

## Method

Use the five prompts and fixtures registered in
`evaluation/substrate_capability/live_conversation_task_graph_harvest_v2.py`,
in this fixed order: scene description, unknown-word clarification,
self-knowledge question, concern authoring, self-report action. Each worker
boots a fresh full-seed WorldAdapter, attaches the scene fixture, then sends
all five prompts to that same adapter. Capture the final graph and each
inbound Message ID. Independently construct each conservative owner set from
its Message, Goals joined through `comprehends`, and related DiscourseEvents
joined through `for_goal` or Goal `origin_event`. Count exact owner intersections,
cross-owner edges, ownerless task Goals/events, task route/outcome contracts,
and graph growth after each prompt when available. Run two fresh workers and
require stable source locks, distinct PIDs, exact graph digest replication,
and resolved IDs before interpreting task ownership.

## Limits

This is a selected five-prompt authored sequence and two replicates, not a
natural-task prevalence or generalization estimate. Relations provide a
conservative ownership projection, not a complete causal/factor dependency
model. Sequential accumulation confounds task order and adaptation; this pass
does not establish order effects, partitioned execution, or tractability.
