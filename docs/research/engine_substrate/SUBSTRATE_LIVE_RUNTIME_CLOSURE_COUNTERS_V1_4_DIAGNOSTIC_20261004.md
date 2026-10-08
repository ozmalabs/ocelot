# Live runtime closure counters v1.4 diagnostic

Date: 2026-10-04

## Capture integrity

The v1.4 runner completed all six workers in the preregistered three-replicate by two-mode design. Start and finish fingerprints match; the corrected parent gate recognizes the actual top-level worker payload; all 12 request records are present. Task projections, replies, and semantic graph digests match across workers and paired modes. All 4,788 runtime RuleUID observations resolve to exported rule definitions.

## Attribution outcome

The namespace repair fixes the original rule-index collision in the measured panel: the analyzer finds no ambiguous metadata, no unattributed candidate tests, and per-rule, per-clause, semantic-edge, and global candidate totals conserve. The `(audit_id, store_id, local_rule_index)` snapshots are present for the audit-on requests.

The measurement gates still fail in two places:

- All three audit-off workers record work on their first prompt (`report your organisation`): 8,099 candidate tests, 86,114 Term evaluations, and 2,340 metadata/identity rows. Their second prompt has all-zero counters and empty audit tables. This means the intended audit-off condition is not holding for the first live request, despite the preregistered two-substrate PyO3 isolation control passing.
- Each audit-on second prompt (`describe who you are`) records 134 Term evaluations as unattributed. Candidate tests are fully attributed, but complete Term-cost attribution does not yet conserve.

Therefore v1.4 is a successful capture of task/runtime parity and a partial pass of matcher attribution, but it is not a valid per-rule natural workload cost result. Do not infer an audit-on/off cost difference from it.

## Next action

Trace the audit mode at the worker boundary and through first-request initialization, including the active Python thread and the native instance that owns `agent.inner`. Find why the first request records despite the off setup; add a focused regression gate for that exact transition. Separately trace the 134 unattributed Term evaluations to their call sites and decide whether to propagate the matcher context or report them as intentionally outside rule attribution. Do not repeat the live panel until both issues have a source-level explanation and their controls pass.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_4_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_4.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_4.py)
- [Lock](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_4_lock_20261004.json)
- [Compressed six-worker capture](../../../evaluation/reports/live_runtime_closure_counters_v1_4_20261004.json.gz)
- [Analysis](../../../evaluation/reports/live_runtime_closure_counters_v1_4_analysis_20261004.json)

Claim boundary: one selected authored two-request route. Its task and graph parity gates pass, and candidate attribution is conserved on audit-on requests. Audit-off isolation and Term attribution fail; no natural-workload tractability estimate follows.
