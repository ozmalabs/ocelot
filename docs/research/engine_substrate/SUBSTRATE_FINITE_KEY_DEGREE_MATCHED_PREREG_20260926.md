# Finite-key edge-count-matched degree comparison — preregistration (2026-09-26)

**Status: locked before capture.** This extends the join/topology work study by
holding graph size and directed edge count exactly equal across degree profiles.

## Question

For the same native positive joins and fixed finite-key effect, how do closure
time and direct matcher-work counters differ across low-, moderate-, and
high-degree input graphs when N and E are matched?

## Design

- N in `{32,64,128,256}`; three directed topologies for each N:
  - bidirected path;
  - bidirected star;
  - bidirected balanced binary tree (heap parent relation).
- Each topology is connected and has exactly `N` nodes and `2(N−1)` directed
  `link` edges. Report the actual degree histogram and maximum degree per graph.
- Match arities `q={1,2,3}` with the same directed path-shaped positive join
  used in the prior study. One fixed literal witness is minted and a `result`
  edge is added from the final matched node. The rule matches only `link`.
- Five replicates per cell in a deterministic shuffled schedule; one fresh
  substrate for an uninstrumented closure timing arm and a separate fresh
  substrate for an audit-enabled integer-counter arm.
- Each counter arm resets/enables global and per-rule `scale_audit` immediately
  before closure and disables it after snapshots. Audit-on wall time is excluded
  from all timing summaries.
- One independent walk enumerator predicts complete binding counts and terminal
  nodes; another exact terminal graph projection check validates both arms.
- Repeat the matrix in two fresh processes. Capture runner, analyzer, matcher,
  graph, scale-audit, protocol, and native artifact hashes. Compare semantic
  outputs and counters exactly across processes; report timings separately.

## Admission

Every cell must have the same N/E across the three topologies, exact input degree
counts, exact final graph, fixed-point status, and a progress count within the
finite-key bound. Candidate-path, candidate-epoch, Term-variant, and per-rule /
global counter identities must hold. Any failure is retained and excludes that
cell from timing interpretation.

## Limits

This manipulates degree profile through authored tree topologies. It does not
isolate all graph invariants (diameter, clustering, shape and join selectivity
also differ), estimate natural prevalence, or establish workload performance.
Counters are instrumented site counts, not CPU instructions. No native
allocation or memory measurement is included.
