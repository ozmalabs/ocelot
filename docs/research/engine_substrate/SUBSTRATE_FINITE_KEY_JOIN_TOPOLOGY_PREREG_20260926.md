# Finite-key join/topology closure envelope — preregistration (2026-09-26)

**Status: locked before capture.** This is a follow-up to the finite-key
single-edge scale-cost sweep. It varies positive-match structure and graph
topology while preserving a finite-key insertion-only effect fragment.

## Question

At fixed one-signature mint/effect structure, how do native closure cost and
closure work respond to positive match arity (one, two, or three directed edges)
and to path, cycle, or high-branching layered input graphs?

## Design

- Match arities `q={1,2,3}` using a directed path-shaped conjunction of q `link`
  triples with distinct variables.
- One rule per case. It matches the q-edge path, mints one fixed `Witness{tag:"w"}`
  using `add_node_if_absent`, and adds an empty-attribute `result` edge from the
  final matched node to that witness. The rule matches only `link`, so output
  edges cannot recursively increase match count.
- Path and directed-cycle sizes `N={32,64,128,256,512}`. Layered topology uses
  four levels of sizes `[1,s,s,1]`, where `N=2s+2` and `s={7,15,31,63}` (N=16,
  32,64,128); all adjacent levels are connected by complete bipartite `link`
  edges.
- Five fresh native substrates per `(topology,N,q)` cell, one separate warmup,
  and a deterministic shuffled execution schedule. Setup and closure are timed
  separately; no outlier is dropped.
- A separate enumerator computes q-edge walk bindings and distinct terminal
  nodes. The independent analyzer reconstructs expected exact final nodes and
  edges, validates a normalized graph digest, analyzer admission, fixed point,
  budget status, and the finite-key progress bound.
- Capture every sample, all graph sizes and match counts, Python/platform,
  relevant source/native hashes, and progress reports. Run in a second process
  for semantic confirmation before interpreting the cost envelope.

## Limits

The topology is authored and all edge values are fixed. This does not measure
arbitrary conjunction planning, node-type/selectivity choices, negative joins,
attribute tests, seed loading, natural task graph frequencies, native allocation,
or the general engine's worst-case bound. The enumerated walk count is an
independent workload descriptor, not a native candidate-counter measurement.
