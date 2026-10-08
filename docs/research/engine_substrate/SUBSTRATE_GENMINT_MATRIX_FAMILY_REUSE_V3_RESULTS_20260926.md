# GenMint matrix-family transfer and reuse results

## Capture integrity

The preregistered factorial completed all 324 workers (six matrices × three predicate layouts × two induction arms × three reuse prefixes × three replicates) in 72.9 seconds, with no worker failures and 324 unique PIDs. The source/native lock and randomized schedule reproduce. The v3 analyzer's held-out reconstruction initially failed because it reused the schedule seed rather than the separate held-out seed. The initial analysis is retained; the v3.1 amendment changes only this reconstruction and passes all 16 integrity, semantic, and repeat checks.

## Acquisition and transfer

All 54 enabled K=0 training calls end with status `recognized_transformed`, but only 33 acquire the exact intended linear matrix. Exact acquisition is 9/9 for `prior_matrix`, `shearA`, and `shearC`; 6/9 for `shearB`; and 0/9 for coordinate swap and signed quarter-turn. The latter two are explained through pre-existing seed generators in these fixtures, not learned as the intended linear matrix. `recognized_transformed` therefore remains an inadequate acquisition metric.

Across held-out applications, the amended route scorer records 651 applications using the exact training-acquired matrix. They predict all 2,604 held-out rows exactly. This 100% conditional accuracy does not mean every held-out call transfers: the full application route counts are 651 expected training-generator uses, 54 application-minted/reused linear routes, 720 other-seed-generator routes, and 729 with no selected generator transform. Application behavior is strongly family- and layout-dependent.

At K=16, matched enabled-minus-disabled total closure medians vary in both directions: `shearA` −11.44 ms (8/9 enabled-faster pairs), `shearB` −10.17 ms (6/9), prior matrix +9.57 ms (1/9), `shearC` +12.14 ms (0/9). Axis swap and quarter-turn are already resolved through seed structure and are not induction wins (−1.89 and −0.28 ms median differences). Pooled across all six families, median paired difference is −0.056 ms and 27/54 pairs favor induction at K=16: this is effectively parity, not a stable aggregate break-even. At K=4 the pooled median difference is +1.78 ms. Training acquisition cost is therefore not generally amortized by 16 applications in this family panel.

Peak RSS medians remain around 42 MiB per worker, with no meaningful arm distinction at this scale. Boot/startup and input construction are excluded from closure timing. These timing results are single-host descriptive estimates.

## Interpretation and limits

The experiment broadens the authored generator family beyond the previous positive shear set and reveals two distinct limitations: status can report transformation recognition without acquiring the target matrix, and an acquired matrix can still be unused on many held-out calls. Conditional transfer is exact in the cases where the route scorer confirms use of the acquired matrix, but this does not establish broad transfer or prevalence. Runtime amortization is matrix-specific and the pooled result is parity through K=16. Coefficient sign/axis symmetries, six selected matrices, three layouts, one full-seed path, and 16 seeded held-out geometries do not represent natural task frequencies.

Next, expand beyond fixed 2-D integer-linear transforms and determine whether the relevant held dimensions are already available in the seed or must be induced. Add independently authored geometries and a larger held-out family; retain separate metrics for status, exact acquisition, route selection, prediction, false mint, latency tails, and per-stage cost. Natural-task frequency and substrate-wide cheap-cut locality remain unmeasured.

## Artifacts

- [Preregistration](SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3_PREREG_20260926.md)
- [Analysis amendment](SUBSTRATE_GENMINT_MATRIX_FAMILY_REUSE_V3_1_AMENDMENT_20260926.md)
- [Source/design lock](../../../evaluation/substrate_capability/genmint_matrix_family_reuse_v3_lock_20260926.json)
- [Runner](../../../scripts/genmint_matrix_family_reuse_probe_v3.py)
- [Initial analyzer](../../../scripts/analyze_genmint_matrix_family_reuse_probe_v3.py)
- [Amended independent analyzer](../../../scripts/analyze_genmint_matrix_family_reuse_probe_v3_1.py)
- [Raw capture](../../../evaluation/reports/substrate_genmint_matrix_family_reuse_v3_20260926.json)
- [Initial failed analysis](../../../evaluation/reports/substrate_genmint_matrix_family_reuse_v3_analysis_20260926.json)
- [Amended analysis](../../../evaluation/reports/substrate_genmint_matrix_family_reuse_v3_1_analysis_20260926.json)
