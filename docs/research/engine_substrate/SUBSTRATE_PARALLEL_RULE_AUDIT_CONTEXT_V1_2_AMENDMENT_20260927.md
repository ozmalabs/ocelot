# Parallel matcher rule-audit context v1.2 implementation amendment

Date: 2026-09-27 local

This intervention corrects four independently identified audit hazards: Rayon workers require explicit thread-local rule rebinding; graph-resident Rule nodes and substrate RuleIdx values require separate identity namespaces; stale identity or clause metadata must not receive attributed candidate work; and every rule-attempt exit must clear the audit context. Native metadata records audit ID, symbol, display name, and match arity. The candidate-test site verifies symbol and arity and increments `cand_tested_unattributed` when the identity is missing or inconsistent. The capture gate requires exact conservation of the global matcher count.

The source change is audit-only and leaves matcher enumeration and effects unchanged. The confirmatory capture is gated by [the preregistration](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_2_PREREG_20260927.md).

The first attempted v1.2 three-worker run is invalid and excluded: the source-closure hash for `substrate/world_adapter.py` changed during the third worker. Inspection shows the worktree acquired adapter-wide and native-call serialization plus allocator-trim behavior while the capture was in progress; this is source code, not an output artifact. The raw attempt is preserved as `substrate_parallel_rule_audit_context_v1_2_workers_raw_20260927.json` and its aggregate driver record as `substrate_parallel_rule_audit_context_v1_2_20260927.json`. After the source settled, the lock was refreshed from the current tree; only a subsequent capture with all start, finish, and post-run inputs equal to that lock is eligible for analysis.
