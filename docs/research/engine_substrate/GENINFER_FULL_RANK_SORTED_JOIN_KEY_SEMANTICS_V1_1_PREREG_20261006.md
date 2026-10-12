# Sorted GenInfer identity join: key semantics v1.1

Status: preregistered extension, run on 2026-10-06. This gate checks
semantic preservation only; it makes no timing or natural-prevalence claim.

## Question

Does the feature-gated sorted identity join preserve the solver's baseline
behavior when key ordering and `Value` equality interact, including key values
that must use the nested fallback?

## Frozen cases

Each case uses the existing 3-D full-rank shear fixture at 16 relations, with
the same solver rules enabled in both builds. The baseline has
`geninfer_full_rank_matrix_solver`; the candidate additionally has
`geninfer_full_rank_sorted_identity_join`. Source and target row order remains
independently shuffled by the existing v2.3 worker.

* `mixed_numeric`: source IDs are integers and target IDs are equal-valued
  floats. This exercises cross-variant equality on a comparator-equal key.
* `float_keys`: both sides use float IDs. Float keys are unsupported by the
  sorted fast path and must preserve baseline behavior through fallback.
* `bool_int`: source IDs alternate booleans and target IDs use the equal
  integers 0/1; predicate values distinguish each pair. This exercises the
  `Bool`/`Int` equality-versus-ordering mismatch and must use fallback.
* `compound_keys`: both sides use unique one-element list IDs; both arms must
  preserve the baseline outcome (the existing solver is expected to refuse).
* `duplicate_ids`: all relations share one identity key; both arms must preserve
  the baseline refusal.
* `missing_ids`: source and target use disjoint key strings; both arms must
  preserve the baseline refusal.

For every case and both phases (training and held-out), require equal status,
`covered_by`, and transform receipts between baseline and candidate, plus
stable source hashes. The first three cases must learn/reuse a transform; the
compound, duplicate, and missing-key cases must preserve their baseline
outcomes without a transform receipt. This gate does not cover NaN, rational,
other nested values, or wide key vectors.

## Run

Build the baseline and candidate from the same checkout using the feature sets
above. Prepare isolated overlays with the runner's `--prepare` command, then
run `--capture`. The runner freezes its own source, the v2.3 workload worker,
this protocol, Cargo metadata, and both native artifact hashes into the
capture. The result is `evaluation/reports/geninfer_full_rank_sorted_join_key_semantics_v1_1_20261006.json`.

This is a narrow correctness gate. Promotion still requires a broader key
matrix and an ordinary-task prevalence census.
