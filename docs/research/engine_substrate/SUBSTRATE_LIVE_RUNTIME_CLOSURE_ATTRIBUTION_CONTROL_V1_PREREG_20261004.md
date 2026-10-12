# Live runtime closure attribution control v1 preregistration

Date: 2026-10-04
Status: preregistered before the confirmatory control run

## Question

Does store-qualified audit identity survive the complete Rust `Substrate` to PyO3 API path when two independent stores reuse local rule index 0, while preserving per-rule and per-clause candidate-count conservation and audit-off isolation?

## Control

Run one fresh Python process against the source-matched native extension. Construct two `_native.Substrate` instances. In each, add two `Node` vertices, add an unchecked `link` edge, install the same one-edge rule named `shared_rule` at local index 0, then call `apply_rule_once(0)`. Read global counters, per-rule rows, clause rows, metadata, and the identity snapshot. After recording the audit-on state, turn the global audit off, reset counters, execute the matching rule once more, and confirm the opt-in tables remain empty and global counters remain zero.

`add_edge_unchecked` is used solely to keep the control independent of Grammar vocabulary setup; it exercises the production graph matcher and substrate dispatch while omitting a capability claim about Gamma admissibility.

## Preregistered gates

1. The worker starts and finishes with the exact preregistration, runner, Rust source, Cargo lock, and native extension fingerprints in the saved lock.
2. Both rule installations return local index 0 and both rule applications find a match.
3. The identity snapshot contains two distinct audit IDs and two distinct store tokens, each paired with local index 0.
4. Metadata contains two non-ambiguous `shared_rule` records with match arity 1.
5. Per-rule candidate-test rows and clause rows each have one row per audit ID; both rows are positive and separate.
6. Global `cand_tested_unattributed` is zero; the sum of clause candidate tests equals global `cand_tested` and the sum of per-rule candidate tests.
7. With global audit disabled, a matching application leaves every global counter zero and the per-rule, clause, metadata, and identity tables empty.

## Interpretation boundary

Passing establishes the native binding and per-rule attribution control for this authored one-edge pattern. It does not establish live workload attribution, production rule coverage, performance overhead, or general tractability. The next gate is a new paired live workload capture using identity snapshots, with audit-on/off request isolation and a corrected aggregate payload validation.

## Artifacts

- Runner: `evaluation/substrate_capability/live_runtime_closure_attribution_control_v1.py`
- Lock: `evaluation/substrate_capability/live_runtime_closure_attribution_control_v1_lock_20261004.json`
- Result: `evaluation/reports/live_runtime_closure_attribution_control_v1_20261004.json`
