# Finite-key closure scale cost — preregistration (2026-09-26)

**Status: registered before capture.** This extends the proven finite-key
monotone insertion fragment with a wall-time/counter envelope; it is not a
general chase or full-engine benchmark.

## Question

For the existing recursive finite-key rule family, how do setup and native
closure time, fixed-point passes, and graph size change as the initial graph
grows, with the rule program and mint-signature count held fixed?

## Design

- Initial graph sizes `N={16,32,64,128,256,512,1024}`.
- Fixed distinct literal mint-signature counts `M={1,2,4}`.
- Initial topology: directed `cycle` with one `link` edge per Seed node.
- Each of M rules matches `x -link-> y`, mints one fixed-tag `Witness` by
  `add_node_if_absent`, and adds an empty-attribute `y -link-> Witness` edge.
- Seven fresh native substrates per cell, in a deterministic shuffled schedule;
  one separate unrecorded warm-up per `(N,M)` cell.
- Time setup (nodes, edges, rules) separately from `run_rules_report`; retain
  every sample and report medians/ranges. No source edits to the native engine.
- Independently verify the exact final node/edge sets, analyzer admission, fixed
  point, no budget exit, and progress steps below the analyzer's conservative
  finite-graph bound. Select runtime progress budget above that bound.
- Capture Python/platform, source/native hashes, all raw times and closure
  reports. No timing sample is dropped as an outlier.

## Expected closure shape

For this specific fixture the terminal graph should contain N Seed nodes, M
distinct Witness nodes, the N cycle edges, and every Witness-tag edge from each
of the N+M nodes to each of the M witness nodes: `N + M(N+M)` total edges. This
fixture-derived oracle is not an arbitrary-rule semantics oracle.

## Admission and limits

All semantic and bound checks must pass in every timed replicate. If a cell
fails, preserve it and mark that cell inadmissible for timing inference. The
result may support scaling only for this rule schema/topology and environment;
it cannot establish a polynomial wall-time bound, natural graph distribution,
dynamic-rule behavior, or unrestricted mint termination.
