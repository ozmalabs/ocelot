# Live runtime store states v1.2 results

## Result

The source-locked replicate-0, audit-on capture completed for both requests. Task projection, replies, final semantic graph digest, and behavioral counter rows match the v1.6 parent. The parity comparison retains every raw counter in the output and excludes only explicitly timed global metrics ending in `_ns` plus `scheduler_plan_ns`, which varied across repeat runs.

Fourteen per-request store snapshots decode and pass SHA-256 and graph referential-integrity checks. Together they contain 50,121 nodes, 22,794 edges, and 4,758 rule rows (216,311,056 uncompressed bytes; 16 MB on disk). The independent analyzer reconciles all 4,745 process-wide matcher identities to captured `(store_id, local_rule_index)` slots; zero are unmatched. Two scoped stores expose disjoint rule slices across matcher entries. The opt-in native recorder therefore retains the first graph seen per store and accumulates distinct rule slots across the request.

The initial v1.1 capture is retained as a diagnostic: it captured 14 valid stores but left eight rule slots unmatched because it stopped at each store's first rule slice. V1.2's cumulative recorder closes that coverage gap on this route.

## Evidence chain

- Protocol: [v1.2 preregistration](SUBSTRATE_LIVE_RUNTIME_STORE_STATES_V1_2_PREREG_20261004.md)
- Native implementation: `runners/dsl/src/scale_audit.rs`, `runners/dsl/src/substrate.rs`, `runners/dsl/src/rewrite.rs`, and `runners/dsl/src/py.rs`
- Runner and source lock: [runner](../../../evaluation/substrate_capability/live_runtime_store_states_v1_2.py), [lock](../../../evaluation/substrate_capability/live_runtime_store_states_v1_2_lock_20261004.json)
- Capture: [request/store manifest](../../../evaluation/reports/live_runtime_store_states_v1_2_20261004.json) and [compressed store payloads](../../../evaluation/reports/live_runtime_store_states_v1_2_payloads/)
- Independent analysis: [analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_store_states_v1_2.py), [analysis](../../../evaluation/reports/live_runtime_store_states_v1_2_analysis_20261004.json)
- Engine build: source-matched release engine `acceedec9576`; current source-lock inputs match the capture's start and post-run hashes.

## Limits and next work

This is one authored route, one replicate, and two requests. The snapshot graph is the first graph observed at matcher entry, while rule slots are accumulated across that request; this is not a simultaneous prompt-boundary image for every secondary store. Identity coverage does not yet prove that every captured rule definition is behaviorally replayable or that its measured work can be independently reproduced store by store. Next build a replay harness from these store payloads and reconcile per-store work to request totals, then repeat across more routes and replicates before claiming broad runtime coverage or tractability.
