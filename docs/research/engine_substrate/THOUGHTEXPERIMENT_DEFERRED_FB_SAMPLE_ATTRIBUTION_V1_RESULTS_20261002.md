# Thoughtexperiment deferred framebuffer sample attribution v1 results

The three-worker source-locked panel passes all gates. Every worker reaches the same two-pass fixed point with one progress step in ordinary, attributed, and exact-snapshot reports. The rule-driven sample emits one successful `deferred=true` event from `look_when_frame_advances`; the resulting graph contains five WorldInstance nodes and two Region nodes. Event targets cover all exact changed nodes and edges, aggregate targets contain all event targets, and no events are dropped.

The fixture writes one fixed 8×8 BGRA frame and samples it to a 2×2 grid without a host `fb_sample` call. It establishes producer attribution and graph-delta coverage for this path, not moving-frame tracking quality, continuous ingestion throughput, multi-rule competition, or perception accuracy.

The implementation is source-linked at [`pending_fb_samples`](../../../runners/dsl/src/graph.rs), the [`Effect::FbSample` enqueue site](../../../runners/dsl/src/rewrite.rs), and [`apply_pending_fb_samples`](../../../runners/dsl/src/substrate.rs).

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_DEFERRED_FB_SAMPLE_ATTRIBUTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deferred_fb_sample_attribution_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_fb_sample_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_fb_sample_attribution_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_deferred_fb_sample_attribution_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_deferred_fb_sample_attribution_v1_analysis_20261002.json)
