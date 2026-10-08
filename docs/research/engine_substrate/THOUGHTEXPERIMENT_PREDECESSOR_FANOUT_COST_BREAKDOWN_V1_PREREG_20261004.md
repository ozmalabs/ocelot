# Thoughtexperiment predecessor fanout cost breakdown v1

Date: 2026-10-04

## Question

Within the four-frame/four-candidate/100,000-noise-node fanout workload, how
much lifecycle time is spent exporting graph dictionaries and computing
canonical graph digests, in addition to the pre-existing named phase timers?

## Design

Repeat the exact six configurations in the source-locked current-source replay:
four independent-state frames, four candidates, 100,000 unrelated nodes, three
fresh-process replicates, and both full-copy/shared-graph-page backends. The
new worker reuses the v1.1 workload unchanged and instruments the Python
`Substrate.graph_to_dict` wrapper and `canonical_graph_digest` calls only while
the base worker's `lifecycle_start`/`lifecycle_ns` interval is active. The
instrumented timer delegates to the original monotonic clock. Existing named
phase timers remain unchanged.

Report three disjoint categories: named phase timer sum; graph-export time;
canonical digest time. Report lifecycle time minus those three categories as
the remaining unattributed time. The instrumentation wrappers must not include
their own clock reads in their accumulated intervals. Every worker still has to
pass the same candidate, closure, oracle parity, isolation, rule preservation,
and stale-return checks. Timing decomposition is accepted only if component
sums do not exceed lifecycle time and source hashes remain stable.

## Gates and limits

Lock the preregistration, runner, analyzer, the exact v1 replay and capture,
v1.1 worker/analyzer, native engine/build sources, and source commit before
capture. Recompute the lock after capture and in the independent analyzer. This
is one authored workload on one host; timer interception adds small overhead,
which is reported as a single-instrumented-run limitation. The results will
not justify causal attribution beyond the directly timed Python graph-export
and canonical-digest functions, nor a speedup or scaling claim.

## Artifacts

- Runner: `evaluation/substrate_capability/thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_thoughtexperiment_predecessor_fanout_cost_breakdown_v1.py`
- Lock and capture: corresponding `evaluation/substrate_capability/*lock*` and `evaluation/reports/*20261004.json`
