# Live describe-scene whole-request audit v1

> **Superseded by v1.1:** the native audit now withdraws Term counts for ambiguous IDs and exposes no-rule/ambiguous work through `term_evals_unattributed`. The rebuilt-engine replication passes the updated conservation gates; see [v1.1 results](SUBSTRATE_LIVE_DESCRIBE_SCENE_WHOLE_REQUEST_AUDIT_V1_1_RESULTS_20260927.md). The original v1 raw-worker file and lock were overwritten before archival; the summary analysis and decomposition remain, but the original raw rows and lock are unavailable, so the preliminary capture is not independently reproducible from current artifacts.

Date: 2026-09-27

## Question and method

This experiment extends native work attribution from three Goal-event producer closures to the entire `WorldAdapter.converse` call. Three fresh source-locked pairs each booted the full seed profile, attached the same three-Percept Scene, and submitted one `describe what you see` instruction. One arm enabled global/per-rule scale counters and native access tracing immediately around the complete call; the paired arm ran with all instrumentation off. Both arms recorded public output, Goal lifecycle, and a semantic digest of the whole final graph.

## Outcome

Six distinct workers completed, source hashes remained stable, and all three audited/uninstrumented pairs matched exactly on reply, Goal lifecycle, graph node/edge counts, and semantic digest. Every arm produced the expected resolved `selection → execution → action_result` Goal. Each final graph had 25,152 nodes and 11,701 edges. The repeated digest was `88bcd1ed3fcd07e17b326a01c6e89313e23b3d153e8b77a1415ddb6655f607bb`.

Whole-request work reproduced exactly in all audited workers:

| Measure | Count |
|---|---:|
| Candidate tests | 678,432 |
| Candidate tests attributed to rules | 678,013 |
| Candidate tests unattributed | 419 |
| Per-clause candidate tests | 678,013 |
| Global Term evaluations | 3,676,862 |
| Raw per-rule Term rows | 3,676,109 |
| Term-kind evaluations | 3,676,862 |
| Selected access trace events | 1,140,892 |
| Access-trace rows | 53,215 |
| Rules with candidate work | 445 |

Candidate totals satisfy `678,432 = 678,013 + 419`; per-rule and per-clause candidate sums both equal the attributed total. A source-linked post-hoc decomposition finds nine ambiguous native rule IDs. Candidate attribution correctly withdraws all candidate rows for these IDs, while Term attribution does not. Of the raw 3,676,109 per-rule Term rows, 1,708 sit under ambiguous IDs; the remaining 3,674,401 belong to unambiguous IDs. Another 753 global Term evaluations have no per-rule row, consistent with the source's `CURRENT_RULE == NO_RULE` path in `per_rule_bump`. The decomposition `3,674,401 + 1,708 + 753 = 3,676,862` exactly reconciles the global total, but the preregistered per-rule Term attribution gate fails because the audit does not withdraw ambiguous Term rows or expose a dedicated no-rule counter. This is an instrumentation attribution limit, not missing global Term work. Access events and candidate tests are separate measures and must not be equated.

Instrumented medians are 16.787 s wall and 16.694 s process CPU; uninstrumented medians are 15.845 s wall and 15.783 s process CPU. These paired fixture measurements suggest roughly 6% instrumentation overhead for this capture, but are not broad performance estimates.

All six public replies match the expected description, while none has a matching graph-visible outbound Message. The behavioral output-alignment issue remains distinct from the passing audited/uninstrumented parity gates.

## Interpretation

This is complete measured candidate/Term work for one serial full-seed live route, with exact final-graph and response parity under the current source lock. Unlike the earlier helper-only audit, the counters wrap the entire `converse` call. Candidate attribution is exact except for 419 explicitly reported unattributed tests. Global Term totals are exact; rule-level Term attribution is nearly complete but does not pass its gate. The run does not establish frame locality, natural workload prevalence, scaling, or general task capability. The profile is one synthetic attached-scene prompt, and the route's graph-visible output remains incomplete.

Next, make per-rule Term attribution apply the same ambiguity poisoning used for candidates and expose the no-rule Term count; the 419 candidate tests are already explicitly attributed to that counter's unattributed bucket, while the nine conflicting IDs explain why those tests are withheld. Then trace the public reply-to-Message path. Once counters and outputs reconcile, vary Scene/percept and Concept membership sizes on this live full-rule route and include a second independently authored task topology.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_WHOLE_REQUEST_AUDIT_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_live_describe_scene_whole_request_audit_v1.py)
- [Historical analysis](../../../evaluation/reports/live_describe_scene_whole_request_audit_v1_analysis_20260927.json)
- [Attribution decomposition report](../../../evaluation/reports/live_describe_scene_whole_request_audit_v1_attribution_residue_20260927.json)
