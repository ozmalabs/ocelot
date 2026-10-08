# Shared evidence randomized topology and mutation preregistration

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
