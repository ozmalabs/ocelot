# Shared evidence randomized topology and mutation v1.2 amendment

V1 completed all 81 workers and its full/scoped semantic gates passed, but its omission-control predicate expected the omitted boundary to be non-stale at checkpoint 3. In this checkpoint the selected boundary is still part of the spanning-tree backbone and remains active at signal 1.0; only a subset of newly inserted cross edges is retracted/deleted. Its omitted outputs therefore correctly remain stale (and expected-nonzero) at checkpoint 3 as well as checkpoints 1, 2, and 4. The v1 raw report is preserved unchanged.

V1.1 changes only the sensitivity predicate to require the two selected boundary outputs to be the only stale outputs at checkpoints 1, 2, 3, and 4, with no stale outputs at initial or final all-retracted checkpoints. Workload generation, mutations, sizes, seeds, arms, counters, and semantic parity gates are unchanged.

V1.1's `mutation_ns` measurement also included closure, projection, and audit work because the timer stopped only after the complete checkpoint. Those values are preserved but must not be interpreted as partition-maintenance cost. V1.2 records pre-closure graph/input/scope mutations and post-closure support/scope-edge removals in separate timers, excluding closure and projection. The semantic workload and gates do not change.

## Question

Do full and caller-scoped native closure preserve frame-local derived state when connected graphs are generated from independent random spanning trees and boundary edges are inserted, retracted, deleted, and reinserted during execution?

## Locked design

- Reuse the two benchmark-native shared-evidence rules from the v1.2 propagation experiment: active evidence copies its signal to supported frame-local outputs; inactive evidence resets supported outputs to zero.
- Test N=12/24/48 frames with three fixed graph seeds (`20260925`, `20260926`, `20260927`), three fresh-process replicates per seed/size/arm, and arms `full`, `scoped`, and `scoped_omit_boundary0`.
- For each (N, seed), create an independently seeded random spanning tree. At checkpoint 2, add `floor(N/4)` non-tree edges selected from a seeded shuffle. Retract and delete half of those additions at checkpoint 3. Reinsert those same endpoint pairs at checkpoint 4. The additions cross the initial partition because their endpoints were not adjacent in the spanning tree.
- Each evidence boundary has two local output states, one per endpoint frame. Its evidence/state nodes are added to the corresponding Microtheory scopes when the edge is inserted and removed from those scopes when deleted. Scope/graph maintenance time and operation counts are recorded separately from closure.
- Six checkpoints: initial disconnected support edges/inactive values; insert/activate the spanning tree at signal 1; update active values to 0.5 and insert/activate new cross edges at 0.5; deactivate half of those new edges, settle their outputs to zero, then delete their support and scope-membership edges; update remaining active edges to 0.75 and reinsert the removed endpoint pairs at 0.75; deactivate all boundaries, settle, then remove support and scope-membership edges.
- Compare all full/scoped output states at each checkpoint to independently calculated expected values. The omitted-boundary arm skips both endpoint scopes of the first spanning-tree edge; those two outputs must remain stale when expected nonzero, while all other outputs match. Capture scoped results before any full-graph report call.
- Record graph sizes, dynamic boundary counts, scope membership additions/removals, mutation time, closure candidates, Term evaluations, progress, scope turns, wall/CPU time, memory, and exact projections. Three replicates are descriptive; graph seeds are the structural variation.
- Lock protocol, runner, rule definitions, binding/scheduler sources and current native-build provenance before execution.

## Claim limits

This is a controlled random sparse-graph family at N≤48 with explicit rules, caller-provided scope visits, and orchestrated retraction before support-edge deletion. It is not evidence of natural graph distributions, automatic native notifications, general truth maintenance, or asymptotic complexity. Any failed parity or sensitivity gate is preserved as a result.
