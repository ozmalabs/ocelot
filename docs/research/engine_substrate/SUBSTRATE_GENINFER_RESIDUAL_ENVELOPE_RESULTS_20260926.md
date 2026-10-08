# GenInfer residual-envelope results (2026-09-26)

## Outcome

All 12 independent integrity and semantic gates pass across 110 field observations (five repeats). The suite covers four matrices with five unique-predicate conditions each, plus two repeated-predicate cases.

The unique-predicate cases behave as locked: positives return the exact matrix and no residual; a global +1 row-coordinate shift returns the same matrix plus one `shift`; simultaneous +1 row and +2 column shifts return two residual entries at `max_dims=2`, and are refused at `max_dims=1`; global red→blue substitution returns one `subst`. A repeated-predicate symbolic conflict (the same held value would map to blue and green) is refused.

The repeated-predicate numeric perturbation reveals a representational ambiguity. The data were generated from `[1,1,0,2]`, then the two p0 target rows received different row shifts (+1 and +2). Across all five repeats, GenInfer selected `[-2,-2,0,2]` and represented the observation using p0 `shift(+3)` and p1 `shift(+6)` residuals on the same slot. This is stable, but it does not recover the generator used to construct the unperturbed target. The case shows that predicate-local residual support can trade off against the inferred matrix; the current Occam ranking does not guarantee recovery of the generating matrix under inconsistent observations.

## Implications

Residual decomposition now has direct evidence for numeric shifts, symbolic substitution, multiple residual entries, the `max_dims` gate, and one symbolic-function refusal. It remains a small evaluator envelope, not broad residual precision/recall. For learning claims, report generator recovery separately from decomposition acceptance. The next test should vary repeated-predicate geometry and perturbation size to measure when this alternate-matrix outcome appears, and whether a matrix-only or residual-complexity tie-breaker restores recovery without increasing false acceptance.

## Limits and artifacts

One authored motif, four small 2-D maps, four unique-predicate residual conditions, and one repeated-predicate arrangement were used. No timings, full-seed closure, automatic minting, or natural-noise distribution were measured.

Protocol: [`SUBSTRATE_GENINFER_RESIDUAL_ENVELOPE_PREREG_20260926.md`](SUBSTRATE_GENINFER_RESIDUAL_ENVELOPE_PREREG_20260926.md). Runner/analyzer: [`geninfer_residual_envelope_probe_v1.py`](../../../scripts/geninfer_residual_envelope_probe_v1.py), [`analyze_substrate_geninfer_residual_envelope_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_residual_envelope_probe_v1.py). Raw: [`substrate_geninfer_residual_envelope_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_residual_envelope_v1_20260926.json). Analysis: [`substrate_geninfer_residual_envelope_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_residual_envelope_v1_analysis_20260926.json).
