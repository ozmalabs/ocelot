# Full built-sheet scope fidelity preregistration

Date: 2026-09-25. Benchmark-only cloned seed manifest; do not alter production seed or engine source.

## Question and claim boundary
Does replacing the global SUnit competition fold with a fold over the matched sheet root's `has_sunit` members preserve the authored dynamics when a substrate contains one complete `settle_lib.build_sheet` sheet? This tests full built anatomy and exact settling-rule semantics. It does not test visual task quality, orientation selectivity, learning, multiple full sheets in one graph, or asymptotic runtime.

## Paired design
For each case, build two independent sheets with the same `seed`, `n_side`, `channels="degenerate"`, and connectivity 8, once with the authored `vision_settle` manifest and once with a deep-copied manifest whose `st_settle` mean numerator and denominator source is `Neighbours(r, has_sunit)`. No other manifest element changes. Cases are `(n_side, seed)` = `(3,11)`, `(3,29)`, `(4,11)`, `(4,29)`. Assert each built substrate has exactly one Retina root, all listed units are its `has_sunit` children, and export locates exactly one `st_settle` and one `st_commit`.

Initialize `aff` and `act` identically in each pair from NumPy PCG64(seed + 9000): aff is uniform [0,1), act is zero; set each `aff_step` to the root's current step. Hold other graph state fixed. Execute only `st_settle` then `st_commit`, in synchronous sweeps, until neither rule progresses or 10,000 sweeps. Record progress per rule, terminal activations, sweep count, exact paired equality, maximum residual, root membership, and source/native provenance.

## Predictions and criteria
In the one-root case, global and root-scoped SUnit sets are identical. Both must terminate below the cap, produce identical terminal activation arrays and sweep counts, and agree with an independent NumPy implementation of `act_next=max(aff + mean(local-neighbor act) - mean(sheet act),0)`. The terminal state must have zero exact residual under one additional compute-and-commit sweep. Any mismatch fails the fidelity gate. No speed claim is made because the number of activated bindings is the same and wall timing is not the primary endpoint.

## Reporting
Preserve raw case-level values, seed/manifest/runner/protocol/native hashes, rule names and root membership checks. A successful result justifies proceeding to full sensory/orientation workload comparison; it does not justify changing the authored seed.
