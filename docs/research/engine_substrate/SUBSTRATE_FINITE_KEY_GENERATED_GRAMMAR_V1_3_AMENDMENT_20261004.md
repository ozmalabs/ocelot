# Finite-key generated grammar v1.3 current-source replay amendment

Date: 2026-10-04

This amendment reruns the v1.2 25-case generated grammar panel against current source because its prior Rust/native source fingerprints are stale. The fixture inventory and acceptance criteria are unchanged: 15 analyzer-admitted programs must load and reach native `fixed_point`, remain within the finite-fact progress bound, and match the independent interpreter's exact node/edge state; 10 unsupported or malformed forms must be refused. The source lock covers runner, analyzer, fragment checker, run-manifest utility, prior protocol, this amendment, native parser/effect/scheduler sources, build manifest, and loaded native extension. The old v1.2 capture remains historical and is not overwritten.

The amendment corrects only provenance and replay date. It adds no rules or cases and does not widen the admitted fragment. Results remain evidence for selected runtime realizations of the finite-key monotone insertion fragment, not exhaustive grammar/runtime equivalence or a wall-time guarantee.
