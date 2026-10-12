# GenInfer data-derived bound scaling results

## Result

The 24-call capture (12 scale-by-condition cells) passed all runner checks and all eight independent analysis checks across three fresh processes and coordinate scales s=1–4. The exact positive shear `[1,1,0,1]` was recovered with zero residual dimensions at every scale; a same-geometry case with one predicate corrupted was explicitly unexplained at every scale. The analyzer independently recomputed the normalized coordinate bound and `(2B+1)^4−1` candidate formula, matching the native `checked` field on both positive and null calls.

Because the goal shear expands the maximum normalized coordinate to B=3s, candidate counts are 2,400, 28,560, 130,320, and 390,624. Median positive direct-Term wall times are 3.01, 33.17, 150.16, and 452.55 ms; median process CPU times nearly match. Across these bounded points, time is roughly proportional to candidate count at about 1.15–1.25 microseconds per candidate. At B=12, the null still checks all 390,624 matrices, but median time is 283.53 ms versus 452.55 ms positive. Thus `checked` captures search cardinality, while time also reflects how quickly `build_candidate` rejects each matrix. No fit or extrapolation is claimed.

## Interpretation and limits

This isolates the production Rust `GenInfer` Term with one codebook part, fixed 2-D transform, and one predicate-corruption class. It empirically shows the fourth-power bound’s cost through B=12 and validates the operator count as a useful primary work measure. It does not include rule-closure repetition, graph mint/redecode, broader residual ranking, boot/setup, other transforms, dimensions above two, or natural input frequencies. The separate full-seed GenInfer experiment covers acquisition/reuse for a smaller authored family; this direct sweep measures the search kernel only.

The first harness launch completed worker calculations but stopped before writing the aggregate because of a JSON gate field-path error. That failure is preserved. The corrected gate changed no workload or criteria; the source was relocked and all cells rerun.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_GENINFER_BOUND_SCALING_PREREG_20260926.md)
- Runner: [`substrate_geninfer_bound_scaling_v1.py`](../../../scripts/substrate_geninfer_bound_scaling_v1.py)
- Independent analyzer: [`analyze_substrate_geninfer_bound_scaling_v1.py`](../../../scripts/analyze_substrate_geninfer_bound_scaling_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/geninfer_bound_scaling_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_geninfer_bound_scaling_v1_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_geninfer_bound_scaling_v1_analysis_20260926.json)
- Preserved harness failure: [failure record](../../../evaluation/reports/geninfer_bound_scaling_v1_harness_failure_20260926.json)
