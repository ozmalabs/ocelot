# Live runtime closure counters v1.6 preregistration

Date: 2026-10-04
Status: preregistered before capture

## Question

After fixing nested audit interference, can the remaining unassigned Term work be classified as direct host-requested evaluation versus missing/ambiguous matcher context, while retaining audit-off isolation and matcher counter conservation?

## Design

Run three fresh worker processes in each mode (audit off and audit on), for six workers total. Each worker replays the same authored two-request route and records per-request global counters, per-rule counters, clauses, semantic pattern-edge counts, metadata, and `(audit_id, store_instance_id, local_rule_index)` identities. Preserve task results, semantic graph digest, runtime RuleUID references and their exported definitions, request trace completeness, and source/native fingerprints. Audit counters are reset and the requested mode is set before every request.

The workload, prompts, base route, and three-by-two design match live runtime closure counters v1.5. This is a new source/native capture. The worker keeps `OZMA_DELEGATE_EVENT_AUDIT_TO_OUTER=1`, preserving producer-event rows while avoiding nested audit resets. A new native scope counter marks Term evaluations entered through the public PyO3 `Substrate.evaluate` API. When per-rule auditing is active, each unattributed Term evaluation is counted in exactly one of: direct host API, no current rule outside that API, or ambiguous rule identity. The independent analyzer checks the partition, preserves separate direct-host totals, and rejects unexplained matcher-context loss.

## Gates

1. Six workers complete in a crossed three-replicate by two-mode design, each with matching start/finish source inputs and zero return code.
2. Each worker returns exactly two requests in the locked prompt order. Task projections, replies, and semantic graph digests match across paired modes and all workers; all runtime RuleUIDs resolve to exported rule definitions; access/work trace drops are zero.
3. Every audit-off request has zero global counters and empty per-rule, clause, metadata, identity, and edge-candidate tables.
4. Each delegated producer-event record resolves to its created event, and no nested audit enable, disable, or reset occurs during a request.
5. Every audit-on request has no ambiguous metadata, no missing identity mapping for an emitted audit ID, valid clause positions, and zero unattributed candidate tests.
6. Per-rule candidate-pair counts sum to global `cand_enum`; per-rule candidate-test counts and clause totals sum to global `cand_tested`; semantic edge candidate totals sum to per-rule candidate pairs; candidate path and first/repeat totals conserve globally.
7. Every per-rule, clause, and edge ID maps to exactly one exported `(store, local index)` identity and one valid metadata row.
8. The parent runner's `all_checks_pass` is derived from the actual top-level worker schema (`task_result`, `requests`, and `native_counter_observations`), not a nested `capture` field.
9. For every audit-on request, `term_evals_unattributed` equals the sum of `term_evals_unattributed_host_api`, `term_evals_unattributed_no_rule`, and `term_evals_unattributed_ambiguous`; no-rule and ambiguous counts must both be zero for the matcher-cost attribution gate to pass.

## Interpretation boundary

Passing validates matcher attribution and separately classifies direct host evaluation on this selected authored route. Direct host terms remain outside per-rule totals and must be reported as their own operation class. It does not establish cheap-cut prevalence, polynomial scaling, uninstrumented latency, or general capability. Any unclassified count keeps the capture diagnostic and blocks natural-workload cost claims.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py`
- Analyzer: `evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_6.py`
- Lock: `evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json`
- Raw: `evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz`
- Analysis: `evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json`
