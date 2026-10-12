# Endpoint-degree join-order oracle v1 preregistration

Date: 2026-09-26

## Question

Can a data-informed endpoint-degree cost model predict the current matcher's candidate-test count for a two-edge chain, choose the cheaper installed order, and reduce uninstrumented closure cost after charging for planning and rule installation?

## Design

For `M={4,16,64}`, use two-edge path relations with `D/M={0,4,16}` one-sided decoys split equally between relations. Each split has the same number of `left` and `right` relation edges, so the engine's existing global edge-count policy ties. Compare a count-control authored order (`trigger,left,right,game`, which the current tie handler installs as `trigger,game,right,left`) with an endpoint-degree policy order. The policy scans the actual relation pairs to estimate the matcher's two path orders:

- left then right: `|L(a)| + Σ(mid∈L(a)) outdegree_right(mid)`;
- right then left: `|R⁻¹(b)| + |R⁻¹(b)| × outdegree_left(a)`.

The equations mirror the current matcher implementation: a bound source enumerates outgoing neighbors, a bound target enumerates incoming neighbors, and the both-bound branch still enumerates the source's outgoing list before rejecting a different target. Constant trigger/game clause work is omitted from choosing the order and added when checking predicted totals. The policy authors the order that causes the current installer to realize its selected path order; it does not bypass or modify the production reorderer.

Run 3 replications for every multiplicity/decoy ratio and both policies: **54 fresh processes**. Each process builds one graph, then runs independently constructed audit-off and audit-on closures. Measure planning CPU/wall time, `add_rule` install time, plain closure CPU/wall time, audit closure time, candidate tests by installed edge and rule, queue work, exact graph/report parity, and source/native identity. Report combined policy+install+plain-closure wall time separately from plain closure alone. Do not count Python process startup or graph construction as planner cost; relation-list scanning required by the estimator is inside planning time.

## Gates

- Source/native lock stable in every worker.
- 54 fresh PIDs, all factorial cells present, three replications per cell.
- Exact audit-off/on graph and report parity; exact policy/control final graph parity.
- Fixed-point completion, zero budget overshoot, one target output, four framebuffer grid cells, deleted trigger, exactly `M` queue enqueues/drains for each queue family.
- Read back actual installed order. Control and treatment must install the intended two path orders.
- For every cell, the analytical estimate for each path order equals the observed writer-rule candidate tests for the matching installed order; the policy chooses the lower count.
- Integer candidate and queue work repeats exactly across replications. Positive timer readings; timing remains descriptive.

## Claim boundary

This is an exact cost oracle for one authored two-edge schema and the current matcher branches, not a general optimizer. Its planning work is O(number of relation edges) in this fixture and is charged. No claim is made about arbitrary joins, natural-task prevalence, memory, or general tractability. A next step would need a bounded estimator for multi-edge rule populations and task-derived replay.
