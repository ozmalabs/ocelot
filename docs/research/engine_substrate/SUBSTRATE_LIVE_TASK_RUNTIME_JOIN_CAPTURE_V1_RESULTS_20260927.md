# Live task runtime join-work capture v1 results

Date: 2026-09-27 local

## Capture integrity and task outcome

Three fresh current-source workers completed the frozen two-request `describe_scene` schedule. The v1.2 independent analysis passes all **52 capture-integrity checks**: source/native identity is stable, RuleIdx patterns align with per-event native counters, candidate tests conserve to global counters, threads and event ordering pass, goal identity/lifecycle pass, and all workers reproduce the same semantic final graph. The representative runtime graph captured before request B's `action_result` event has 25,142 nodes and 11,762 edges; its exact canonical graph digest is identical in all three workers.

The separate legacy reply gate **fails**. Request B returns the expected description, while request A returns: “I understood that as an instruction to describe 'see', but I hold no faculty for it yet -- I've filed it as a gap to work on.” All three workers reproduce this same A/B reply pair. Therefore this is admitted only as a current runtime work and task-failure characterization; it is not a passing `describe_scene` capability result. The observed A reply change is not attributed to a particular source modification by this capture.

## Full-call timing available in the capture

The same raw capture records `converse` wall and calling-thread CPU time for both requests. Across three workers, request A has median wall time 20.66 s (19.47–20.72 s) and median thread CPU 20.57 s (19.39–20.58 s). Request B has median wall time 18.13 s (17.37–18.29 s) and median thread CPU 11.44 s (11.12–11.74 s). The roughly 6.7 s median B wall/CPU gap is consistent with waiting or other off-thread time in this serialized fixture, whose harness deliberately exercises the conversation lock. These values include the per-event audit instrumentation and do not isolate engine matcher time, establish uninstrumented latency, or measure throughput. They are useful as an end-to-end diagnostic baseline for a future whole-request counter capture.

## Runtime multi-edge work

The selected full profile starts with 2,316 active rule slots. During the six measured producer-event closures (three each for A and B), the event-time store grows to 2,334 slots for A and 2,340 by B. Each worker records 337,540 native candidate tests across these six closures (1,012,620 across all three workers). The original v1 analyzer attributed 872,946 tests to two-clause rules, 133,044 to one-clause rules, and 2,210 to rules with at least three clauses per worker. These arity shares are superseded by [the attribution amendment](SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_ATTRIBUTION_AMENDMENT_20260927.md): a subsequent request-level audit exposed thread-local RuleIdx attribution anomalies on Rayon work, so these breakdowns should not be treated as validated rule arity evidence.

The v1 event-time snapshots join names to RuleIdx values, but the follow-up anomaly means these named per-rule rankings remain provisional wherever parallel matcher work can inherit stale thread-local context.

## Exact runtime graph check

An independent enumerator checks `rule_intent_about_mentioned_concept` against the captured pre-action graph. Its installed pattern is:

`m -has_intent→ intent`, `m -has_mention→ mention`, `mention -refers_to→ c`.

The snapshot contains 2, 8, and 22 edges for those relations. Source-bound expansion therefore scans 2 candidates at clause one, 8 at clause two, and 22 at clause three: **32 candidate visits per pass**, yielding 22 complete bindings. At request B's action-result closure, the recorded native rule counter is 64 candidates over two scheduler passes, matching the independent 32×2 calculation in all three workers. The separate runtime graph analyzer passes all 6 checks. Because later evidence shows RuleIdx attribution can be inconsistent on Rayon paths, that native-to-rule comparison is provisional until the rule is confirmed to use the serial matcher path or the audit context is repaired; the graph enumeration itself remains independently valid.

## Interpretation and limits

This capture establishes a reproducible runtime graph snapshot and an independent graph-level join enumeration. Its general per-rule attribution claims are superseded by the later audit amendment. It also exposes a current reply-quality gate failure and dynamic addition of rule slots during the task. Multi-edge clauses account for a small part of candidate tests in the six selected producer closures; this does not establish where the remaining work goes across the entire request.

The arity distribution says the next attribution should focus first on binary match work, while the six-closure boundary still leaves internal request work unmeasured. The next measurement should attribute candidate work across the full request boundary, including internal closure outside `_record_live_goal_event`, while preserving the reply failure as a separate task-quality issue. Then repeat the exact-graph join calculation for a second runtime rule with different arity and verify its read/write and effect semantics.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_PREREG_20260927.md)
- [Amendment: reply-gate failure reporting](SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_AMENDMENT_20260927.md)
- [Analysis correction amendment](SUBSTRATE_LIVE_TASK_RUNTIME_JOIN_CAPTURE_V1_ANALYSIS_AMENDMENT_20260927.md)
- [Capture runner](../../../scripts/substrate_live_task_runtime_join_capture_v1.py)
- [Locked analyzer v1](../../../scripts/analyze_substrate_live_task_runtime_join_capture_v1.py)
- [Corrected independent analyzer v1.2](../../../scripts/analyze_substrate_live_task_runtime_join_capture_v1_2.py)
- [Runtime graph join analyzer](../../../scripts/analyze_substrate_live_task_runtime_join_snapshot_v1.py)
- [Current-source lock](../../../evaluation/substrate_capability/live_task_runtime_join_capture_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_live_task_runtime_join_capture_v1_workers_raw_20260927.json)
- [Runtime graph snapshot](../../../evaluation/reports/substrate_live_task_runtime_join_capture_v1_runtime_graph_20260927.json)
- [Capture-integrity and task-gate analysis](../../../evaluation/reports/substrate_live_task_runtime_join_capture_v1_2_analysis_20260927.json)
- [Independent graph join analysis](../../../evaluation/reports/substrate_live_task_runtime_join_snapshot_v1_analysis_20260927.json)

Claim boundary: three current-source repeats of one authored concurrent conversation fixture; selected event-closure counters; one exact pre-action graph; one independently checked multi-edge rule. The legacy reply oracle fails, and no general task prevalence or full request cost claim follows.
