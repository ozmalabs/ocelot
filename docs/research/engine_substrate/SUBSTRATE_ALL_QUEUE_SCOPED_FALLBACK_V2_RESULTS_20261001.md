# Scoped/full closure parity with distinct writes and dependent rules v2 results

Date: 2026-10-01

## Outcome

The preregistered **exact graph-wire parity** gate fails in 18 of 27 workers, all with `R=8` or `R=32`. The analysis passes 282/300 checks. The failures are not missing facts: a post-hoc state-order analysis finds identical node arrays and identical edge-fact multisets in all 27 workers. Exact edge insertion order matches in 9/27; the other 18 have the same final facts in a different edge order. This distinction is retained rather than normalizing away the preregistered failure.

The new rule interaction itself settles as expected. Every worker creates and verifies exactly `R×M` distinct per-binding edges, then reaches the same `R` target edges, framebuffer population, and five-family queue totals in both settled arms. Scoped-only completes graph-local verifier work (`R×M` verified edges) while correctly reporting deferred queue effects pending; global fallback drains those effects and reaches fixed point.

For `M=4` and `M=16`, the relative order of the `handled_mid` edge family is preserved even though the complete edge list interleaves the newly generated `verified_by` edges differently. At `M=1`, the `handled_mid` family itself is ordered differently in all six `R>1` worker cells (3 replicates each for R=8 and R=32). Edge iteration order could affect downstream matching or first-match consumers. The current probe does not measure such an order-sensitive continuation, so canonical fact equality is not upgraded to general semantic equivalence.

## Evidence and artifacts

- [Preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V2_PREREG_20261001.md)
- [Runner](../../../scripts/substrate_all_queue_scoped_fallback_v2.py)
- [Strict analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v2.py) — reports 282/300 because the exact wire-order gate fails.
- [Post-hoc state/order analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v2_state_order.py) — reports identical node arrays and edge-fact multisets in 27/27, exact wire equality in 9/27, and identical handled-edge subsequence order in 21/27.
- [Source/native lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v2_lock_20261001.json)
- [Raw workers](../../../evaluation/reports/all_queue_scoped_fallback_v2_workers_20261001.json)
- [Strict analysis](../../../evaluation/reports/all_queue_scoped_fallback_v2_analysis_20261001.json)
- [State/order analysis](../../../evaluation/reports/all_queue_scoped_fallback_v2_state_order_20261001.json)

All worker fingerprints are stable across execution. The strict result is preserved as a failed preregistered gate; the state/order report is explicitly post hoc.

## Next gate

Construct an order-sensitive continuation over the final graph that consumes the affected edge family and produces an externally visible result (for example, a first-match selection recorded in a node attribute). Run it against full and scoped-plus-fallback branches without sorting or normalizing edges. This will distinguish harmless serialization order from operationally observable state. Also test binding sets whose earlier writes change whether later snapshotted bindings remain valid, because v1.1 aligned the drain fold but did not establish that interaction.

The claim remains limited to one synthetic join and one direct-owner scope. It establishes distinct-write and dependent-rule fact coverage, not arbitrary scheduler equivalence, natural-task prevalence, or a complexity bound.
