# Thoughtexperiment predecessor fanout edge-topology study v1

Date: 2026-10-04

## Question

At fixed node count and edge count, do unrelated background-edge layouts change
thoughtexperiment candidate-fanout lifecycle cost, allocation, or correctness?
This extends the previous node-scale sweep, whose background nodes had no
edges. It measures branch/snapshot and audit behavior; it does not test whether
the engine discovers cheap cuts or whether these layouts are natural task
graphs.

## Fixed design

Use 100,000 unrelated background nodes and 99,999 background edges, added to
the fixed 511-node/467-edge predecessor-fanout task fixture. Compare four
connected tree layouts: path, star, 100-star clusters joined by a path of
cluster centers, and a seeded random-recursive tree. All layouts have exactly
N−1 undirected-structure edges, all use the same edge type and empty attributes,
and none is in a task frame or participates in rule closure. Hold four
independent-state frames, four supplied candidate branches, the correct-candidate
schedule, and both snapshot backends fixed. Run three fresh processes per
topology/backend cell (24 workers); shuffle order with seed 20261007.

The source-locked lifecycle instrumentation records graph export, canonical
digest, candidate fork and existing phase costs, allocator residency, RSS/PSS,
and the semantic oracle checks. Summarize per-cell medians and ratios against
the existing 100k-node, 467-edge sparse-background study. Report setup time
separately from the lifecycle: constructing the noise topology is not charged
to candidate execution. Preserve raw worker records and worker failures.

## Gates

1. Lock this protocol, runner, analyzer, lifecycle instrumenter, current-source
   replay, engine/native/build inputs, and the prior 100k sparse-background
   capture/analysis before any worker starts.
2. Capture exactly 24 unique fresh workers in the fixed randomized schedule;
   require stable inputs and no dropped failures.
3. In every worker require exactly 100,511 nodes and 100,466 edges, four
   candidate outcomes, one correct grounded candidate, oracle/branch/primary
   parity, primary isolation before return, rule preservation, stale-return
   refusal, and quiescent closure.
4. Require five lifecycle graph exports and five canonical digests, nonnegative
   uninstrumented remainder, and exact setup edge count for the declared
   topology.
5. Independently recompute all checks and medians from the retained capture.

## Limits

Three replicates per cell on one host provide descriptive evidence only. The
background graph is intentionally unrelated to candidate closure, so results
measure graph representation/audit overhead under equal sparse density, not
inference locality, natural cheap-cut prevalence, concurrent throughput, or a
general complexity law. Instrumentation overhead remains subject to the prior
wide paired-control intervals.
