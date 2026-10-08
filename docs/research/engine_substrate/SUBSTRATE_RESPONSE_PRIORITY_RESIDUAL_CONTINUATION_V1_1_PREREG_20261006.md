# Response-priority residual-continuation v1.1 candidate diagnostic

Date: 2026-10-06  
Status: preregistered one-worker-per-arm diagnostic; not confirmatory.

## Question

Does deferring `retire_duplicate_gap` together with the six v1 ambient rules preserve the consumer-before-retirement lifecycle and restore full graph parity after continuation?

## Arms

Use the same locked seven-turn held-topic workload, seed, facts, and host hooks as v1. The global arm uses existing closure. The candidate priority arm assigns `retire_duplicate_gap` in addition to `slang_variant_bind_denotes`, `curiosity_targets_ambivalent_nodes`, `gr_condition_lapse`, `sd_decode`, `sd_transform_decode`, and `sd_infer_dimension` to `ambient_work`. All other active rules are assigned to `response_critical`, with dynamically authored `global` rules included in selected foreground. After each response, run ordinary unbounded all-area continuation.

Run one worker per arm for this diagnostic, with `PYTHONHASHSEED=0`. Enable the native per-rule write journal only for the first turn and its continuation. Do not interpret wall time as a performance estimate. Preserve the complete event-family summaries, replies/outcome projection, selected-settlement trace, dirty residuals, and normalized graph fingerprints.

## Gates

1. Source and worker input hashes remain stable.
2. Replies and registered held-topic outcome projections match at all turns.
3. The candidate has no round-cap hits and reaches zero residual after continuation.
4. Semantic graph fingerprints and node/edge cardinalities match global after continuation at every turn.
5. The turn-zero write trace shows whether `register_gap_recurrence_identity`, `register_recurrent_gap_identity`, assessment, and review occur before `retire_duplicate_gap` in the candidate arm.

A pass is only a candidate diagnostic. It does not establish natural-task prevalence, a speedup, or general correctness. If graph parity fails, report the exact remaining event-family deltas; do not proceed to the three-worker v1 confirmatory panel. If parity passes, freeze this candidate and run an independently locked multiworker replication before making a scheduler claim.

For the diagnostic pilot, wrap `conceptualize_reply` to record whether the live reply path calls it, returns, or raises before the adapter's fail-closed fallback. Record the resulting `_last_reply_intent` readback for turn zero. This call tracing is outside performance claims and distinguishes remaining graph differences caused by a skipped/failed host bridge from rule-schedule differences.

## Rationale and limits

The v1 native write trace showed global processing boot-integrity concerns into recurrence and review records before duplicate retirement, while priority retired first. This candidate tests the minimal dependency-preserving scheduling change suggested by that trace. It leaves the other six ambient rules deferred, so a pass would be evidence for this one dependency fix only.
