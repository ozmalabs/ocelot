# GenInfer transform-family probe results (2026-09-26)

## Result

The preregistered probe passes all 11 independent gates. Five calls for each of four invertible transform matrices recover the exact expected matrix (20/20). Every case uses the same four unique-predicate relations, an independently derived B=4, and 6,560 candidate matrices. Source/native hashes, condition schedule, and finite timing samples verify.

## Timing

| Transform family | Median | Range | Ratio vs first family |
|---|---:|---:|---:|
| Asymmetric scale-shear `[1,1,0,2]` | 11.18 ms | 11.10–11.65 ms | 1.000 |
| Anisotropic scale `[2,0,0,1]` | 11.68 ms | 11.12–12.05 ms | 1.045 |
| Swap-scale `[0,2,1,0]` | 11.40 ms | 11.17–13.01 ms | 1.020 |
| Coupled shear `[2,0,1,1]` | 11.21 ms | 11.13–11.74 ms | 1.002 |

The observed timing differences are small relative to the five-sample ranges and do not support a transform-specific cost ordering. The fixed-bound candidate loop appears to dominate for these cases; that is an interpretation of this probe, not an instruction-level attribution.

## Claim boundary and next work

This extends positive recovery beyond one matrix while keeping relation count, correspondence, dimension, and search bound fixed. It does not establish robust learning under noise, nonlinear or noninvertible transforms, higher-dimensional inference, automatic mint/closure acquisition cost, or natural-task utility. Combine these transforms with preregistered null/noise cases and then measure the full seed path, including recognition, minting, and subsequent reuse, before making rung-three tractability claims.

## Reproduction

- Protocol: [preregistration](SUBSTRATE_GENINFER_TRANSFORM_FAMILY_PREREG_20260926.md)
- Runner: [capture script](../../../scripts/geninfer_transform_family_probe_v1.py)
- Independent analyzer: [analysis script](../../../scripts/analyze_substrate_geninfer_transform_family_probe_v1.py)
- Raw: [JSON](../../../evaluation/reports/substrate_geninfer_transform_family_v1_20260926.json)
- Analysis: [JSON](../../../evaluation/reports/substrate_geninfer_transform_family_v1_analysis_20260926.json)
