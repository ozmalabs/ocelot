# Event-reasoning Stage A envelope v1.1 results

## Result

The provenance-only v1.1 rerun passes all nine runner gates and all fourteen independent analysis checks across 30 cells, six fresh workers, five entity counts, and three arm orders per replicate. Ordinary closure and Stage-A-enabled closure agree exactly on full graph state, progress, terminal status, and the independent entity-state oracle. All arms settle; source inputs remain stable. Each cell has three eligible drains, zero excluded drains, and zero conflict fallbacks; Stage A proposals scale as `3N`.

At N=1/4/16/64/256, the median Stage-A-to-ordinary wall-time ratios are 1.27×/1.20×/1.65×/1.52×/2.35×. This path captures and serially commits proposals, so the result is overhead without parallel speedup. Six replicates support descriptive workload-specific ratios only.

The new manifest records current engine provenance and explicit runner/protocol/seed/loader/source/analyzer hashes. The independent analyzer validates all explicit hashes, the parent stdout/stderr log, and each worker's stdout and empty stderr hashes. The original v1 record remains unchanged.

## Limits

This is an authored independent-entity rule family. It measures admission, fallback, semantic parity, and descriptive proposal-path cost; it does not estimate Stage A eligibility or fallback prevalence on natural workloads, demonstrate acceleration, or prove general scheduler completeness. Shared Stage-A eligible rules with meaningful overlap and coupled task graphs remain open.

## Artifacts

- Provenance amendment: [v1.1 amendment](SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_V1_1_AMENDMENT_20260926.md)
- Original design: [v1 preregistration](SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_PREREG_20260926.md)
- Runner: [`substrate_event_reasoning_stage_a_envelope_v1.py`](../../../scripts/substrate_event_reasoning_stage_a_envelope_v1.py)
- Independent analyzer: [`analyze_substrate_event_reasoning_stage_a_envelope_v1_1.py`](../../../scripts/analyze_substrate_event_reasoning_stage_a_envelope_v1_1.py)
- Current-source lock: [v1.1 lock](../../../evaluation/substrate_capability/event_reasoning_stage_a_envelope_v1_1_lock_20260926.json)
- Raw workers and manifest: [v1.1 report](../../../evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_1_20260926.json)
- Independent analysis: [v1.1 analysis](../../../evaluation/reports/substrate_event_reasoning_stage_a_envelope_v1_1_analysis_20260926.json)
- Parent process log: [stdout/stderr](../../../evaluation/run_logs/substrate-event-reasoning-stage-a-envelope-v1-1-20260926.stdout_stderr.log)
- Preserved original: [v1 results](SUBSTRATE_EVENT_REASONING_STAGE_A_ENVELOPE_V1_RESULTS_20260926.md)
