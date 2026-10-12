# Thoughtexperiment predecessor fanout instrumentation overhead v1

Date: 2026-10-04

## Question

Does wrapping `Substrate.graph_to_dict` and `canonical_graph_digest` to time
them materially change lifecycle cost or semantic outcomes in the source-locked
100k-node thoughtexperiment workload?

## Fixed design

Run a matched on/off pair for each of three replicates and two snapshot
backends: four independent-state frames, four candidates, and 100,000 unrelated
nodes. This produces 12 fresh-process workers. The instrumented arm uses the
existing cost-breakdown wrapper; the off arm invokes the exact v1.1 worker
without wrappers. Within each backend/replicate pair, arm order is randomized
using Python `random.Random(20261004).shuffle` over the fixed six pairs. Record
the schedule in the capture.

Primary outcome is paired lifecycle time, with on/off ratio and absolute delta
reported separately for each backend and as the median of three pairs. Also
require exact candidate outcomes, canonical graph/oracle parity, branch
isolation, stale-return refusal, rule preservation, and closure quiescence in
both arms. Report the on-arm graph export/digest components, but do not use the
on arm alone to estimate an uninstrumented speed profile.

## Gates

Pre-run lock includes this protocol, runner, analyzer, both prior locked
replays, their captures/analyses/locks, engine/build sources, and repository
commit. Capture all 12 workers and preserve failures. Recompute the lock before
and after the run. Independent analysis verifies pairing, schedule, semantics,
and calculations.

## Limits

Three pairs per backend provide a small instrumentation diagnostic, not a
universal overhead factor. The wrapper may affect dispatch as well as clock
reads. No graph-size scaling or natural-task prevalence is measured.
