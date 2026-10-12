# Live runtime closure counter v1.3 diagnostic

Date: 2026-10-04

## What the capture establishes

Six fresh workers completed with return code zero and stable source fingerprints. Their two-request task contracts match across audit modes, and all six reproduce one semantic graph digest. Across the twelve requests, all 4,788 observed runtime RuleUID references resolve to definitions exported after the corresponding request. This validates the runtime extraction and task/graph parity path.

The native counter gates do **not** pass. Each nominal audit-off worker records 8,099 candidate tests on its first request, though the second request is zero in that mode. In audit-on mode, `report your organisation` reports 8,099 tests consistently, while `describe who you are` reports 36,072 tests and 36,082 candidate expansions. The latter has 51 unattributed candidate tests and nine ambiguous native rule IDs in each worker; per-rule totals do not conserve with global totals. Therefore the audit-off isolation control and per-rule attribution are invalid for this live runtime panel. The observed global audit-on totals are retained as diagnostic values, not confirmatory cost estimates.

The runner's aggregate `all_checks_pass` field is false because its final gate expected each worker payload under a nested `capture` key, while the worker returned the capture fields at the top level. The independent reconciliation analyzer reads those completed records, confirms the six successful workers and source lock, and retains the genuine counter-gate failures above. The compressed raw archive is unchanged.

## Instrumentation gap identified

Current per-rule tables and metadata are keyed by a process-global `u32` rule index, and the thread-local `CURRENT_RULE` carries only that index. The source documents that callers must namespace indices when multiple stores share the process-global counters, but runtime rule stores reuse local indices. Ambiguous metadata then invalidates attribution; matcher paths without a valid context either disappear from per-rule totals or are marked unattributed. This accords with the earlier [live task request-cost audit](SUBSTRATE_LIVE_TASK_REQUEST_COST_CAPTURE_V1_RESULTS_20260927.md), which found out-of-arity per-clause rows in a separate production-route capture.

The next measurement gate depends on fixing and verifying audit identity across rule stores and Rayon execution, and isolating audit-off requests so no earlier request or runtime path can leave the global audit enabled. Re-run a small serial/parallel attribution control first; repeat the live panel only after the controls pass. No per-rule hot-rule or natural workload tractability claim follows from this diagnostic.

## Audit identity repair

The Rust audit path now allocates each rule-owning store a process-unique token and maps `(store token, local rule index)` to a unique process-local audit ID. `Substrate` retains its token; forks receive fresh tokens. The plain rewrite runner allocates a token for its invocation, while the scoped runner receives the owning substrate's token. Metadata and per-rule, clause, and edge counters continue using the compact audit ID, so their existing row shapes remain usable. A new identity snapshot API maps audit IDs back to `(store token, local rule index)` for source-level attribution. The token is allocated at owner creation and does not depend on pointers, names, or pattern hashes.

The namespace is propagated through `Substrate::apply_rule_once`, `Substrate::apply_rule_batch`, `Substrate::attempt_one_rule` (the core fixpoint path), both scoped runner entry points, and `rewrite::run_rules_opts_with_audit_ids`. `CURRENT_RULE` and Rayon `with_rule_index` rebinding carry the generated audit ID. Missing context remains explicitly unattributed; it is not silently dropped. Metadata ambiguity is now assessed per generated identity, rather than on colliding local indices. The new PyO3 identity snapshot exposes source identities to capture runners.

Implementation references: [audit identity allocation and snapshots](../../../runners/dsl/src/scale_audit.rs), [substrate owner token and dispatch paths](../../../runners/dsl/src/substrate.rs), [rewrite and Rayon propagation](../../../runners/dsl/src/rewrite.rs), and [PyO3 snapshot export](../../../runners/dsl/src/py.rs).

`cargo check --lib` passes. Three focused Rust checks now pass:

- `scale_audit::tests::namespaced_rule_identity_separates_overlapping_indices_across_threads` exercises the source identity map and worker-thread rebinding, and checks that audit-off leaves opt-in tables empty.
- `rewrite::tests::per_rule_audit_separates_same_local_rule_across_serial_and_rayon_matchers` uses same-name, same-shape rules at the same local index under two store tokens. It exercises serial enumeration and the production Rayon batch matcher, then verifies distinct audit IDs, metadata arity, per-rule/clause separation, and exact candidate-count conservation.
- `substrate::tests::independent_substrates_keep_overlapping_rule_indices_distinct_in_audit` constructs two real `Substrate` instances, installs a matching rule at local index 0 in each, runs `apply_rule_once`, and checks distinct owner tokens, exported audit identity rows, metadata, clause separation, and exact conservation.

These checks prove the Rust owner-to-matcher path, including the real serial/Rayon matcher. The sanctioned `scripts/engine_build.sh` first produced engine `8789f3257fdc`; an inline Python 3.13 smoke control showed two distinct audit IDs and stores `(0, 1, 0)` and `(1, 2, 0)`, identical non-ambiguous metadata, two attributed candidate tests, and exact clause conservation.

The first formal Python binding control [v1 result](../../../evaluation/reports/live_runtime_closure_attribution_control_v1_20261004.json) failed one gate: after disabling global audit while leaving per-rule mode enabled, a match left metadata and identity rows behind even though counters were zero. This exposed a registration-gate defect. The source now requires both global audit and per-rule mode before registering audit metadata. The preregistered [v1.1 control](SUBSTRATE_LIVE_RUNTIME_CLOSURE_ATTRIBUTION_CONTROL_V1_1_PREREG_20261004.md) repeats the binding capture with that isolation gate included; its result will decide whether the live workload panel can be resumed. The v1.3 capture and runner remain unchanged as historical evidence.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_3_PREREG_20261004.md)
- [Runner](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_3.py)
- [Worker source lock](../../../evaluation/substrate_capability/live_runtime_closure_counters_v1_3_lock_20261004.json)
- [Compressed six-worker capture](../../../evaluation/reports/live_runtime_closure_counters_v1_3_20261004.json.gz), SHA-256 `55b95f5bdf19312f30d72e96af370ec17a85a6dc344f0c9a483e6395a14e2d7e`
- [Reconciled diagnostic analysis](../../../evaluation/reports/live_runtime_closure_counters_v1_3_reconciled_analysis_20261004.json)
- [Reconciliation analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_closure_counters_v1_3_reconciled.py)

Claim boundary: six fresh workers over one authored two-request production route. The graph and task parity and RuleUID-resolution checks pass; audit-off isolation and native per-rule attribution fail. This is a measurement-instrument diagnostic, not a successful natural-workload cost result.
