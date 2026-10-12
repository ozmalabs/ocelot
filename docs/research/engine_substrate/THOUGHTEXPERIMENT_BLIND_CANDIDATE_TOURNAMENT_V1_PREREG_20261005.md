# Blind candidate tournament v1 (preregistration)

## Question

Can the structural proposal pool from `edit_ops` be evaluated against actual
task outcomes in isolated CoW branches, and can the graph-native
self-change rules select a candidate using only measured candidate/control
evidence, without family labels or target identity?

## Tasks and policy boundary

Two task conditions use the same small rule shape and candidate language. In
`repair_needed`, the live rule writes `task_pass=false` while the task oracle
requires true. In `no_repair`, the live rule already writes true. Each task
has two train examples, three disjoint canary examples, and two fresh final
examples. Examples are separate graph nodes with the required `has_task` and
`has_context` relations.

The proposal generator receives only the live rule JSON. The trial evaluator
receives candidate rules and train examples with oracle outcomes. The graph
selector receives opaque candidate IDs, task-measured candidate/no-op/placebo
gains, invariant count, budget, and replication evidence. It receives no
fault label, candidate operator name, target UID, or corrected rule. The
target UID/revision/hash are bound to the selected patch only after the graph
selects it, for guarded Rust CAS. Task construction and correctness labels
remain harness-owned and are charged as external capabilities.

## Procedure

Three fresh workers each run both cases. Candidate, no-op, and one-edit
same-size placebo arms are each measured in three isolated
shared-graph-page CoW branches. Candidate gains are derived from exact
training-example accuracy, scaled by ten points per correct example; control
gains are measured the same way. All candidate patches are represented as
opaque `RulePatch` graph nodes and connected to measured `TrialEvidence`.
Graph rules mint obligations, reject candidates that fail controls, and
select the minimum-MDL passing proposal. The repair-needed selection then
runs on the disjoint canary split, binds the CAS identity, and commits through
the native transaction path only on a pass. Fresh final examples verify the
committed rule. The no-repair case closes its evidence batch and must abort
without changing the target revision.

## Gates and measures

Require exact candidate output/evidence accounting, identical decisions in
all workers, no primary mutation during rehearsal, graph-native selection of
the sole control-beating candidate in `repair_needed`, explicit no-repair
abstention, canary pass before a single revision increment, successful final
outputs, and source-lock stability before/after each worker. Capture candidate
count, per-phase wall time, train/canary/final outcomes, selected opaque ID,
control scores, abort/commit status, and revision receipts.

This is a two-condition, one-rule-family integration probe. Even a pass does
not establish broad structural induction, task-agnostic evaluation, natural
workload transfer, or self-improvement. It tests whether candidate generation,
branch utility, graph selection, canary, and CAS can be connected without
passing the family answer to the selector.
