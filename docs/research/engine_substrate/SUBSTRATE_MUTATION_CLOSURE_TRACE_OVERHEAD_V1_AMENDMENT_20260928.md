# Mutation-to-fixpoint trace overhead v1 amendment

Date: 2026-09-28  
Applies to: `SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_PREREG_20260928.md`

## Correction before confirmatory rerun

The first capture completed all workers with stable source/native hashes and exact graph/report parity, but its independent analyzer failed the dense-family progress oracle. The preregistration incorrectly predicted D progress steps from D newly inserted effect edges. The native report counts the successful rule application as one progress step even when that application inserts D distinct edges. The retained failed pilot and analysis are `mutation_closure_trace_overhead_v1_failed_oracle_pilot_20260928.json` and its `_analysis_` companion.

Correct the dense-family semantic oracle to require one progress step and exactly D derived edges. The sparse family continues to require one progress step and one derived edge. No workload, timing, arm, replication, or source-stability condition changes. The analyzer will separately gate report fixed-point status, progress steps, edge cardinality, exact graph digest parity, counter parity, and trace reconciliation. The corrected capture must use a new source/native lock.

## Timed-batch and work-attribution refinement

The corrected eight-fixture-per-arm rerun passed all semantic and parity gates, but its timing deltas remained noisy, including negative differences substantially larger than the expected instrumentation cost. Preserve it as the short-batch pilot. Before the confirmatory capture, raise the timed batch to 32 independently preconstructed fixtures per arm. Add an audit-work gate: across all calls in a sparse cell, `cand_tested` must equal 32; in a matcher-dense cell it must equal `32*(D²+D)` (72 candidates per fixture for D=8). This verifies that the workload family actually reaches the intended sparse/dense candidate paths. No family, size, arm, mutation, or timing-boundary definition changes. The confirmatory capture uses the updated source lock.
