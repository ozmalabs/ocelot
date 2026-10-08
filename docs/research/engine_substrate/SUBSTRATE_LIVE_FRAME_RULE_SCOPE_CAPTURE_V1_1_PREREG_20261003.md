# Live frame rule-scope capture v1.1 preregistration

Date: 2026-10-03  
Status: preregistered before follow-up capture; addresses the v1 pre-request rule-export gap.

## Question

Can each RuleUID observed in the live frame-interface capture be joined to the
native exported rule definition that existed during that request, including
rules minted while processing the request?

## Workload and capture

Run three fresh workers using the identical seed profile and ordered prompts
from v1: `report your organisation`, then `describe who you are`. Preserve
all v1 access/work traces, graph snapshots, lifecycle results, and controls.
For every request, record native rule-store exports immediately before and
after `converse`; retain both snapshots in each worker. A rule UID observed
during a request must be resolved against its post-request export. The pre-
request export is retained to identify additions and revisions. Do not infer
identity from graph node IDs, rule names, or UID sequence alone.

## Gates

1. Three distinct worker processes; stable v1.1 source lock at worker start,
   worker finish, and after the run; valid measuring-engine provenance.
2. Each worker captures exactly the two prompts and before/after exports in
   the expected order. Preserve task lifecycle and shortfall outcomes.
3. Final semantic graph digests reproduce across workers and match the v1
   capture's final semantic graph digest.
4. Every v1 runtime RuleUID for each prompt is present in that prompt's
   post-request native export. Verify exact definition hash stability for
   corresponding UIDs across workers. Retain any unmapped or revised UID.
5. All v1 semantic controls pass. Failures remain in raw output; do not repair
   or exclude after capture.

## Interpretation boundary

This closes RuleUID-to-exported-definition identity only for this two-prompt
fixture and build. Exported match patterns, Term syntax, and effects are
candidate static scopes, not complete semantic dependencies or inference
factor scopes. Terms may read dynamic populations, callbacks, or host state
not captured by the export. A successful identity join does not establish
frame locality, partition correctness, or a speedup.

## Artifacts

- Runner: `scripts/substrate_live_frame_rule_scope_capture_v1_1.py`
- Lock: `evaluation/substrate_capability/live_frame_rule_scope_capture_v1_1_lock_20261003.json`
- Raw capture: `evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_workers_raw_20261003.json.gz`
- Summary: `evaluation/reports/substrate_live_frame_rule_scope_capture_v1_1_20261003.json`
