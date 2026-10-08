# Held-topic runtime interface trace v1.1: conservative dependency flags

This is a measurement amendment and fresh capture, not a reinterpretation of the prior raw data. The v1 runner retained explicit per-rule resource lists but omitted the native `reads_any` and `writes_any` booleans returned by `rule_access_sets()`. Those flags are necessary to distinguish a true static/dynamic mismatch from an access covered conservatively by a wildcard declaration.

## Change

Repeat the same seven held-topic turns in three fresh workers under the current source/native/seed lock. For every observed rule, capture all eight `rule_access_sets()` tuple fields: rule slot/name/active status, explicit reads, Term edge reads, explicit writes, `reads_any`, and `writes_any`. Refresh the full static map as rules appear during the task. Keep the v1 runtime event trace and node/attribute interface fields unchanged. The task ownership remains the v1.6 protocol projection. Preserve the known current-source failure on “Can you tell me about copper?” as a task-quality outcome.

## Analysis gates

Require source stability, seven turn traces per worker, zero dropped runtime events, rule UID mapping, exact reconciliation of explicit/wildcard/uncovered access counts, and repeated structural/runtime signatures across three workers. Classify an event as explicitly covered only when the concrete `attr:/edge:/type:` key is in the rule's corresponding set; classify it as conservatively covered only when `reads_any`/`writes_any` is true; otherwise report it as uncovered. Do not call a `reads_any` rule frame-local even when its observed accesses in this run happen to stay inside the declared cut.

This enriches one known authored task family with the static fidelity needed for meaningful trace reconciliation. It does not estimate natural-task prevalence, prove complete host/scheduler coverage, or establish safe partitioned execution.
