# GenInfer selected-null refusal results (2026-09-26)

## Outcome

The preregistered diagnostic v1 and amended v2 both fail the all-null-refusal gate. Positive recovery is perfect (20/20 per capture), and predicate-corrupt, missing-relation, and extra-relation controls are refused (60/60 each). However, every coordinate-perturbation control is accepted (20/20) and returns the same matrix as its positive counterpart. The v1 origin perturbation is translation-equivalent under coordinate origin normalization. The v2 p1 perturbation is also accepted, showing that `explained=true` does not mean the matrix alone exactly accounts for all observed coordinate differences.

In `shape_decode.rs::eval_gen_infer`, a winning matrix can be returned with residual `DimTransform`s (`cand.transforms`); the acceptance predicate requires those transforms to be accounted for in `dims_needed`, not that the matrix alone exactly predicts the observation. This is consistent with the implementation's stated role as a generator inference plus residual transform decomposition. Consequently, coordinate corruption is not a valid null for the current boolean `explained` contract. The accepted-control pattern is deterministic in all 20 repetitions per capture, not timing noise.

## Timing

V2 timed only `GenInfer(field=explained)`; fields for matrix and checked candidates were read outside the timed interval. Each of 20 cells has five calls at B=4 and 6,560 enumerated candidates. Median time was 11.30 ms for positive observations and 11.36 ms for the accepted p1-perturbation control. Predicate-corrupt, missing-origin, and extra-relation controls stopped earlier, with medians 4.48, 4.37, and 4.39 ms respectively. These are narrow direct-call measurements, not end-to-end closure or mint costs.

## Gate record

V2 passes factorial completeness, locked input, generated signature, fixed bound/count, positive recovery, finite timing, deterministic schedule, and source/native hash checks. It fails `all_null_cases_refused` solely because `point_corrupt_p1` is accepted. The v1 failure is preserved in `substrate_geninfer_noise_refusal_v1_analysis_20260926.json`; v2 is in `substrate_geninfer_noise_refusal_v2_analysis_20260926.json`. No capture was overwritten.

## Claim boundary and follow-up

This evaluates four 2-D integer-linear signatures with unique predicates, four selected null classes, five repeats, and no realistic observation-noise distribution. It establishes selected refusal for predicate and coverage mismatches, and identifies an API/semantic distinction between “a linear generator is inferred” and “the full observation is explained by that generator alone.” It does not estimate a false-positive rate.

Next, measure `residual_dims` and returned transforms on coordinate-corruption cases, then define separate acceptance criteria for generator recovery, residual-decomposed explanation, and exact matrix-only fit. Only after those semantics are preregistered should broader noise classes or calibration be run.

## Reproduction and artifacts

Protocol and amendment: [`SUBSTRATE_GENINFER_NOISE_REFUSAL_PREREG_20260926.md`](SUBSTRATE_GENINFER_NOISE_REFUSAL_PREREG_20260926.md).

Runners: [`geninfer_noise_refusal_probe_v1.py`](../../../scripts/geninfer_noise_refusal_probe_v1.py), [`geninfer_noise_refusal_probe_v2.py`](../../../scripts/geninfer_noise_refusal_probe_v2.py). Analysers: [`analyze_substrate_geninfer_noise_refusal_probe_v1.py`](../../../scripts/analyze_substrate_geninfer_noise_refusal_probe_v1.py), [`analyze_substrate_geninfer_noise_refusal_probe_v2.py`](../../../scripts/analyze_substrate_geninfer_noise_refusal_probe_v2.py).

Raw captures: [`v1`](../../../evaluation/reports/substrate_geninfer_noise_refusal_v1_20260926.json), [`v2`](../../../evaluation/reports/substrate_geninfer_noise_refusal_v2_20260926.json). Independent analyses: [`v1`](../../../evaluation/reports/substrate_geninfer_noise_refusal_v1_analysis_20260926.json), [`v2`](../../../evaluation/reports/substrate_geninfer_noise_refusal_v2_analysis_20260926.json).
