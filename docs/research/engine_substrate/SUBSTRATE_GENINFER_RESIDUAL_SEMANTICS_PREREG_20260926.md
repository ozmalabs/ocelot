# GenInfer residual-semantics audit preregistration (2026-09-26)

## Status and question

This is a confirmatory repeat of an explicitly exploratory field inspection prompted by the selected-null refusal captures. The question is whether accepted coordinate-perturbed cases are represented by residual transforms, and whether the positive controls have none.

## Locked design

Use the four maps and four-relation signature from the noise-refusal protocol, with two conditions per map: exact `positive`, and `point_corrupt_p1` (increment only p1's first target coordinate by one). Make five repetitions per cell. Read `explained`, `matrix`, `residual_dims`, `transforms`, `dims`, and `checked` on each fresh evaluation. This is a field-semantics audit; do not interpret its repeated calls as independent task samples or time them as a performance benchmark.

## Expected output and gates

For all 20 positive calls: `explained=true`, exact locked matrix, `residual_dims=0`, empty `transforms` and `dims`, and `checked=6560`. For all 20 perturbed calls: `explained=true`, same locked matrix, `residual_dims=1`, one `shift` transform on dimension 1 with delta +1 and predicate p1, `dims=[1]`, and `checked=6560`. Verify deterministic condition construction, complete balanced cells, finite-independent raw values (no timing field), and current source/native hashes. Any mismatch fails the semantic contract gate.

## Claim boundary

Four small 2-D integer-linear maps, one source motif, one coordinate perturbation, and repeated direct evaluator reads only. This characterizes the output decomposition for this fixture. It does not validate transform soundness over other perturbations, natural noise, or end-to-end mint/reuse behavior.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/geninfer_residual_semantics_probe_v1.py
python3 scripts/analyze_substrate_geninfer_residual_semantics_probe_v1.py
```
