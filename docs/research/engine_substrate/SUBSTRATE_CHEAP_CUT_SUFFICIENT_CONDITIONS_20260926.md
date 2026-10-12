# Cheap-cut tractability: sufficient conditions and measurement gates

**Date:** 2026-09-26. **Purpose:** make the structural tractability claim
precise enough to test. This is a conditional complexity statement, not a
claim that current Ocelot execution satisfies the conditions.

## Claim under test

Let a finite factor graph or rule-dependency graph contain `n` task-local
variables, each with domain size at most `d`. A frame decomposition is a tree
of local regions. Each region has at most `s` local variables and exports at
most `k` variables to its parent; every factor is assigned to one region or
explicitly represented as a boundary factor. Assume the decomposition is
complete: every dependency crossing a frame boundary is represented in the
boundary interface, and every update to a boundary value reaches all dependent
frames before a fixed point is reported.

For exact finite-domain inference, table-based variable elimination over this
decomposition costs

`O(n · d^(w+1))` arithmetic operations and `O(n · d^w)` table space,

where `w` is the maximum induced width of the actual elimination order,
including local frame work and boundary variables. In a frame tree with
bounded local factor work, `w <= max(s, k + r)` for a bounded local factor
scope `r`, giving linear dependence on the number of frames for fixed `d`,
`s`, `k`, and `r`. The constants include the cost of evaluating and combining
local factors.

This is the useful theorem shape. “Boundary size at most `k`” by itself is
insufficient: a frame can have arbitrarily large internal treewidth, a factor
can span the whole frame, the domain can grow, or an unrepresented global
factor can couple every frame. Conversely, a small separator hierarchy is
evidence for a low-width elimination order only when its local interiors and
boundary factors are also controlled. For approximate inference, this exact
bound does not apply; approximation error and convergence must be measured
separately.

For closure, locality gives a different sufficient condition. Let `F` be the
number of frames and `C_i` the cost of a complete local saturation of frame
`i` for the current boundary snapshot. If each rule effect either stays in
its frame or emits a complete notification to every frame whose next enabled
match can change, a fair work queue reaches the same least fixed point as
monolithic monotone closure. Its work is bounded by the sum of local match
costs plus notification and queue costs; it is not automatically linear in
`F`, because one boundary update can wake `F` frames and repeated cross-frame
feedback can cause many rounds. A bound additionally needs finite progress,
bounded fan-out, bounded notifications per progress event, and a termination
bound for rule effects.

## Conditions that must be recorded

| Symbol / condition | Meaning | Required evidence |
|---|---|---|
| `F` | Number of frames | Exact count at every checkpoint |
| `s` | Maximum task-local frame size | Full distribution, including maximum and tail quantiles |
| `k` | Maximum exported boundary variables/nodes | Per-frame distribution and stable identity of each boundary item |
| `w` | Induced width of the full dependency/factor graph | Exact where feasible; otherwise named upper bound and algorithm |
| `d` | Maximum variable domain | Observed and configured domain limits; do not assume Boolean domains |
| `r` | Maximum factor/rule read scope | Static declared scope plus observed concrete accesses; unknown remains unknown |
| Completeness | All cross-frame reads/effects represented | Mutation-recall controls and trace coverage; refusal on incomplete contracts |
| Maintenance | Cost to find/update frames and boundaries | CPU, wall, memory, and work counts included in end-to-end cost |
| Semantics | Partitioned result equals monolithic least fixed point | Full normalized graph parity and independent task/fixed-point oracle per checkpoint |

The commonly useful special case `O(n · d^k)` requires that the *whole*
elimination width be bounded by `k` (or another stated constant), not merely
that each cut has at most `k` members. “Polynomial in frame size and linear in
frame count” is conditional on fixed interface and local-width bounds; if
these grow with the input, the exponent or table size grows with them.

## Mapping to current substrate evidence

The current scoped API accepts a Microtheory owner and scopes through
`has_concept` membership. Its delta report exposes changed nodes, edges, and
affected Microtheories, while the Python binding declares frame notifications
incomplete. Therefore it does not yet establish dependency completeness,
arbitrary stable frame membership, or correct scheduling after every
cross-frame effect. Caller-side owner queues in Bigville and conversation
experiments are useful reference implementations, not native scheduler
evidence.

Existing structural measurements already include synthetic cut distributions,
CAN factorization controls, a Vision global-fold counterexample, Bigville
caller-queued parity, and connected conversation panels. These establish that
locality varies by workload and rule path. They do not estimate the frequency
of bounded `s`, `k`, or `w` on independently sampled tasks. The current
cheap-cut status remains **open / workload-specific**.

## Required gates for a positive bounded-cost statement

1. **Structural gate:** on preselected, independently sourced task families,
   measure `F`, `s`, `k`, `w`, domain size, factor arity, global-boundary
   incidence, and partition build/update cost at runtime checkpoints. Include
   a sparse case, a connected case, and a known global-coupling negative case.
2. **Contract gate:** audit static rule dependencies, dynamic read/write
   coverage, boundary delivery completeness, and cross-frame mutation recall.
   Incomplete or ambiguous cases must refuse partitioned execution.
3. **Semantic gate:** compare every partitioned checkpoint with fresh
   monolithic closure/inference and an independent oracle; include omitted and
   stale-boundary controls that must diverge when the omitted dependency is
   active.
4. **Cost gate:** report local work, queue/message work, partition discovery
   and maintenance, CPU, wall time, and memory. Report setup-inclusive and
   steady-state costs separately. A reduction in candidate pairs alone is not
   a speedup.
5. **Scaling gate:** increase task size and frame count independently, then
   vary interface width. Fit empirical scaling only within the frozen domain;
   do not extrapolate a polynomial from a narrow interval or use synthetic
   topology as a natural-task prevalence estimate.

Passing these gates would support a scoped empirical claim, and the formal
bound above would explain its assumptions. A general substrate-wide guarantee
would additionally require those conditions as enforced input/runtime
contracts.
