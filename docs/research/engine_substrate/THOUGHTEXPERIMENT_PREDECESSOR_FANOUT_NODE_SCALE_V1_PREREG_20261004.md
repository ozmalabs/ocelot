# Thoughtexperiment predecessor fanout node scale v1

Date: 2026-10-04

## Question

How do lifecycle, graph-export, canonical-digest, candidate-fork, and process
memory costs change with unrelated graph size for the same predecessor-based
thoughtexperiment workload?

## Fixed design

Measure 10,000, 100,000, and 200,000 unrelated noise nodes. Hold four frames,
independent discourse states, four supplied candidate branches, and the task
rule/evidence constant. Use both full-copy and shared-graph-page backends and
three fresh-process replicates per cell (18 workers total). All workers use the
same lifecycle-bounded export/digest instrumentation as the prior cost
breakdown. Randomize the 18-cell order with `random.Random(20261006).shuffle`;
record the schedule before execution.

Capture actual graph node/edge counts, candidate outcomes, oracle and primary
parity, source revision, full-copy/shared fork timings, graph export and digest
calls/times, existing phase timers, allocator samples, and RSS/PSS fields from
the base worker. Primary scaling summaries are per-backend medians and the
10k→100k and 100k→200k ratios for lifecycle, export, digest, and fork times.
Report memory at baseline/retained/after-return/after-drop. Keep all costs
separate; the on/off control intervals from the preceding study are too broad
to justify a precise instrumentation correction.

## Gates

1. Pre-run source lock covers this protocol, runner, analyzer, prior cost
   instrumenter and capture/analysis, current-source replay, engine/build
   hashes, and repository commit.
2. Capture exactly 18 unique workers, preserve failures, and verify stable
   sources and the preregistered randomized schedule.
3. Require the unique correct candidate, exact candidate outcomes, branch and
   primary parity with the monolithic oracle, primary isolation, active-rule
   preservation, stale retry rejection, and quiescent closure in every row.
4. Require exactly five graph exports and five digests within each measured
   lifecycle and nonnegative component remainder.
5. Independent analysis recomputes all ratios, summaries, provenance, and
   semantic checks from raw worker records.

## Limits

This is an authored graph with unrelated isolated nodes, not a natural task
graph or a test of edge-density/topology scaling. Three replicates per cell
provide descriptive scaling evidence only. The instrumentation overhead
remains uncertain, so absolute export/digest times are not corrected. No
concurrent fanout, candidate-generation, or general complexity claim follows.
