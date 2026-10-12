# Thoughtexperiment predecessor fanout node scale v2 preregistration

Date: 2026-10-04

## Question

How do lifecycle, export/digest, branch-fork, and memory costs scale from 200,000 through 1,000,000 unrelated graph nodes for a fixed predecessor-based thoughtexperiment workload? Does shared graph-page CoW preserve semantic outcomes and isolation at that scale?

## Design

Use 200,000, 400,000, and 1,000,000 noise nodes, four independent-state frames, four supplied candidate branches, the fixed 467-edge task structure, and both `full_copy` and `shared_graph_pages` backends. Run two fresh-process replicates per cell (12 workers), with the order frozen by `random.Random(20261007).shuffle`. Retain the prior lifecycle-bounded export/digest instrumentation and allocator/RSS/PSS observations. Compare the 200k→400k and 400k→1m ratios for lifecycle, export, digest, candidate-fork, and retained allocator growth. Include branch-retained and post-drop memory; report all measurements without correcting for instrumentation overhead.

## Gates

1. Before capture, lock the protocol, runner, analyzer, instrumenter, current-source replay and its lock/capture/analysis, engine/build identity, and the full randomized configuration schedule.
2. Capture 12 unique workers with no failures; require the locked schedule and source stability before and after.
3. For every worker, require the unique correct supplied candidate, exact monolithic-oracle parity, branch/primary isolation, active-rule preservation, stale-residual rejection, and quiescence.
4. Require 5 graph exports and 5 canonical digests within each timed lifecycle, exact graph sizes/edge counts, and nonnegative unaccounted remainder.
5. Independently recompute all gate results, per-cell medians, scale ratios, and memory summaries from raw worker records.

## Claim boundary

This is a sparse synthetic graph with unrelated noise nodes, one host, and two workers per cell. It does not measure natural task graphs, candidate generation quality, concurrent fanout, or a general complexity law. At one million nodes this is a large-scale single-process engineering point, not evidence of useful throughput under memory contention. Existing instrumentation-on/off intervals remain broad, so export/digest components are descriptive.
