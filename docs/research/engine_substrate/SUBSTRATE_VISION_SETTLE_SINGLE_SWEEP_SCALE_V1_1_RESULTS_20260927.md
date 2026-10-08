# Vision settling single-sweep scale v1.1 results (2026-09-27)

## Result

The source-locked v1.1 capture and independent analyzer pass all gates (driver gates: 9/9; analyzer gates: 15/15) across three fresh processes, five supported sheet sizes, three seeds, and paired global/root-scoped rule variants. Source and engine fingerprints remain stable. The equation analyzer independently recomputes every `act_next` value; global and root-scoped outputs are identical in all 15 size/seed pairs. Every application processes exactly one candidate test per SUnit.

The preserved v1 capture had the same semantic outputs and integer work counts but failed an overly broad counter-repeatability check because `deferred_queue:fb_samples:drain_ns` varied. V1.1 retains those duration fields and requires exact equality for all non-time global counters and all per-rule/per-clause counts. See the [v1.1 amendment](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_1_COUNTER_AMENDMENT_20260927.md), [v1 capture](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_20260927.json), and [v1 analysis](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_analysis_20260927.json).

## Size envelope

Each row below summarizes exact counts repeated across seeds and workers. Timing is the median across 9 worker/seed medians; each underlying median uses five audit-disabled applications. Timing excludes graph construction, boot, commit, and fixpoint settling.

| SUnits | Variant | Candidate tests | Term evaluations | `NodesOfType` term units | Directed global-factor pairs crossing row frames | One-application median |
|---:|---|---:|---:|---:|---:|---:|
| 9 | Global | 9 | 781 | 171 | 54 | 21.7 µs |
| 9 | Root-scoped | 9 | 799 | 9 | 54 | 21.6 µs |
| 16 | Global | 16 | 1,888 | 528 | 192 | 49.9 µs |
| 16 | Root-scoped | 16 | 1,920 | 16 | 192 | 49.1 µs |
| 36 | Global | 36 | 7,252 | 2,628 | 1,080 | 180.6 µs |
| 36 | Root-scoped | 36 | 7,324 | 36 | 1,080 | 175.6 µs |
| 64 | Global | 64 | 20,176 | 8,256 | 3,584 | 502.8 µs |
| 64 | Root-scoped | 64 | 20,304 | 64 | 3,584 | 469.1 µs |
| 100 | Global | 100 | 46,036 | 20,100 | 9,000 | 1.134 ms |
| 100 | Root-scoped | 100 | 46,236 | 100 | 9,000 | 1.028 ms |

For `N` units, the seed's two global SUnit folds plus one per-binding SettleParams lookup produce exactly `2N²+N` `NodesOfType` term units; the root-scoped clone produces `N` of that counter. Candidate tests are exactly `N`. The global sum factor makes every output depend on every input activation, yielding a complete directed output/input relation, primal treewidth `N−1`, and `N(N−n_side)` unique directed pairs crossing the declared row partition. At 100 units, 90% of those pairs cross row frames.

## Interpretation and limits

This gives a measured cross-family structural counterexample to assuming that natural-looking spatial frames always have cheap boundaries: the authored visual settling rule contains explicit global competition. The row partition is imposed by the protocol; it is not a learned frame. Root scoping prevents inclusion of other sheets in the global population, but in a one-sheet graph the within-sheet factor remains complete and the cross-row pair count does not change.

At the time of v1.1, the `NodesOfType` term-unit counter fell sharply in the root-scoped clone, but adjacency items visited by `Neighbours` were not yet counted; v1.1 therefore made no total-work comparison. The follow-up [v1.4 trace capture](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_4_RESULTS_20260927.md) confirms 20,000 `has_sunit` edge visits replace 20,000 SUnit type-index items at N=100, while preserving 1,368 local-neighbor edge visits and the same one-step outputs. This is equal quadratic population enumeration through a different index path, not a total-work reduction. The one-sweep timings remain small-fixture diagnostics, vary by size and process load, and are not an end-to-end speedup claim. This probe excludes commit/fixpoint behavior, full task quality, orientation selectivity, learning, and large-scale extrapolation. The anatomy builder caps this sweep at 10×10 units.

The evidence now says the cheap-cut hypothesis is workload-conditional: the conversation measurement has a reproducible small declared projection but nontrivial boundary, while this authored vision rule has dense cross-frame dependence. Neither fixture supplies a natural-task prevalence estimate. Next measure whether the full vision task requires the global factor, inspect factor-aware decomposition rather than spatial tile cuts, instrument adjacency traversal units, and compare task outcomes before considering a rule change.

## Reproduction artifacts

- [v1 preregistration](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_PREREG_20260927.md)
- [v1.1 size amendment](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_1_AMENDMENT_20260927.md)
- [v1.1 counter amendment](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_1_COUNTER_AMENDMENT_20260927.md)
- [v1.1 replication protocol](SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_1_PREREG_20260927.md)
- [runner](../../../scripts/substrate_vision_settle_single_sweep_scale_v1_1.py) and [independent analyzer](../../../scripts/analyze_substrate_vision_settle_single_sweep_scale_v1_1.py)
- [source lock](../../../evaluation/substrate_capability/vision_settle_single_sweep_scale_v1_1_lock_20260927.json)
- [raw capture](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_1_20260927.json) and [analysis](../../../evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_1_analysis_20260927.json)
