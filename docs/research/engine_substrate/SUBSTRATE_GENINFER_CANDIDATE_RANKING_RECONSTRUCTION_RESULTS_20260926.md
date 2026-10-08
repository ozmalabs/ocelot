# GenInfer candidate-ranking reconstruction results (2026-09-26)

## Validation

The source-derived Python enumerator matches the native capture's winner fields on all 18 layout × identity-mode × corruption cells. The analyzer independently verifies the five native repeats per cell, input-capture digest, candidate count formula, score ordering, native binary hash, and reconstruction source hashes. All eight gates pass. This is a replay model checked against native outputs, not instrumentation of the Rust loop.

## What the candidate set shows

- **Search-bound exclusion is not the cause.** Every generating matrix is inside the enumerated coefficient cube: B=2 for 624 candidates and B=4 for 6,560 candidates, while the largest true coefficient is 2.
- **Stable-ID original geometry, all magnitudes:** the generating matrix is not eligible under the predicate-local uniform-shift check. Each accepted corruption has exactly one eligible matrix: `[0,0,0,2]`, `[-1,-1,0,2]`, or `[-2,-2,0,2]`. Stable IDs fix pairings, which leaves a within-p0 coordinate discrepancy that no single p0 residual shift can absorb with the true matrix.
- **No-ID original +2:** three candidates are eligible. The true matrix has score `[1 residual, L1=4, [1,1,0,2]]` and beats the two-residual candidates at the first Occam term.
- **No-ID paired-square +2:** 25 candidates are eligible. The true matrix is eligible with score `[1,4,[1,1,0,2]]`, but `[-1,0,0,2]` has one residual and L1=3, so the L1 tie-break selects the alternative. This is a direct, reconstructed instance of Occam ranking selecting a non-generating matrix even though the generator remains eligible.
- **Stable-ID paired-square +2:** no candidate is eligible, so GenInfer refuses; this contrasts with the accepted no-ID case.

These results split the ambiguity into two mechanisms: alignment/predicate-uniformity can make the generating matrix ineligible, and where it remains eligible, the declared ranking can prefer a lower-norm alternative. Neither issue is caused by the B bound in these fixtures.

## Limits

The reconstruction mirrors the documented integer 2-D enumeration and numeric residual grouping on 18 small captured cases. It does not examine native candidate traces, other value types, higher dimensions, multiple codebook parts, or automatic mint behavior. A broader proof would require native per-candidate instrumentation or independent fixtures covering those branches.

## Artifacts

Protocol: [`SUBSTRATE_GENINFER_CANDIDATE_RANKING_RECONSTRUCTION_PREREG_20260926.md`](SUBSTRATE_GENINFER_CANDIDATE_RANKING_RECONSTRUCTION_PREREG_20260926.md). Reconstructor/analyzer: [`reconstruct_geninfer_candidate_ranking_v1.py`](../../../scripts/reconstruct_geninfer_candidate_ranking_v1.py), [`analyze_geninfer_candidate_ranking_v1.py`](../../../scripts/analyze_geninfer_candidate_ranking_v1.py). Input capture: [`relation-identity ablation`](../../../evaluation/reports/substrate_geninfer_relation_identity_ablation_v1_20260926.json). Candidate ranking record: [`substrate_geninfer_candidate_ranking_v1_20260926.json`](../../../evaluation/reports/substrate_geninfer_candidate_ranking_v1_20260926.json). Analysis: [`substrate_geninfer_candidate_ranking_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_geninfer_candidate_ranking_v1_analysis_20260926.json). Relevant Rust source: [`shape_decode.rs`](../../../runners/dsl/src/shape_decode.rs).
