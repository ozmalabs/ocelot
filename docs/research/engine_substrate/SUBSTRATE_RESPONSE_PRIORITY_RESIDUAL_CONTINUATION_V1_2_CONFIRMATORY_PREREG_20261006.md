# Response-priority residual-continuation v1.2 confirmatory replication preregistration

Date: 2026-10-06  
Status: preregistered three-worker-per-arm confirmation; instrumented costs are descriptive only.

## Question

Does the v1.2 priority partition preserve finite-turn response and post-continuation graph outcomes after fixing canonical `global` area selection and selected-scheduler firing-history capture?

## Locked design

Use the same seven-turn held-topic workload, facts, seed, adapter hooks, arm definitions, rule attribution, and `PYTHONHASHSEED=0` as the passing v1.2 pair. Global closure remains unchanged. In the priority arm, assign only `slang_variant_bind_denotes`, `curiosity_targets_ambivalent_nodes`, `gr_condition_lapse`, and `retire_duplicate_gap` to `ambient_work`; run `response_critical` and canonical `global` during response, then perform unbounded all-area continuation. Run three fresh workers per arm in a fixed arm/replicate order, six workers total. Preserve worker outputs and locked source/input fingerprints. Do not use the trace-instrumented elapsed times to claim a speed benefit.

## Gates

1. The six-worker capture matches the source lock and all workers report stable inputs and `PYTHONHASHSEED=0`.
2. All workers complete all seven turns with selected `global` readback, committed composer intent when global commits, and zero continuation residual without round-cap hits.
3. Reply and registered held-topic projections match between arms at each turn, with within-arm worker repeatability.
4. Normalized graph fingerprints and node/edge cardinalities match between arms and repeat within each arm at every turn.
5. Turn-scoped firing-history ledger fields (presence, last rule, and settlement sequence) match between arms at every turn.

A failed gate closes any scheduler-performance claim and triggers a discrepancy audit. A full pass supports only finite semantic parity for this held-topic workload and partition. It does not establish a general speedup, natural-task prevalence, or tractability of structure induction.

## Artifacts

Runner: `scripts/substrate_response_priority_residual_continuation_v1_2_confirmatory_20261006.py`  
Capture: `evaluation/reports/response_priority_residual_continuation_v1_2_confirmatory_20261006/capture.json.gz`  
Lock: `evaluation/substrate_capability/response_priority_residual_continuation_v1_2_confirmatory_20261006_lock.json`
