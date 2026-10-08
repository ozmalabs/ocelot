# Parallel matcher rule-audit context v1.1 implementation amendment

Date: 2026-09-27 local

Source inspection confirmed that `scale_audit::CURRENT_RULE` is thread-local and that the batch matcher evaluates partition roots on Rayon workers. The v1.1 intervention captures the active rule index at the parallel-dispatch boundary and uses an unwind-safe scoped rebinding around each worker partition. No match ordering, candidate generation, graph effects, scheduling, or default-disabled audit behavior is changed.

The release engine was rebuilt with `scripts/engine_build.sh`; the resulting engine provenance identifier is recorded in the source/native lock. This amendment records implementation scope only. The confirmatory capture and all interpretation gates are defined by [the preregistration](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_1_PREREG_20260927.md).

The first post-capture analyzer execution failed before producing an analysis because its arity accumulator indexed the request-level map incorrectly. The analyzer was corrected to accumulate into the request's `Counter`. Worker raw data and source/native lock are unchanged; the corrected independent analysis is rerun against the same capture.

The v1.1 source lock records `substrate/world_adapter.py` at SHA-256 `0b965df54782da885657ce3ef75389ba4e9f2f970e01f7406e6bb53c50ce6a69`; the valid v1 comparison capture locked that file at `2e8061253e6ee9930f69a45c108e307a99e93087a6fbfe2d047440d6302f4856`. The worktree source changed between captures, so exact cross-version graph parity is not a valid gate. The v1.1 workers do reproduce one another's graph digest and replies. The analyzer's baseline-comparison gate is amended to report this non-comparability rather than a regression.

The explicit Rayon context propagation did not reduce the out-of-arity clause rows. Source review found additional unresolved attribution hazards: `graph_rules::run_graph_rules_opts` calls the generic matcher with local vector indices that overlap the seed-installed `RuleIdx` namespace, and the generic batch branch in `rewrite::run_rules_opts` continues without `end_rule_enumeration`. The next correction must give graph-resident and substrate-installed rules distinct stable audit identities, clear context at every rule-attempt boundary, and explicitly count matcher work without a rule identity as unattributed. The v1.1 raw attribution remains failed and must not be used for names/arity.
