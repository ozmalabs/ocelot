# Live runtime closure counters v1.4 preregistration

Date: 2026-10-04
Status: preregistered before capture

## Question

After the store-qualified audit identity repair and the v1.1 PyO3 control pass, can runtime candidate and Term work be attributed to native rule stores on the selected two-request conversation route, with audit-off isolation and exact counter conservation?

## Design

Run three fresh worker processes in each mode (audit off and audit on), for six workers total. Each worker replays the same authored two-request route and records per-request global counters, per-rule counters, clauses, semantic pattern-edge counts, metadata, and `(audit_id, store_instance_id, local_rule_index)` identities. Preserve task results, semantic graph digest, runtime RuleUID references and their exported definitions, request trace completeness, and source/native fingerprints. Audit counters are reset and the requested mode is set before every request.

The workload, prompts, base route, and three-by-two design match live runtime closure counters v1.3. This is a new source/native capture, not a reinterpretation of v1.3. The runner fixes the v1.3 aggregate payload-shape check; independent analysis reads the same top-level worker records and verifies their contents directly.

## Gates

1. Six workers complete in a crossed three-replicate by two-mode design, each with matching start/finish source inputs and zero return code.
2. Each worker returns exactly two requests in the locked prompt order. Task projections, replies, and semantic graph digests match across paired modes and all workers; all runtime RuleUIDs resolve to exported rule definitions; access/work trace drops are zero.
3. Every audit-off request has zero global counters and empty per-rule, clause, metadata, identity, and edge-candidate tables.
4. Every audit-on request has no ambiguous metadata, no missing identity mapping for an emitted audit ID, valid clause positions, and zero unattributed candidate or Term work.
5. Per-rule candidate-pair counts sum to global `cand_enum`; per-rule candidate-test counts and clause totals sum to global `cand_tested`; semantic edge candidate totals sum to per-rule candidate pairs; candidate path and first/repeat totals conserve globally.
6. Every per-rule, clause, and edge ID maps to exactly one exported `(store, local index)` identity and one valid metadata row.
7. The parent runner's `all_checks_pass` is derived from the actual top-level worker schema (`task_result`, `requests`, and `native_counter_observations`), not a nested `capture` field.

## Interpretation boundary

Passing validates attribution for this selected authored route. It does not establish the prevalence of cheap-cut locality, polynomial scaling, uninstrumented latency, or general capability. Any counter-control failure keeps the capture diagnostic and blocks natural workload cost claims.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_closure_counters_v1_4.py`
- Analyzer: `evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_4.py`
- Lock: `evaluation/substrate_capability/live_runtime_closure_counters_v1_4_lock_20261004.json`
- Raw: `evaluation/reports/live_runtime_closure_counters_v1_4_20261004.json.gz`
- Analysis: `evaluation/reports/live_runtime_closure_counters_v1_4_analysis_20261004.json`
