# Vision global-fold native work attribution

**Run:** 2026-09-25. **Evidence:** four sizes, one fixed seed, global and Retina-scoped variants, with opt-in native scale and per-rule counters. Instrumented progress and terminal states were checked against the matching uninstrumented scaling record.

## Result

All eight instrumented arms exactly matched uninstrumented progress and activation arrays. Per-rule candidate-test and Term counters summed to their global counters at every size. The authored fold clone changes only two `NodesOfType(SUnit)` source terms to `Neighbours(Retina, has_sunit)`.

| SUnits | Global `NodesOfType` calls in settle rule | Scoped calls | Extra global calls | Inferred extra node values traversed/materialized |
|---:|---:|---:|---:|---:|
| 4 | 6,144 | 2,048 | 4,096 | 16,384 |
| 16 | 24,576 | 8,192 | 16,384 | 262,144 |
| 64 | 98,304 | 32,768 | 65,536 | 4,194,304 |
| 256 | 393,216 | 131,072 | 262,144 | 67,108,864 |

The final column is derived, not a native interior-work counter: the measured difference in per-rule `NodesOfType` invocations is multiplied by the known SUnit population N. The source transformation replaces the two global SUnit folds, and the native implementation of `NodesOfType` enumerates and materializes all N matching nodes on each invocation. This is a directly attributable logical traversal/materialization count for this source path; it is not a CPU instruction count.

Across sizes, extra global values scale quadratically with N for the fixed progress envelope: each of the two replaced folds is reevaluated for each unit binding and traverses the full SUnit set. The global Term-evaluation invocation totals themselves differ from scoped by only 0.18% at N=256, illustrating why invocation counts alone miss aggregate interior work. Candidate-test counts are identical between variants; the excess is inside the global-fold Term evaluation.

## Interpretation and limits

This identifies a real all-to-all repeated traversal in the authored rule and quantifies its logical work through N=256. Yet the earlier uninstrumented timing difference was only about 5.9% at N=256. That gap indicates most wall time in this bounded workload is not explained by the incremental traversal count alone, or is obscured by other costs. Per-variant Term units do not currently record `NodesOfType`'s interior cardinality; the derived measure depends on the exact source rewrite and the known returned-set size.

The finding is for one synthetic single-sheet rule under a 1,024-progress cap and one seed. Most arms are budget-limited; this is not full convergence cost, production frame scheduling, natural-workload prevalence, or general locality evidence. Next instrument aggregate Terms with cardinality work units (or retain this derivation with a direct native oracle), measure wall overhead under repeated load, and test multiple independently rooted sheets.

## Evidence

- [preregistration](SUBSTRATE_VISION_GLOBAL_FOLD_ATTRIBUTION_PREREG_20260925.md)
- [runner](../../../scripts/substrate_vision_global_fold_attribution.py)
- [independent analyzer](../../../scripts/analyze_substrate_vision_global_fold_attribution.py)
- [raw report](../../../evaluation/reports/substrate_vision_global_fold_attribution_20260925.json)
- [analysis](../../../evaluation/reports/substrate_vision_global_fold_attribution_analysis_20260925.json)
- [lock](../../../evaluation/substrate_capability/vision_global_fold_attribution_lock_20260925.json)
