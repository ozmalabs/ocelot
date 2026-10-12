# Response-priority residual-continuation v1.1 candidate: diagnostic result

Date: 2026-10-06  
Status: one-worker-per-arm diagnostic; parity gate failed.

## Result

The candidate deferred the six v1 ambient rules plus `retire_duplicate_gap`. It fixes the recurrence lifecycle: on turn zero both arms have 11 `GapRecurrence`, 11 `GapLearningAssessment`, and 11 `HumanReview` records after continuation. The priority write trace now orders `assess_compromised_boot`, recurrence registration, assessment, and review before `retire_duplicate_gap`, matching global closure. Replies match on all seven turns, and both arms reach zero dirty residual without a round cap.

Graph parity still fails on every turn. Priority is short by nine nodes after turn zero and the gap grows over the sequence. The missing records are the reply conceptualizer chain: `CommunicativeIntent`, `MessageShapeRequest`, `SystemModel`, `MessageShape`, `MonitorRequest`, `Verdict`, two `Committed` records, and `RuleFiringHistory`. Call instrumentation shows `conceptualize_reply` is invoked in both arms. In priority it returns with `intent=None` and `committed=None`; global returns a committed intent. No live `form_intent_*` or companion conceptualizer rules appear in the priority arm.

The event trace identifies the upstream difference: priority's `conceptualizer_live` `Observation` remains `pending`, while global decodes it. `ensure_conceptualizer_rules` reaches `induce_concern`, whose synchronous decode depends on the `sd_decode` family; those rules were in the deferred set. Consequently the induced residual is unavailable to `ground_concern`, so the conceptualizer composer does not author its rules. The ordinary answer text still comes from the existing adapter path, which is why reply text equality concealed this missing cognitive/graph work.

## Interpretation

Deferring duplicate retirement restores one required producer-consumer order, but the original six-rule ambient partition still defers structure acquisition that the held-topic response itself needs. This is not a successful priority result. The next candidate must keep the `sd_decode`, `sd_transform_decode`, and `sd_infer_dimension` rules foreground and defer only the other v1 housekeeping candidates plus duplicate retirement. That diagnostic will test whether response-critical structural induction and lifecycle cleanup are sufficient for graph parity.

## Artifacts

- [Candidate protocol](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_1_PREREG_20261006.md)
- [Candidate runner](../../../scripts/substrate_response_priority_residual_continuation_v1_1_candidate_20261006.py)
- [Source lock](../../../evaluation/substrate_capability/response_priority_residual_continuation_v1_1_candidate_20261006_lock.json)
- [Compact capture](../../../evaluation/reports/response_priority_residual_continuation_v1_1_candidate_20261006/capture.json.gz)
- [Turnwise analysis](../../../evaluation/reports/response_priority_residual_continuation_v1_1_candidate_20261006/analysis.json)

This pilot does not estimate natural-task prevalence or latency benefit. Keep the confirmatory multiworker gate closed.


## Correction after v1.2 API audit

The Python binding converted the canonical selected-area label `global` to a newly interned symbol rather than `Sym::default()`. Consequently, v1.1's selected arm did not select default-area rules. The recurrence lifecycle observations for explicitly reassigned named areas remain informative, but v1.1's missing-composer explanation is superseded and this run does not validate complete selected-area execution. The corrected binding and one-pair follow-up are reported in [v1.2 results](SUBSTRATE_RESPONSE_PRIORITY_RESIDUAL_CONTINUATION_V1_2_RESULTS_20261006.md).
