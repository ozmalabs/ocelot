# Multi-sheet vision fold coupling scale results

**Run:** 2026-09-25. **Evidence:** 48 native arms: three deterministic afferent seeds × four sheet sizes × global/scoped fold × low/high second-sheet state. Independent equation and counter audit passes.

## Result

Each substrate held two separate `World` roots with equal square SUnit lattices. Changing every B unit from act=0 to act=1 changed the global mean from 0.5 to 1.0. Sheet A's output changed by exactly 0.5 in every seed/size pair. Under the benchmark-only root-scoped variant, A's output was identical across B conditions at all 12 pairs. Every arm matched an independent implementation of the settlement equation within 1e-12; root memberships were disjoint and exact. Progress stayed below the 10,000 cap, and candidate-test and Term-unit counters reconciled with their per-rule totals.

| Side per sheet | SUnits total | Global `NodesOfType` units | Scoped `NodesOfType` units | A response change: global | A response change: scoped |
|---:|---:|---:|---:|---:|---:|
| 2 | 8 | 136 | 8 | 0.5 | 0 |
| 4 | 32 | 2,080 | 32 | 0.5 | 0 |
| 8 | 128 | 32,896 | 128 | 0.5 | 0 |
| 16 | 512 | 524,800 | 512 | 0.5 | 0 |

The work counts are medians across the three fixed seeds and use one B-state condition per variant; both B conditions had the same work counts. They are native `NodesOfType` interior cardinality work units, not elapsed time or CPU instruction counts.

## Interpretation and limits

This extends the earlier two-pair semantic probe to full synthetic grids through 512 SUnits. It confirms that the authored global fold couples independently rooted sheets and that replacing the fold with root membership removes that cross-root path while preserving the local equation on these fixtures. The source's global fold therefore defeats frame independence across roots unless the system scopes or factors that dependency explicitly.

This does not show how frequently natural substrate workloads contain such global dependencies. The generated grids have a deliberately simple state pattern; only one rule and no learning or downstream task were measured. No production seed was changed, no timing comparison was made, and the benchmark clone is not a production frame scheduler.

## Evidence

- [preregistration](SUBSTRATE_VISION_MULTI_SHEET_SCALE_PREREG_20260925.md)
- [runner](../../../scripts/substrate_vision_multi_sheet_scale.py)
- [independent analyzer](../../../scripts/analyze_substrate_vision_multi_sheet_scale.py)
- [raw report](../../../evaluation/reports/substrate_vision_multi_sheet_scale_20260925.json)
- [analysis](../../../evaluation/reports/substrate_vision_multi_sheet_scale_analysis_20260925.json)
- [lock](../../../evaluation/substrate_capability/vision_multi_sheet_scale_lock_20260925.json)
