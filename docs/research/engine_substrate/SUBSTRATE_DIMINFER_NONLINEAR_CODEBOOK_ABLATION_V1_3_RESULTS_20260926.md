# Full-seed nonlinear DimInfer codebook ablation results

## Confirmatory capture

The v1.3 preregistered capture completed 72 fresh workers (eight transform families × three asymmetric geometries × three replicates), each with intact and matched codebook-ablated full-seed states. There were zero worker failures, 72 unique PIDs, stable locked source/native inputs, and all 14 independent analysis checks passed. GenInfer was explicitly off in both arms. The v1 and v1.1 harness failures, v1.2 capture, and initial analyses are retained but excluded from the reported quantum outcomes: v1/v1.1 had harness/schema errors, v1.2 counted the quantum inventory after closure in both fields, and its first analyzer compared a JSON list to tuple reconstruction. V1.3 fixes the measurement boundary and uses the disclosed corrected independent analyzer. One single-cell smoke check was used only to validate v1.2 wiring and is not part of the capture.

## Exact route, alternate route, and fallback

Every intact case is `recognized_transformed`, but route-level scoring gives a more precise result:

| Requested family | Exact intended sequence selected | Matched ablation result |
|---|---:|---|
| `rotation90` | 9/9 | 9/9 mint one CapabilityAxis quantum |
| `reflection_r` | 9/9 | 9/9 still recognized through an alternate generator sequence |
| `reflection_c` | 9/9 | 9/9 still recognized through an alternate generator sequence |
| `scale2` | 9/9 | 9/9 mint one quantum |
| `cycle4` | 9/9 | 6/9 mint one quantum; 3/9 are explained by `reflection_r` |
| `rotation90 → cycle4` | 9/9 | 9/9 mint one quantum |
| `reflection_r → cycle4` | 6/9 | 9/9 mint one quantum |
| `rotation90 → scale2` | 9/9 | 9/9 mint one quantum |

The reflection ablations reveal an exact algebraic alias, not just a fixture effect. Since two `rotation90` steps form a half-turn, `reflection_r = reflection_c → rotation90(k=2)` and `reflection_c = reflection_r → rotation90(k=2)` on every bounded point set. Removing `reflection_r` selects the exact residual-free alternate on six cells; on the third geometry it selects `cycle4(k=1)` plus predicate-local shifts (+2 for p2 and −2 for p3). Removing `reflection_c` selects the exact residual-free alternate on all nine cells. For `reflection_r → cycle4`, three intact geometries select `cycle4(k=2)` plus the opposite predicate-local shifts instead of the intended two-step sequence. These local residual decompositions depend on the selected geometry; the reflection identities do not. Endpoint coordinates alone cannot identify which of two exactly equivalent reflection paths generated the observation. The native operators are defined in [`shape_decode.rs`](../../../runners/dsl/src/shape_decode.rs).

All 72 intact arms add zero CapabilityAxis quanta. The 54 ablated arms that fall to `minted` add exactly one each; the remaining 21 retain a recognized-transformed status via the alternate routes above and add none. This confirms the value of the held codebook on several selected transform families and exposes the need to measure alternative explanations separately from intended-generator recovery.

## Cost observations

Median full-seed rule-closure time is about 0.70–0.74 ms for exact primitive routes and 1.60–1.70 ms for the tested two-generator compositions. Ablated reflection cases that search alternate compositions take about 1.24–1.25 ms median; cases falling directly to quantum mint are about 0.59–0.77 ms. The small paired timing differences are descriptive, include closure only, and exclude boot and fixture construction. They do not establish a runtime advantage or a scaling law.

## Interpretation and limits

This measures application of the shipped 2-D rotation, reflection, scale, modular-cycle, and selected composition operators under codebook removal. It demonstrates held-structure use and causal dependence for `rotation90`, `scale2`, and selected compositions in this fixture set. It also finds that reflection and cycle transforms are not identifiable from shape outcomes alone in all tested geometries. The study does not induce a new nonlinear primitive, measure natural task frequencies, establish general composition accuracy, or sample beyond three fixed six-point geometries.

Next, sample independently authored geometries to estimate how often geometry-specific residual aliases arise. Exact reflection identities cannot be disambiguated from endpoint coordinates; evaluate sequence identification only where histories, interventions, or another independent signal provide evidence. Separately evaluate genuine novel nonlinear induction; the current GenInfer learner remains an integer-linear inducer. Keep exact operator selection, equivalent explanation, residual, quantum mint, and runtime as separate fields.

## Artifacts

- [Preregistration](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_PREREG_20260926.md)
- [v1 harness amendment](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_1_AMENDMENT_20260926.md)
- [v1.2 fixture amendment](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_2_AMENDMENT_20260926.md)
- [v1.2.1 analysis amendment](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_2_1_AMENDMENT_20260926.md)
- [v1.3 measurement amendment](SUBSTRATE_DIMINFER_NONLINEAR_CODEBOOK_ABLATION_V1_3_AMENDMENT_20260926.md)
- [Source/design lock](../../../evaluation/substrate_capability/diminfer_nonlinear_codebook_ablation_v1_3_lock_20260926.json)
- [v1.3 runner](../../../scripts/substrate_diminfer_nonlinear_codebook_ablation_v1_3.py)
- [v1.3 independent analyzer](../../../scripts/analyze_substrate_diminfer_nonlinear_codebook_ablation_v1_3.py)
- [v1 harness failure capture](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_20260926.json)
- [v1.2 raw capture](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_2_20260926.json)
- [v1.2 initial analysis](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_2_analysis_20260926.json)
- [v1.2.1 corrected analysis](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_2_1_analysis_20260926.json)
- [v1.3 raw capture](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_3_20260926.json)
- [v1.3 analysis](../../../evaluation/reports/substrate_diminfer_nonlinear_codebook_ablation_v1_3_analysis_20260926.json)
