# Multi-task order-effect v1 preregistration

Date: 2026-10-04

## Question

Do the five existing task contracts pass when the tasks share one persistent
graph, and does the result depend on prompt order?

## Design

Run all five task conditions in five cyclic orders, with two fresh full-seed
workers per order (10 workers total). Each order rotates the fixed panel by
one place from the prior order, so every task appears at every ordinal
position once. Each worker uses a new WorldAdapter and one shared graph for
the five prompts. Attach the scene fixture in every worker. Capture the
per-request reply, direct `act_on_instruction` route/goal-kind/concern,
prompt-linked Goals and lifecycle events, clarification messages, teacher call
count, final graph, and source identity. Apply the pre-existing isolated-task
contract predicates from `live_conversation_task_graph_harvest_v2.py` to each
request, adapted only to the sequential capture fields; report each predicate
and each condition/order outcome without post-hoc threshold selection.

## Gates and analysis

Require ten fresh PIDs, stable source lock, all 50 request records, exact
replication of the task-condition outcome vector within each order (ignoring
only explicitly identified diagnostic timing fields), resolved prompt IDs,
and independent recomputation of per-task Goal/event ownership. Correctness is
reported as a task-contract pass fraction and order-position table; the
contract outcomes are not used as a capture integrity gate. Analyze task,
position, and order descriptively; five cyclic rotations and two replicates do
not support a population or causal order-effect claim.

## Limits

This uses five authored prompts in an artificial fixed panel. It does not
estimate natural conversation prevalence, separate adaptation from time/order,
provide independent human ownership labels, or measure partitioned execution.
The same task contracts used for the isolated harvest may be brittle under
cross-task context; preserve every per-condition result and report failures.
