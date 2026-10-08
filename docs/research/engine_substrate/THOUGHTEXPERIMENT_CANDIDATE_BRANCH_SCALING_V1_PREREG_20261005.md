# Thoughtexperiment candidate branch scaling v1 (preregistration)

## Question

How do reusable shared-graph-page branch costs and task-local rule execution
change as a sparse background graph grows while the task, rule aperture, and
number of task-local writes stay fixed? This measures one concrete operating
path under increasing total graph size; it does not directly measure treewidth
or natural-task prevalence.

## Design

Use four total graph sizes (0, 1,024, 8,192, and 32,768 decoy nodes). Decoys
form one directed path with edge type `decoy_next`; task rules mention only
`TaskInput`, `TaskOutput`, and `TaskContext`, so the path is outside the rule's
match aperture. The task rule is a live `signal >= 0` threshold. A candidate
branch changes it to `signal >= 1`; one input with `signal=0` must therefore
produce `true` under live/no-op and `false` under the candidate.

Three fresh processes measure each size. Each process builds the primary graph
once, then performs five paired no-op/candidate branch repetitions. Arm order
alternates by repetition and process. Each branch times shared-page fork,
rule installation, task input creation, native closure, and targeted result
read separately. Graph construction time is reported outside branch timings.
The runner records wall phase times, process resident-memory snapshots,
graph size, exact outputs, and primary graph plus active-rule revision/hash
before and after. RSS snapshots are diagnostic only; no memory delta claim is
registered because allocator reclamation and temporary serialization can move
RSS in either direction.

## Acceptance and limits

All 120 branch episodes must produce the registered outputs, source hashes
must match the frozen lock in every worker, paired repetitions must agree,
and primary graph/rule digests must remain unchanged. Report medians by graph
size and phase; do not fit a complexity exponent from four points. The sparse
path is a controlled topology, not a natural workload. The fixed task does not
test candidate induction, broad rule matching, changing aperture, high-degree
graphs, memory pressure, concurrent forks, or multi-host execution.
