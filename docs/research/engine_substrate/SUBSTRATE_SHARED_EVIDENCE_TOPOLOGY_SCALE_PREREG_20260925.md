# Shared evidence topology and scale preregistration

## Question

How do full and frame-scoped native closure costs change with topology and boundary fan-out for the validated shared-evidence copy/retract rule pair, while preserving exact state through repeated boundary insertions, updates, and retractions?

## Frozen design

- Reuse the two benchmark-native rules from the shared-evidence propagation v1.2 experiment: active evidence copies `signal` to each supported frame-local state; inactive evidence resets that state to zero.
- Test N=8/16/32/64 frames, three deterministic connected topologies (path, star centered at frame 0, and heap-indexed binary tree), and three fresh-process replicates.
- Each topology edge is one shared evidence node with separate local output states at its two endpoint frames. The evidence node belongs to both endpoint Microtheory scopes; each output state and frame is local to one scope. Boundary `supports` edges are initially absent and inserted/removed during the run.
- Compare `full`, `scoped` round-robin across all frame scopes, and `scoped_omit_boundary0`, which skips both endpoint scopes of the first topology edge. The omission arm is a sensitivity control only.
- Six checkpoints: (0) inactive/no support edge; (1) insert both support edges and activate signal 1.0; (2) update active signal to 0.5; (3) deactivate, run closure to reset local state, then delete both support edges; (4) reinsert support edges and activate signal 0.75; (5) deactivate, run closure, then delete support edges.
- At every checkpoint, compare all frame-local state values to an independent expected vector and compare full/scoped projections exactly. For omission control, boundary 0's two endpoint states should be stale at activation/update/re-activation; all other states should match. Record per-checkpoint candidate enumeration, Term evaluations, progress, turns, wall/CPU time, peak RSS, and state projections.
- Lock topology generator/rules/runner, protocol, bindings and scheduler sources before execution; require a current native build.

## Claim boundary

This is a controlled engine benchmark for three graph families through N=64. Scope visitation is caller-directed. It measures neither automatic notification nor natural task topology prevalence, and it does not establish asymptotic complexity outside the sampled sizes. Retraction is explicit and occurs before deleting the support edges; no automatic truth maintenance is claimed.
