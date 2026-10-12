# Live runtime pre-request state capture v1 — preregistration (2026-10-04)

## Question

Can the selected v1.6 full-seed route's primary native graph and rule store be captured at each request boundary, with exact task-output parity to the parent capture? This is prerequisite evidence for replay, not a claim that the primary store contains every store represented in global counters.

## Fixed sample and procedure

Run replicate 0 of the existing two-prompt worker once with native per-rule audit enabled. At each `WorldAdapter.converse` boundary, export the primary graph and full rule store immediately before and after the request, and snapshot global/per-rule matcher counters and store-qualified identities. Preserve both requests in order. Also capture the task result and final semantic digest. Store the four request-boundary states as separate gzip checkpoints so the analyzer can verify one at a time; keep only compact route metadata in the manifest. No secondary store is inferred from the primary export.

Compare the task projection, replies, and final graph semantic digest against replicate 0/audit-on in the locked v1.6 capture. Require each request's `after` graph/rules to equal the next request's `before` graph/rules exactly; require graph node/edge IDs and rule UIDs to be unique within each snapshot; verify source hashes before and after. Report snapshot sizes and store-identity coverage. A failure remains in the raw capture and fails the independent analysis.

## Claim boundary

This is one replicate on one authored two-request route. The repeated primary graph and rule snapshots make that store replayable at request boundaries. Global audit identities include other native stores whose bodies this API does not expose; therefore this capture alone cannot reproduce all measured global work or establish whole-route replay parity. It does not estimate natural-workload prevalence, prove termination, or establish general tractability.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_pre_request_state_v1.py`
- Independent analyzer: `evaluation/substrate_capability/analyze_live_runtime_pre_request_state_v1.py`
- Lock: `evaluation/substrate_capability/live_runtime_pre_request_state_v1_lock_20261004.json`
- Capture manifest: `evaluation/reports/live_runtime_pre_request_state_v1_20261004.json`
- Compressed primary graph/rule checkpoints: `evaluation/reports/live_runtime_pre_request_state_v1_checkpoints/`
- Analysis: `evaluation/reports/live_runtime_pre_request_state_v1_analysis_20261004.json`
