# Thoughtexperiment touched-object parity audit v1

Date: 2026-10-04

## Question

Can the thought-experiment return path replace a repeated whole-graph parity
audit with exact validation of the objects named in the mutation journal, and
what divergence can that local check miss?

## Workload and arms

Replay the current predecessor-fanout task at 10k/100k/200k unrelated isolated
nodes, both full-copy and shared-page backends, three fresh processes per cell
(18 workers). Keep four independent-state frames and four supplied candidates.
The existing lifecycle returns the unique valid residual to primary and
compares canonical full-graph digests of the selected branch and returned
primary. Add a validator that captures full before-images only for
`nodes_changed`, applies the journal delta, reconstructs each full expected
touched node from its preimage and journaled attr/type patch, and compares that
node's full type/attribute map with primary. It refuses unsupported delta
shapes (node add/remove or any edge add/remove/change) rather than silently
claiming coverage. Record preimage capture and post-apply validation time
separately from graph application and lifecycle timing.

For replicate zero in each size/backend cell, make a second shared-page scratch
fork after successful adoption, change one unrelated noise-node attribute
outside the journal, and compare: (a) touched-object projection versus the
valid residual (expected to pass because the changed object is outside its
scope), and (b) exact canonical graph digest versus the selected branch
(expected to fail). This explicit control bounds the guarantee: touched-object
equality does not establish whole-graph equality in the presence of
unjournaled/out-of-scope mutation.

## Measures and gates

Capture graph exports and canonical digests individually so the exact full
parity audit cost can be reconstructed from the selected-branch export/digest
plus the returned-primary export/digest. Also capture targeted preimage and
post-validation times, touched-object/attribute counts, retained allocator and
RSS/PSS fields, and the scratch-control outcome. Report medians by size and
backend, full-audit/touched-audit cost ratios, and scaling ratios. Compare
against the node-scale baseline at matching graph sizes.

1. Lock this protocol, runner, analyzer, prior lifecycle instrumenter,
   current-source replay, native/build inputs, and baseline capture/analysis.
2. Require 18 unique fresh workers and exact randomized schedule, stable source
   lock, complete capture, and zero worker failures.
3. Every worker must preserve unique correct candidate selection, exact
   selected branch/primary/monolithic-oracle parity, pre-return primary
   isolation, active-rule preservation, stale-retry atomic refusal, and scoped
   quiescence.
4. Require every successful residual to fit the preregistered touched-node-only
   shape; touched full-object reconstruction must match after return in all 18
   workers. Reject the touched-audit result if unsupported delta rows exist.
5. All six scratch controls must show touched projection passes and exact
   whole-graph digest detects the injected unrelated mutation.
6. Require five graph exports/digests in each original lifecycle and
   nonnegative timing remainder. Scratch falsification costs are reported
   outside lifecycle.
7. Independent analysis recomputes every gate, audit cost, ratio, and summary
   from raw worker rows.

## Claim limits

This tests validation of the journal's changed-node projection on one authored
task family. The scratch control is expected to demonstrate that this is a
conditional residual-consistency check, not a replacement for exact global
parity where untracked or unrelated state changes are possible. No general
engine guarantee, edge mutation validation, natural task transfer, or broad
complexity claim follows. The prior eight-pair instrumentation control has
wide intervals; timer shares remain descriptive.
