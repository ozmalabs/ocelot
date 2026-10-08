# Live task request-cost capture v1 analysis amendment

Date: 2026-09-27 local

The source-locked three-worker capture completed with stable worker-start, worker-finish, and post-run fingerprints. The first analyzer draft incorrectly compared the raw `locked_inputs` value with the entire JSON lock envelope, which contains that value under its `locked_inputs` key. This produced one false integrity failure (`source_native_identity_stable`) despite the raw evidence showing exact equality. The analyzer is corrected to compare against the nested lock payload. Worker data, counters, source lock, protocol, and all task gates are unchanged. The corrected analyzer is run independently against the retained raw data.

A second analysis-only refinement publishes candidate totals by request and match arity, plus the top per-rule contributors. It derives these summaries from the already validated request-boundary `per_rule` snapshots and final RuleIdx pattern tables. No worker is rerun and no capture gates or raw data change.

A final integrity check now verifies each clause-position counter's RuleIdx exists in the request's installed pattern table and the zero-based clause position is within that rule's match arity. This strengthens the preregistered RuleIdx/clause join gate; it uses only retained worker data and does not alter counters or worker runs.

The valid v1 capture shows 41 request-A and 28 request-B clause-position rows per worker beyond the mapped rule's match arity. Source inspection locates a likely mechanism: `CURRENT_RULE` is thread-local in `scale_audit.rs`, while `collect_batch_bindings_parallel` invokes `extend_each` on Rayon workers without rebinding that context. The v1 candidate totals remain valid globally; v1 per-rule/arity values are withdrawn pending the preregistered v1.1 context-propagation replay.
