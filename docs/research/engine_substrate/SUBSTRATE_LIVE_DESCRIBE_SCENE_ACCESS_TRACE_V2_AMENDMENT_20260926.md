# Live `describe_scene` access trace v2 amendment (2026-09-26)

## Question

Measure selected native work separately for each serialized request, estimate instrumentation overhead against untraced twins, and verify whole-graph semantic parity under the existing two-thread schedule.

## Design

Run three labeled replicates in six fresh worker processes: one traced and one untraced arm per replicate, with arm execution order shuffled deterministically. Each process boots the same seeds and authored scene, then runs the same A/B schedule. Pair arms by replicate label. In the traced arm, reset and enable the process-global native trace only after a request acquires the conversation lock; disable and snapshot it immediately before that lock is released. This interval captures one request at a time and excludes the competing request while it waits. Record wall and calling-thread CPU time for both complete `converse` calls and trace interval durations/counts for traced calls.

## Gates

Require six distinct processes, stable source/build inputs, joined threads, successful original serialization and lifecycle gates, exact per-pair replies/event rows/Goal projections/task cuts, and a SHA-256 match of the canonical whole-graph semantic projection. That projection includes every node ID, type, stable attribute, and typed edge; it removes only `ts` and `runtime_s` attributes on `SystemModel` diagnostics because those record wall-clock execution metadata. Preserve the full raw-graph hash too so this normalization remains explicit. Require exactly two nonempty per-request traces with zero dropped events in traced workers and no trace rows in untraced workers. Reconcile combined trace counts with A+B intervals. Compare timing medians descriptively; with three pairs, do not claim a general or precise overhead factor.

## Limits

The trace is a selected-operation diagnostic with known blind spots. Lock-delimited intervals are per request but include all native work triggered synchronously while that request owns the conversation lock. Traced and untraced processes are fresh twins, not repeated arms on one graph; graph-hash parity is the control for initial setup and final state. Timing also includes process scheduling and is specific to this fixture. This probe does not implement partitioned closure, test natural-task prevalence, or establish a tractability class.

## Reproduction

Freeze `evaluation/substrate_capability/live_describe_scene_access_trace_v2_lock_20260926.json` from `scripts/substrate_live_describe_scene_access_trace_v2.py --lock`, then run the runner normally with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. It writes paired worker records and a summarized report under `evaluation/reports/`.
