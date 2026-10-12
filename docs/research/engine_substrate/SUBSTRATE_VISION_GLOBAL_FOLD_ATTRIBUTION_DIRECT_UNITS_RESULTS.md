# Vision global-fold direct interior-work counter results

**Run:** 2026-09-25. Follow-up to the invocation-based attribution report, using a newly rebuilt native engine with opt-in `NodesOfType` cardinality accounting.

## Result

The `NodesOfType` evaluator now charges the size of its returned node vector to the existing `term_units` counter when scale auditing is enabled. The counter is disabled by default. The canonical engine build completed and recorded the current source fingerprint. No rule or authored seed changed.

Eight audited arms (global/scoped at N=4/16/64/256; seed 4101) exactly match the previous uninstrumented run in progress count and terminal activation. Global minus scoped `term_unit:NodesOfType` counts are 16,384, 262,144, 4,194,304, and 67,108,864. These match exactly the independent derivation from the earlier rule-level invocation-count difference multiplied by N. Global, per-rule, and per-variant term-unit counters conserve at every size, as do candidate-test and term-evaluation counts.

The direct counter confirms that the authored global fold incurs repeated full-population traversal/materialization at each matched unit. At N=256, it adds 67.1 million node-value work units under the 1,024-progress cap. This operation count is now directly observed by native instrumentation rather than inferred only from the result set cardinality. It does not claim each unit has identical CPU cost or equate work units to machine instructions.

## Boundaries

This is one rule family, one seed, a synthetic single-sheet setup, and a fixed progress cap; most runs reach the cap. It establishes neither natural-workload prevalence nor the cost of converged execution. The earlier wall-time comparison still showed only about a 5.9% global/scoped difference at N=256, so candidate/Term counts do not account for all elapsed time. Multi-sheet behavior, repeated timing under controlled load, and natural dependency snapshots remain open.

## Evidence

- [v1.1 amendment](SUBSTRATE_VISION_GLOBAL_FOLD_ATTRIBUTION_V1_1_AMENDMENT_20260925.md)
- [instrumentation change](../../../runners/dsl/src/term.rs)
- [runner](../../../scripts/substrate_vision_global_fold_attribution_direct_units.py)
- [independent analyzer](../../../scripts/analyze_substrate_vision_global_fold_attribution_direct_units.py)
- [raw report](../../../evaluation/reports/substrate_vision_global_fold_attribution_direct_units_20260925.json)
- [analysis](../../../evaluation/reports/substrate_vision_global_fold_attribution_direct_units_analysis_20260925.json)
- [lock](../../../evaluation/substrate_capability/vision_global_fold_attribution_direct_units_lock_20260925.json)
- [engine build record](../../../runners/dsl/python/substrate_rs/_native.build.json)
