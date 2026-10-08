# Bounded coupled-quadratic synthesis v1 preregistration

## Question

Can the current native `SynthEnumerate` path acquire and transfer the coupled map that the GenInfer v1.5 measurement did not learn, when its bounded grammar is supplied cross-coordinate multiplication? This is a direct program-synthesis capability test. It does not integrate the result with GenInfer or demonstrate autonomous self-modification.

## Tasks and splits

The linear positive control is `T(r,c)=(r+c,2c)`. The target is `T(r,c)=(r+r*c,c+r*r)`. Both use training inputs `(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)`. Linear held-outs are `(0,3),(2,3),(1,4),(4,4),(2,5),(5,5)`. Quadratic held-outs are `(0,0),(2,0),(0,2),(2,2),(1,3),(3,3)`. Outputs are generated from the formulas in the locked runner and independently reconstructed by the analyzer.

## Search arms and budget

Three cells are registered: linear control with `Plus, TupleOf`; quadratic target with `Plus, TupleOf` (operator ablation); and quadratic target with `Plus, Times, TupleOf` (operator included). Constants are forbidden. Maximum term size is 7 and maximum candidate count is 150,000 per acquisition. There are ten fresh-substrate repetitions per cell, shuffled with seed 20261005. Found terms are evaluated on all six held-outs and in reuse batches of 1, 2, 5, and 100.

## Admission and interpretation

The source/native lock is created before capture. The independent analyzer checks lock stability, the full 30-cell matrix, candidate accounting, formula reconstruction, and independently replays every found term on every held-out point. The linear positive control must acquire exact transfer in 10/10 runs for admission. Quadratic acquisition and exact-transfer rates are outcomes, not admission conditions. A cap refusal means no result within the registered budget; it does not prove the target is unrepresentable. Any quadratic exact transfer is evidence only for this supplied finite grammar, authored task, and native direct-synthesis route. Comparison to GenInfer v1.5 is descriptive because the hypothesis language and execution route differ.

## Reproduction

Run `python3 scripts/substrate_synthenumerate_coupled_quadratic_v1.py --lock` to create the lock, then run the same command without arguments for capture. Analyze with `python3 scripts/analyze_substrate_synthenumerate_coupled_quadratic_v1.py`. The lock, raw capture, and analysis are retained under `evaluation/substrate_capability/` and `evaluation/reports/` with the v1 date stem.
