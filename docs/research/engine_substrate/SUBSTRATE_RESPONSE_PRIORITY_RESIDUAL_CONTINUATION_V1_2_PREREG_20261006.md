# Response-priority residual-continuation v1.2 candidate diagnostic

Date: 2026-10-06  
Status: preregistered one-worker-per-arm diagnostic; not confirmatory.

## Question

Does keeping structure-decoding rules in the foreground while deferring the housekeeping candidates and duplicate retirement preserve reply conceptualization and full graph parity after continuation?

## Arms

Use the same source-locked seven-turn held-topic workload, seed, facts, and original adapter hooks. Global closure is unchanged. The candidate priority arm assigns only these four rules to `ambient_work`: `slang_variant_bind_denotes`, `curiosity_targets_ambivalent_nodes`, `gr_condition_lapse`, and `retire_duplicate_gap`. In particular, `sd_decode`, `sd_transform_decode`, and `sd_infer_dimension` remain foreground with all other nonambient rules. Dynamically authored `global` rules remain selected. Run ordinary unbounded all-area continuation after each response.

Run one worker per arm with `PYTHONHASHSEED=0`. Enable the rule-write journal on turn zero and continuation, and record the `conceptualize_reply` call outcome, `_last_reply_intent`, and live conceptualizer rule-area readback. These diagnostics are outside any performance claim.

## Gates

1. Source and worker input hashes remain stable.
2. The selected-area API round-trips the canonical `global` area label to `Sym::default()`; when dynamic conceptualizer rules are authored, no unexplained `global` dirty residual remains after selected settling.
3. Replies and registered held-topic outcome projections match at every turn.
4. Conceptualizer intent and commitment are present when global has them; event-state summaries show no unexplained pending request/observation.
5. Both arms finish continuation without a round cap and with zero residual.
6. Normalized graph fingerprints and node/edge cardinalities match after continuation at all seven turns.
7. Turn-zero rule-write order preserves both structure decoding before composer induction and recurrence consumers before duplicate retirement.
8. Selected settlement contributes its last progressing rule to the same turn-scoped firing-history capture used by global closure; resulting ledger presence, last rule, and settlement sequence agree after continuation.

This is a one-pair candidate diagnostic only. Failure keeps the three-worker confirmatory panel closed. A pass requires an independently locked multiworker replication before any scheduler claim. Do not use its instrumented wall times as a speed estimate.
