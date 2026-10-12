# Full-seed GenInfer residual-robustness preregistration (2026-09-26)

## Question

Do the direct GenInfer decomposition ambiguities observed under repeated-predicate corruption change what the production `shape_decode_loop` mints and whether later clean orbit members reuse the resulting codebook?

## Factorial design

Cross three base layouts (`original`, `orthogonal_pairs`, `paired_square`), two signature modes (`no_identity`, `stable_identity`), four first-member conditions (`positive`, or p0 relation 0 row-coordinate corruption +1/+2/+3), and the seed switch (`gen_infer_enabled` on/off). Use five fresh-core replicates per cell: 3×2×4×2×5 = 240 three-observation sequences. Randomize the 48 cells within each repetition using Python `Random(20260926)` and store the full schedule.

Each sequence installs the production seed and a graph-resident base `ShapeSignature`. It observes, in order: the clean `M(base)` (`M=[1,1,0,2]`) or its registered corruption; then clean `M²(base)`. Stable-identity signatures put a unique unchanged string ID after predicate and before coordinates; the no-ID arm reproduces the earlier four-slot signatures. All use `max_dims` and other seed behavior unchanged. After every full native rule closure, record observation status/attrs, residual transform nodes, newly minted CapabilityAxis count, all linear generator attrs, codebook epoch, closure elapsed time, and graph size. Do not directly invoke GenInfer or insert inferred nodes.

## Measures and gates

The primary measures are first-member route (`recognized_transformed`, `minted`, other terminal status), matrix of each linear generator after every stage, per-stage and cumulative quantum count, later clean-member status, later new generator count, and closure latency. Report exact-matrix acquisition separately from any linear-generator acquisition. Summarize paired enabled/disabled differences by layout, identity mode, and perturbation magnitude. No universal performance or accuracy threshold is set.

Integrity gates: 240 complete sequences; exactly two settled observations per sequence; fixed input construction; positive and corruption labels match targets; the disabled arm never contains a newly minted linear generator; repeated outputs/state summaries are stable within each cell except timing; finite positive closure timings; deterministic schedule; and current source/native hashes. Enabled-arm discovery and reuse outcomes are measurements, not pass/fail assumptions.

## Claim boundary

One authored 2-D generator, three repeated-predicate layouts, one corruption site, three magnitudes, five fresh-core replicates per cell, and the existing production seed. This measures full-seed mint/reuse sensitivity for these fixtures; it does not estimate natural noise, general generator-learning capability, or commodity-scale resources.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/genmint_residual_robustness_probe_v1.py
python3 scripts/analyze_substrate_genmint_residual_robustness_probe_v1.py
```
