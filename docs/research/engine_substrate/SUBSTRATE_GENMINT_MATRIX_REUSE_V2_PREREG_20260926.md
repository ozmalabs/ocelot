# Full-seed GenMint extended-horizon and staged-cost preregistration

**Lock date:** 2026-09-26, before capture. **Question:** after the matrix/layout confirmation found exact reuse but no runtime crossover through K=4, does any measured crossover occur through K=16, and can the training-stage and subsequent-application closure costs be reported separately on matched workers?

## Design

Reuse the v1 matrices (`prior_matrix [1,1,0,2]`, `shearA [1,0,1,1]`, `shearB [1,1,0,1]`), three predicate layouts, six training rows, and the same full-seed production path. Preserve the `shearB × adjacent_01` acquisition miss as a registered negative cell. Cross matrix × layout × GenInfer enabled/disabled × K={0,1,2,4,8,16}, with five fresh-process repetitions: 3×3×2×6×5 = 540 workers. Each K arm applies a prefix of one common ordered held-out task list, so costs at K are cumulative and comparable.

The 16 four-relation held-out bases are generated before capture using Python `random.Random(20260930)`, drawing coordinates independently from `[0,7]` until a base has four unique points, at least three distinct values in each coordinate, and the first three points are non-collinear. The runner writes the realized coordinates and targets into every raw worker row; the analyzer independently reconstructs the generated list and all targets. Predicate sequence is p0,p1,p0,p1. Each target is the assigned matrix applied to the base coordinates. This is a controlled shape generator, not a sample of natural tasks.

## Measures and analysis

Record native closure wall time and quanta for the training closure and for every held-out application closure separately, generator inventory before/after each stage, selected transforms, statuses, graph node counts, total quanta, full-process peak RSS, and worker PID. Independently score matrix acquisition, selected-generator provenance (training-acquired, application-minted, application-reused, pre-existing, or no selected generator), and exact held-out prediction under the returned generator plus residual transforms.

For each matrix/layout/replicate/K, report cumulative training-plus-application closure time, cumulative application-only closure time, and corresponding disabled control. Also report matched training-stage deltas and the per-application closure sequence separately; these expose where enabled cost is spent without claiming the rule engine has been instrumented below a closure call. Report median and range, first measured pooled and per-stratum runtime crossover, training acquisition rate, exact transfer conditional on training acquisition, quanta, graph growth, and process RSS. This is an extended finite-horizon cost curve, not an asymptotic fit.

Integrity gates: exact 540-worker design, balanced 90 cells × five workers, unique PIDs, no worker failures, exact deterministic schedule and heldout reconstruction, exact target reconstruction, stable within-cell task outcomes, runner/analyzer/protocol/native source and lock hashes, and no unclassified generator route. Acquisition and crossover are measured outcomes, not pass requirements. Any discrepancy or null result is retained.

## Provenance and execution

The runner lock covers this protocol, exact runner/analyzer sources, seed/modules/Rust files, and installed native extension. Save its exact `--lock` output at `evaluation/substrate_capability/genmint_matrix_reuse_v2_lock_20260926.json` before the capture. The runner refuses source-lock changes or stale native builds. Outputs are distinct from v1.

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_matrix_reuse_probe_v2.py --lock
# Save exact JSON to evaluation/substrate_capability/genmint_matrix_reuse_v2_lock_20260926.json
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_matrix_reuse_probe_v2.py
python3 scripts/analyze_genmint_matrix_reuse_probe_v2.py
```

This extends the same three authored linear matrices on one host. It does not establish general learning accuracy, natural-task prevalence, cheap-cut frame locality, commodity-scale performance, or asymptotic complexity.
