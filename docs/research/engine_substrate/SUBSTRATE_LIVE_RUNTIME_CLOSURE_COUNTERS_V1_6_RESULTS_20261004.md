# Live runtime closure counters v1.6 — results and limits (2026-10-04)

## Outcome

The source-locked six-worker capture (three replicates × audit off/on) passes the independent analyzer: 12 request records, one semantic graph digest, task/reply parity, zero dropped access/work events, and all 4,788 runtime RuleUID observations map to exported definitions. All six audit-off requests have zero counters and empty attribution tables. The audit-on requests have zero unattributed candidate tests, no ambiguous rule metadata, valid store identities, and conserved candidate, clause, and semantic-edge totals. No nested audit mode transition occurred during any request.

The v1.5 panel's 145 first-prompt and 134 second-prompt unattributed Term evaluations are now exactly classified. Every one enters through direct host calls to the public PyO3 `Substrate.evaluate` API: first prompt 145 host API evaluations and 805,270 rule-attributed evaluations, total 805,415; second prompt 134 host API evaluations and 374,088 rule-attributed evaluations, total 374,222. The no-current-rule-outside-host and ambiguous-rule categories are zero in every replicate. The per-rule plus host API counts equal the global Term totals exactly.

## Interpretation and limits

This closes the measurement attribution gap for the selected authored two-request route. The unmatched terms were not matcher work that lost a rule identity; they were direct host evaluation work, which has no single rule owner by design and is now accounted for as a separate operation class. The v1.4 audit-off failure was a nested-instrumentation artifact; v1.5 and v1.6 both pass the corrected whole-request isolation gate.

These are exact integer counts under opt-in instrumentation for three replicates of one authored route. They do not estimate natural task frequency, uninstrumented latency, cheap-cut prevalence, asymptotic complexity, or general capability. Natural workload coverage, learning genuinely new structure, prospective thoughtexperiment discovery, and large-scale memory/CPU behavior remain open programme items.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_6_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_6.py)
- [Source lock](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json)
- [Six-worker capture](../../../evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz)
- [Independent analysis](../../../evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json)
