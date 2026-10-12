# Thoughtexperiment per-rule write attribution v1 preregistration

## Question

Does the opt-in `run_rules_delta_report` trace attribute graph mutation targets to the rule invocation that touched them, with adequate coverage of exact graph changes and explicit handling of no-op attempts? What is the measured overhead on small native closure fixtures?

## Protocol

Run three fresh worker processes against one source-locked native extension. Each worker constructs two deterministic typed-graph fixtures:

1. A single rule that changes a node attribute, creates a node and edge, deletes an edge, and deletes a node with an incident edge.
2. Two overlapping rules that both set the same attribute and create the same edge, so the first can progress and the other can make a no-op attempt.

For each fixture, build three semantically identical fresh substrates and run ordinary `run_rules_report`, instrumented `run_rules_delta_report`, and exact `run_rules_snapshot_delta_report`. Require status/progress/pass parity. The union of attributed event targets must cover every exact changed node and edge. Every event target must occur in the instrumented call's aggregate touched-target report. Event overflow is a failure. In the overlap case, require both rule names to appear and at least one no-progress attempt to be recorded. No rule may be inferred as causal for deferred effects outside its invocation.

Separately collect 15 paired wall-time samples per fixture for ordinary versus attributed settlement on fresh equivalent states, with construction outside the timed interval and deterministic arm order shuffling. Report medians and ratios descriptively; this v1 does not set a performance acceptance threshold.

## Interpretation boundary

Passing establishes bounded target attribution for these direct graph mutation fixtures and quantifies the local diagnostic overhead. It does not establish field-level cause, binding-level cause, deferred-effect ownership, exact causal semantics, target-blind diagnosis, or general engine overhead. This is a prerequisite engine observability gate only.

## Reproducibility

The lock records the benchmark, preregistration, analyzer, native Rust sources, Python extension wrapper, and loaded native binary hashes. Workers recheck the lock before and after each capture. The analyzer independently verifies semantic reconciliation, no-op coverage, worker identity, source stability, and timing records.

For this capture, the extension was built into an isolated package using `maturin build --manifest-path runners/dsl/Cargo.toml --out /tmp/ocelot-rule-attribution-wheel`, then extracted to `/tmp/ocelot-rule-attribution-pkg`. Set `OCELot_NATIVE_IMPORT_ROOT=/tmp/ocelot-rule-attribution-pkg` for `--lock`, `--run`, and the analyzer. The workspace engine was subsequently installed through `PYTHON=python3 scripts/engine_build.sh`; provenance reports no stale sources. To rerun against that installed engine, create a new versioned lock/capture because the loaded binary fingerprint differs from this capture.
