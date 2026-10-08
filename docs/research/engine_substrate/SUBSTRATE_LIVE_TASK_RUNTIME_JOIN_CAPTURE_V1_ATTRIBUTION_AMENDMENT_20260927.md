# Live task runtime join capture v1 attribution amendment

Date: 2026-09-27 local

A follow-up request-boundary capture found a native audit-attribution defect relevant to interpreting the earlier v1 per-rule work table. `scale_audit.rs` stores the current rule index in thread-local `CURRENT_RULE`; the parallel batch matcher in `rewrite.rs::collect_batch_bindings_parallel` performs matcher candidate tests on Rayon workers without visible propagation of that context. In the follow-up, per-clause totals numerically conserve to the global total, but clause positions exceed the mapped rules' match arities (41 rows for request A and 28 for B per worker). This is direct evidence that the current RuleIdx/clause attribution can be inconsistent on the captured parallel workload.

Accordingly, the earlier v1 arity shares, multi-edge named-rule rankings, and use of per-rule native counts as exact rule attribution are withdrawn as general runtime attribution claims pending a corrected audit path. The independently enumerated graph join remains an exact graph-level calculation; its comparison to the native rule-specific counter is provisional until the native attribution path is validated against a serial-only or context-propagating capture. Global candidate-test totals are unaffected by this caveat.

This amendment does not alter the prior raw workers or source lock. The follow-up request-cost results document contains the anomaly counts, relevant source locations, and next instrumentation step.
