# Thoughtexperiment persistent adoption v1 preregistration

## Question

After revision-checked activation, do selected recurrence and conversation
repairs remain useful on a second sequential batch in the same substrate? Can
a detected regression from a deliberately wrong guard be rolled back to the
captured source rule?

## Design

Use four workers in each authored family. Activate each previously selected
guard in a fresh faulted context, run the registered first batch, then run a
second batch without rebuilding the substrate. Recurrence's second batch adds
a new episode and candidate; conversation reuses the same WorldAdapter for its
held-out utterance batch. Require the intended output counts on both batches.

For each recurrence worker, separately activate the known agent-wide guard
that failed recurrence transfer in the prior panel. Its first case must fail
the two-candidate output oracle. Treat that observed failure as the rollback
trigger, replace the bad successor with the captured original source rule
using the current semantic revision, and require the repaired recurrence
oracle to pass.

Lock runner, analyzer, this protocol, prior candidate generator and captures,
domain/native interfaces, and native binary before capture. This is a
harness-driven persistence and rollback test; it does not test autonomous
regression detection, decision thresholds, or deployment-wide authorization.
