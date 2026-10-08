# Vision global versus Retina-scoped fold scaling

**Run:** 2026-09-25. **Evidence:** 12 paired fresh native workloads, three fixed seeds at four SUnit sizes. The source seed and engine were not changed.

## Design and result

The benchmark compared the authored global `NodesOfType(SUnit)` competition fold with a benchmark-only clone using `Neighbours(Retina, has_sunit)`. Each pair had identical deterministic afferents and used only `st_settle` and `st_commit` under a fixed 1,024 native progress-application budget. Sizes were 2×2, 4×4, 8×8, and 16×16 SUnits (4, 16, 64, and 256 units), with three seeds per size. Because the prior builder used a 16×16 retina that could not fit 16 units per side at RF=7, the v1.1 amendment resized the synthetic retina to preserve RF=7 and lattice margins; paired arms had identical geometry. Total graph nodes grew from median 1,912 to 30,655.

Across all 12 pairs, global and scoped arms had identical progress counts and exactly equal terminal activation arrays. Independently recomputed equation residuals were at most 1.25×10⁻¹³. The per-size median paired global/scoped wall-time ratios were 1.003, 1.008, 1.025, and 1.059. At 256 SUnits, measured medians were 3.425 s global and 3.243 s scoped for the fixed budget. Median global time rose from 6.01 ms at 4 units to 3.425 s at 256 units (about 570×); this co-varies with total graph size and does not isolate an asymptotic cost term. At 8×8 for seed 7301, both arms returned 690 applications before the cap; the other 22 arms reached the 1,024 budget. A budget exit is not evidence of convergence.

## Interpretation

Root-scoping preserved this rule's computed states on the measured single-Retina sheets, but it yielded only a small timing difference in this fixed-budget probe. This does not demonstrate that the global fold is the dominant runtime cost; matching, graph size, attribute access, and scheduler overhead also contribute. The steep increase in per-application time with sheet size is an observed envelope for this benchmark and warrants native candidate/Term attribution before assigning cause.

The comparison does establish a usable structural contrast: the global rule's dependency signature spans all SUnits, while the scoped clone is bounded by Retina membership. Yet neither the experiment nor the small timing deltas establish a general benefit from hierarchical frames. No multi-sheet isolation, production frame scheduler, task quality, learned weights, or natural workload prevalence was measured.

## Protocol qualification

The initial v1 launch stopped before n=16 because the fixed 16×16 retina rejected that size. No outcome comparison was produced from that attempt. The preregistration amendment documents the controlled retina resize before the complete run; graph size and retina dimensions are retained per arm.

## Evidence

- [v1 preregistration](SUBSTRATE_VISION_GLOBAL_FOLD_SCALE_PREREG_20260925.md)
- [v1.1 amendment](SUBSTRATE_VISION_GLOBAL_FOLD_SCALE_V1_1_AMENDMENT_20260925.md)
- [runner](../../../scripts/substrate_vision_global_fold_scale.py)
- [independent analyzer](../../../scripts/analyze_substrate_vision_global_fold_scale.py)
- [raw report](../../../evaluation/reports/substrate_vision_global_fold_scale_20260925.json)
- [analysis](../../../evaluation/reports/substrate_vision_global_fold_scale_analysis_20260925.json)
- [lock](../../../evaluation/substrate_capability/vision_global_fold_scale_lock_20260925.json)
