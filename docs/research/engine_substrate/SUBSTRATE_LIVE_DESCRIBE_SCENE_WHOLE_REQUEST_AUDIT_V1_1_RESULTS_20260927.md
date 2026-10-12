# Live describe-scene whole-request audit v1.1

Date: 2026-09-27

## Change from v1

The first full-request capture found that candidate attribution explicitly withdraws counts for colliding rule IDs, while Term attribution did not. I updated the native scale audit so per-rule accumulation skips ambiguous IDs, a collision withdraws all earlier rows for that ID, and `term_evals_unattributed` records evaluations with no unique active rule identity. This counter is meaningful when per-rule mode is enabled; it remains zero when that optional mode is off.

The engine was rebuilt with the repository build script. Release compilation completed successfully and the build provenance record was refreshed. The preregistered fixture, full-call audit interval, and paired parity gates were retained. The source lock includes the rebuilt native artifact.

## Replication result

Three fresh audited/uninstrumented pairs pass all 12 independent v1.1 gates, including stable source locks, exact public reply / Goal lifecycle / whole-graph parity, zero untraced instrumentation, complete zero-drop access traces, candidate conservation, Term conservation, and withdrawal of ambiguous rule rows.

| Measure | Audited count |
|---|---:|
| Candidate tests | 678,432 |
| Rule-attributed candidates | 678,013 |
| Unattributed candidates | 419 |
| Per-clause candidates | 678,013 |
| Term evaluations | 3,676,862 |
| Unambiguous per-rule Term evaluations | 3,674,401 |
| `term_evals_unattributed` | 2,461 |
| Selected access trace events | 1,140,892 |
| Access-trace rows | 53,215 |
| Rules with candidate work | 445 |

Both equations reconcile exactly:

- `678,432 = 678,013 + 419`
- `3,676,862 = 3,674,401 + 2,461 = sum(term_eval:<variant>)`

The audited and uninstrumented arms both end at 25,152 nodes and 11,701 edges with the same semantic graph digest and expected description. Median request wall/CPU is 16.918/16.862 seconds audited and 16.430/16.313 seconds uninstrumented. Treat the difference as fixture-specific instrumentation overhead, not a general latency estimate.

All six public replies match the expected text, but none is represented by a matching graph-visible outbound Message. This observation is reported separately from the passing parity and engine-accounting gates.

## Scope

This establishes reproducible, whole-request candidate and Term accounting for one serial full-seed `describe_scene` route. It does not measure learned frame locality, natural-task prevalence, scaling with graph/task size, or general capability. The trace count is a separate view of selected accesses and is not a candidate count.

Next measure controlled live-route size scaling and a second task topology. Keep the graph-visible reply projection as a separate correctness measure.

## Artifacts

- [v1 preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_WHOLE_REQUEST_AUDIT_V1_PREREG_20260927.md)
- [Native counter source](../../../runners/dsl/src/scale_audit.rs)
- [Runner](../../../scripts/substrate_live_describe_scene_whole_request_audit_v1.py)
- [v1.1 independent analyzer](../../../scripts/analyze_substrate_live_describe_scene_whole_request_audit_v1_1.py)
- [Rebuilt engine lock](../../../evaluation/substrate_capability/live_describe_scene_whole_request_audit_v1_1_lock_20260927.json)
- [Analysis](../../../evaluation/reports/live_describe_scene_whole_request_audit_v1_1_analysis_20260927.json)
- [Raw workers](../../../evaluation/reports/live_describe_scene_whole_request_audit_v1_1_workers_raw_20260927.json)

## Historical artifact note

The first v1 raw-worker file was overwritten in place by the post-fix capture before it had been copied. Its summary analysis and attribution-decomposition JSON remain, but its original raw rows are no longer in the worktree. Use the distinct v1.1 lock, driver report, and raw-worker artifact linked above for the rebuilt-engine result.
