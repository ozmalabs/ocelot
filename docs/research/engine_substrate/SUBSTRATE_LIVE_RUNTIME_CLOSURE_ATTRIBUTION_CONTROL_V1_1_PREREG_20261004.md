# Live runtime closure attribution control v1.1 preregistration

Date: 2026-10-04
Status: preregistered before the confirmatory control run

## Amendment from v1

The v1 smoke run found that metadata registration was gated by per-rule mode but not by global audit mode. With global audit disabled and per-rule mode left enabled, a rule attempt could repopulate metadata and identity snapshots even while numeric counters remained zero. v1.1 adds the requirement that metadata registration return immediately unless both global audit and per-rule mode are enabled. The failed v1 output is retained unchanged.

## Question and control

Does store-qualified identity survive two independent `_native.Substrate` instances using local rule index 0, while per-rule and per-clause candidate counts conserve and all opt-in tables remain empty when global auditing is disabled?

Run one fresh Python process against the source-matched native extension. Create two substrates; add two `Node` vertices and one unchecked `link` edge to each; install the same one-edge `shared_rule` at local index 0; and call `apply_rule_once(0)` on both. Capture global counters, per-rule rows, clause rows, metadata, and identity rows. Disable global audit, reset the tables, and apply the first rule once again.

`add_edge_unchecked` keeps the control independent of Grammar vocabulary setup. It still exercises the production graph matcher and substrate dispatch; this does not evaluate Gamma admissibility.

## Gates

1. Start and finish fingerprints for the preregistration, runner, Rust audit/substrate/rewrite/PyO3 sources, Cargo lock, and native extension match the saved lock.
2. Both installed rules occupy local index 0 and both applications find a match.
3. The audit-on identity snapshot contains two distinct audit IDs and store tokens, both paired with local index 0.
4. Metadata contains two valid, non-ambiguous `shared_rule` rows with arity 1.
5. Per-rule candidate and clause rows have one positive row per audit ID.
6. Unattributed candidates equal zero; per-rule totals, clause totals, and global candidate tests conserve exactly.
7. With global audit disabled, a matching application leaves global counters and all opt-in per-rule, clause, metadata, and identity snapshots empty.

## Interpretation boundary

Passing validates the store-to-matcher path and the PyO3 identity snapshot for this authored one-edge control. It does not establish live workload attribution, production rule coverage, instrumentation overhead, or general tractability. Passing is a prerequisite for a new paired live capture with identity snapshots and request-isolated audit modes.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_closure_attribution_control_v1_1.py`
- Lock: `evaluation/substrate_capability/live_runtime_closure_attribution_control_v1_1_lock_20261004.json`
- Result: `evaluation/reports/live_runtime_closure_attribution_control_v1_1_20261004.json`

## v1.1 result

All six gates pass against the source-matched extension. Both local rule-0 applications matched; identity rows were `(0, 1, 0)` and `(1, 2, 0)`; metadata was non-ambiguous; candidate tests and clauses separated one per ID; total candidate tests were 2 with zero unattributed; and all audit-off counters and opt-in tables were empty. Engine ID: `2934cb1c37e7`. Result SHA-256: `7c39669fee2e2ccb1a1218ce7ade5d29e838072e25c1cd5dbc5e061e2eb7db82`.
