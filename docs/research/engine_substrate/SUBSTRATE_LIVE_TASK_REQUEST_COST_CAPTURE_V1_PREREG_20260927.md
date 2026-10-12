# Live task request-cost capture v1 preregistration

Date: 2026-09-27 local
Status: protocol locked before implementation and capture

## Question

How much native matcher candidate work occurs over each complete serialized `converse` lock interval in the current `describe_scene` two-request fixture, and how is that work distributed over active installed rules and match clauses?

The prior live capture reports only six `_record_live_goal_event` closure intervals per worker. Its wrapper resets and disables `scale_audit` at every producer event, so those event rows cannot be summed into a complete request total. This capture moves counter reset/enable/snapshot to the outermost conversation-lock boundary and removes per-event counter resets. Event-time rule-table snapshots remain available for mapping RuleIdx values that are appended during the task.

## Frozen task and schedule

Use the exact existing `describe_scene` task fixture, two identical `describe what you see` requests, the same speaker and scene, the same forced serialization schedule, and the existing goal identity/lifecycle and final semantic graph gates. Do not change seeds, request text, graph data, concurrency ordering, or native matcher code. Run three fresh worker processes. Request A is expected to retain the already observed gap response; request B's expected response remains the existing baseline. Report both outcomes without conditioning work inclusion on reply success.

## Instrumentation boundary

At outermost acquisition of the conversation lock, reset global scale and per-rule audit counters, enable both audit modes, then enter the measured lock interval. At outermost release, disable audit modes and snapshot global counters, per-rule metrics, and per-rule match-clause counters before leaving the lock. Requests are serialized by the lock, so only one request owns the process-global counters at a time. Do not reset counters inside `_record_live_goal_event`; preserve event-level timing if convenient, but request totals are primary.

The measured interval is the lock-protected request body. It excludes Python work before lock acquisition and after lock release, boot, and the lock wait preceding acquisition. Report call wall/CPU separately and state this boundary. Audit-enabled timing is instrumentation-contaminated; no uninstrumented latency or throughput claim is allowed.

## Required counters and joins

Capture global native candidate tests, candidate pairs, term evaluations, where evaluations, and other `scale_audit` fields exposed by the snapshot. Capture per-rule metrics and clause-position candidate tests. Snapshot installed rule patterns at boot and at each producer event (or another exact mutation boundary) so every observed RuleIdx is mapped to the correct rule identity and match arity. Preserve a raw event-time pattern history and a raw request-boundary counter snapshot.

## Gates

1. Three fresh PIDs and stable source/native fingerprints before and after each worker.
2. Both requests acquire and release the observed lock; A precedes B; threads join without errors.
3. Existing task schedule, distinct goal identity, lifecycle, pause and final normalized graph gates reproduce.
4. Reply outputs reproduce across workers; report the legacy A semantic gate as failed if it remains failed.
5. Every per-rule and per-clause metric maps to an installed event-time pattern; unknown RuleIdx is a hard failure.
6. Per-rule candidate tests sum exactly to request-boundary global candidate tests. Clause-position candidate counts must reconcile to candidate tests under the native counter semantics; if they do not, report the discrepancy and fail this gate rather than infer equality.
7. Record counters before each lock reset for scope accounting; reset/enable at acquisition, snapshot/disable at release, and prove no candidate-work leakage after reset by requiring `cand_tested == 0` and empty per-rule/per-clause tables in the post-reset snapshot. Non-work audit fields such as FFI calls may change when taking snapshots and are not required to remain zero.
8. Candidate work summaries distinguish one-, two-, and >=3-clause rules, and request A/B totals. Report all worker values and medians/ranges.

## Analysis and claim boundary

Primary result: exact request-lock-scoped matcher work, attributed by rule arity and request, for this one authored task fixture on the current source. Secondary: audit-instrumented lock interval wall/CPU and full-call wall/CPU, clearly separated. This does not establish natural task prevalence, general frame locality, uninstrumented latency, commodity-scale throughput, or successful request-A capability. The capture must retain the A reply failure as a separate quality result.

## Artifacts

Implementation, source/native lock, raw workers, independent analyzer, and results document will be added before execution. Any harness or analyzer defect discovered after capture must be documented as an amendment; do not silently amend the locked protocol.
