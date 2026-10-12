# Parallel matcher rule-audit context v1.1 results

Date: 2026-09-27 local

## Capture outcome

Three fresh current-source workers completed under a stable source/native lock. Global candidate totals reproduce exactly: request A **677,795** and request B **842,748** per worker, unchanged from the valid v1 capture. The 36 capture-integrity checks pass, including per-rule/per-clause aggregate conservation, reset boundaries, schedule/lifecycle, and within-v1.1 graph/reply reproduction.

The rule-attribution gate **fails**. There are still 41 clause-position rows per A request and 28 per B request whose positions exceed the match arity attributed by the current pattern join (123 and 84 rows across three repeats). The explicit Rayon worker context rebinding therefore did not resolve the observed attribution anomaly. Rule-name and match-arity totals remain diagnostic only and are not interpretable.

Request A still returns the exact-reply gap response; B returns the registered baseline. The task quality gate remains failed for A. The v1-to-v1.1 graph comparison was made non-comparable after discovering `world_adapter.py` changed between their locks. V1.1's final graph and reply pair reproduce across its own three workers.

## Updated diagnosis

Source review shows the native per-rule table is keyed by a bare `u32`. Seed-installed rules use stable `RuleIdx` values from `Substrate::attempt_one_rule`; graph-resident rules run through `graph_rules::run_graph_rules_opts` and the generic `rewrite::run_rules_opts`, which assigns indices local to its temporary rule vector. These namespaces overlap, so joining every row to `export_rules()` can map graph-rule work to an unrelated seed rule. In addition, the generic batch branch continues without `end_rule_enumeration`, which can leave thread-local context set beyond the rule attempt. The failed v1.1 replay shows Rayon context rebinding alone is insufficient; both identity namespace and context lifetime need explicit treatment.

The next correction should encode distinct stable audit identities for graph-resident and substrate-installed rules, record or reconstruct the matching pattern under that same identity, clear audit context on every return/continue path, and count matcher work with no active identity as unattributed. Then rerun the same three-worker task capture and require exact totals, per-rule/per-clause conservation, and zero out-of-arity rows before using named-rule hot spots.

## Claim boundary

The valid v1.1 result is exact global candidate work in the two outer conversation-lock intervals for one authored task fixture. It does not validate per-rule names, arity shares, natural task prevalence, cheap-cut locality, asymptotic scaling, or uninstrumented performance. Request A's reply capability gate fails.

## Artifacts

- [Preregistration](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_1_PREREG_20260927.md)
- [Implementation/source amendment](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_1_AMENDMENT_20260927.md)
- [Driver](../../../scripts/substrate_parallel_rule_audit_context_v1_1.py)
- [Worker](../../../scripts/substrate_parallel_rule_audit_context_v1_1_worker.py)
- [Analyzer](../../../scripts/analyze_substrate_parallel_rule_audit_context_v1_1.py)
- [Source/native lock](../../../evaluation/substrate_capability/parallel_rule_audit_context_v1_1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_1_workers_raw_20260927.json)
- [Analysis](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_1_analysis_20260927.json)
- [Capture manifest](../../../evaluation/reports/substrate_parallel_rule_audit_context_v1_1_20260927.json)
