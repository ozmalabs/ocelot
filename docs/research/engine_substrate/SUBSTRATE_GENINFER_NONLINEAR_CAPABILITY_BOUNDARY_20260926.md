# GenInfer nonlinear capability boundary (2026-09-26)

## Finding

Current GenInfer is a bounded integer-linear inducer, not an open-ended primitive learner. `eval_gen_infer` in `runners/dsl/src/shape_decode.rs` accepts frames with exactly two coordinate dimensions, derives a finite integer-entry bound from the observed base and goal, enumerates 2×2 matrices, applies each matrix once, and ranks candidates that satisfy the shared residual-consistency check. It does not search over arbitrary functions, program syntax, or newly defined operator families.

The decode-time `Generator` representation confirms this limit. `kind` selects a finite implementation dispatch. The `linear` kind is the only map whose operation is supplied as graph data (`matrix`); `translate` supplies an offset vector. Rotation, reflection, scale, cycle, and the other kinds are already implemented operators. Discovering a new matrix therefore mints data consumed by existing code, while discovering a new nonlinear primitive would require a search/representation/admission mechanism that is not present in this path.

## Existing evidence

- The full-seed GenMint measurement reports a nonlinear warp remains outside the linear inducer. This is an explicit negative capability result on its registered fixture, not evidence that all nonlinear families fail. See [`SUBSTRATE_GENMINT_MEASUREMENT_RESULTS.md`](SUBSTRATE_GENMINT_MEASUREMENT_RESULTS.md), runner [`genmint_measure.py`](../../../scripts/genmint_measure.py), and [analysis](../../../evaluation/reports/substrate_genmint_measurement_analysis_20260926.json).
- The held-operator DimInfer panels show that preinstalled nonlinear operators can be applied and ablated. They measure codebook application, not induction of a new operator. See [`SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_RESULTS_20260926.md`](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_RESULTS_20260926.md) and [`SUBSTRATE_DIMINFER_NONLINEAR_GEOMETRY_DISTRIBUTION_V2_RESULTS_20260926.md`](SUBSTRATE_DIMINFER_NONLINEAR_GEOMETRY_DISTRIBUTION_V2_RESULTS_20260926.md).
- GenInfer residual/noise and held-out relation work measures decompositions within the current matrix family. It finds that consistent training residuals can transfer incorrectly to clean holdouts; `explained=true` is not a held-out correctness metric. See [`SUBSTRATE_GENINFER_HELDOUT_RELATION_RESULTS_20260926.md`](SUBSTRATE_GENINFER_HELDOUT_RELATION_RESULTS_20260926.md), [`SUBSTRATE_GENINFER_RESIDUAL_SEMANTICS_RESULTS_20260926.md`](SUBSTRATE_GENINFER_RESIDUAL_SEMANTICS_RESULTS_20260926.md), and [`SUBSTRATE_GENMINT_RESIDUAL_ROBUSTNESS_RESULTS_20260926.md`](SUBSTRATE_GENMINT_RESIDUAL_ROBUSTNESS_RESULTS_20260926.md).

## What is supported, and what is not

Supported claim: on bounded 2-D integer-coordinate fixtures, the current path can infer a 2×2 integer matrix, attach a checked residual decomposition, mint the matrix as graph data, and reuse it through decode. Separate experiments measure selected held operators, noise sensitivity, acquisition cost, and later reuse.

Unsupported claim: the current path learns arbitrary nonlinear dimensions, searches for new primitive programs, or has a general Rung 3/4 solution. Held nonlinear operators and finite authored nonlinear codebooks are application of prior structure. They are not evidence of learning that structure.

This narrows the tractability report's residue: within the current family, candidate search is finite and bounded by the observed coordinate extent (with a potentially expensive fourth-power matrix enumeration); beyond that family there is no measured learner envelope because this route has no nonlinear hypothesis search. The larger open question is not yet the runtime of general nonlinear induction, but whether any production learning route proposes, validates, mints, and safely adopts such a new operator.

## Registered capability gate (executed in v1.1)

The preregistered production-path contrast with independently held-out nonlinear maps (including at least quadratic shear and one non-polynomial or piecewise family), a linear positive control, a held-operator control, and a no-induction/frozen-codebook control. Use enough distinct points that a 2×2 linear map plus allowed residual transforms cannot explain the training and holdout rows by coincidence. Record route reached, residual status, candidate family, mint/adoption events, exact held-out predictions, false acceptance, search budget/depth, CPU time, peak memory, and later reuse. An inability to propose a nonlinear candidate is a valid, explicit gap outcome; do not count a held operator as induction.

Before execution, lock generators, point sets, train/holdout split, control arms, source/native hashes, and independent scoring. Gate success requires the linear control to reproduce current behavior, the held-operator arm to show application only, and nonlinear outcomes to be separately classified as refusal, residual, false explanation, or a genuinely induced and held-out-valid operator. No general nonlinear-learning claim follows from one family or one run.


## Current measurement update

The next gate has now been executed as v1.1 with a passing linear control. Across ten fresh cases per arm/family, the production path induces and transfers the linear map 10/10 times, while quadratic and piecewise shear induce no operator and fall back to quantum minting 10/10 times. The quadratic miss path reaches a 2.042 s maximum closure in this capture. See [`SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_1_RESULTS_20260926.md`](SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_1_RESULTS_20260926.md). This changes the boundary from a source-only prediction into a narrow, source-current production-path measurement; it does not establish natural-task prevalence or general nonlinear learning.
