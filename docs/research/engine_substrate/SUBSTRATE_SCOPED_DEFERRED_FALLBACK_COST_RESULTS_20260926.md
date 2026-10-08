# Scoped deferred-effect fallback cost — 2026-09-26

## Result

The amended v1.1 cost sweep passed all nine analysis gates across 120 fresh workers: 1/2/4/8/16 TrackIdentity pairs (2/4/8/16/32 frame owners), 12 repeats, and ordinary-full versus scoped-then-global-fallback arms. Final identity projections match in all 60 paired cells. Scoped fallback always reports its expected one-step budget exit and pending queue; both arms reach fixed point, and the terminal full-closure probe makes zero progress.

| Frame owners | Full closure median | Scoped + global fallback median | Paired wall ratio median (range) |
|---:|---:|---:|---:|
| 2 | 0.082 ms | 0.104 ms | 1.24× (0.81–1.73) |
| 4 | 0.084 ms | 0.103 ms | 1.23× (0.86–1.43) |
| 8 | 0.085 ms | 0.100 ms | 1.18× (0.95–1.52) |
| 16 | 0.088 ms | 0.104 ms | 1.23× (0.86–1.40) |
| 32 | 0.089 ms | 0.109 ms | 1.20× (0.89–1.47) |

The median incremental wall cost is roughly 0.015–0.023 ms. Paired CPU ratios are similar (about 1.19–1.29×). Per-cell paired ranges are broad and include ratios below one, so the relative overhead is not precisely resolved at these sub-millisecond latencies. Graph setup is 0.43–0.59 ms median and is excluded from settlement; worker elapsed is about 56–58 ms, dominated by fresh interpreter/import overhead. Peak process RSS is about 24 MiB, likewise an import-floor measure. No engine work counters beyond closure progress are present in this capture.

## Interpretation and limits

On this fixture, fallback adds a small absolute cost and a noisy ~20% median settlement premium through 32 frame owners. The effect is affordable for this measured synthetic case; it does not establish affordability at useful substrate scale. Work is too short for a stable relative-time conclusion, setup/startup dominate worker time, and the TrackIdentity search shape is fixed. Other deferred queues, natural workloads, detailed CPU operation counts, and larger structures remain unmeasured. The result motivates instrumented work attribution and additional queue families before any general fallback-economics claim.

## Reproducibility

- Protocol and v1.1 amendment: [`SUBSTRATE_SCOPED_DEFERRED_FALLBACK_COST_PREREG_20260926.md`](SUBSTRATE_SCOPED_DEFERRED_FALLBACK_COST_PREREG_20260926.md)
- Runner: [`substrate_scoped_deferred_fallback_cost_v1.py`](../../../scripts/substrate_scoped_deferred_fallback_cost_v1.py)
- Independent analyzer: [`analyze_substrate_scoped_deferred_fallback_cost_v1.py`](../../../scripts/analyze_substrate_scoped_deferred_fallback_cost_v1.py)
- Initial v1 capture and failed overstrict analysis retained: [raw](../../../evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_20260926.json), [analysis](../../../evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_analysis_20260926.json)
- Accepted v1.1 lock: [`scoped_deferred_fallback_cost_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/scoped_deferred_fallback_cost_v1_1_lock_20260926.json)
- Accepted raw capture: [`substrate_scoped_deferred_fallback_cost_v1_1_20260926.json`](../../../evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_1_20260926.json)
- Independent analysis: [`substrate_scoped_deferred_fallback_cost_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_scoped_deferred_fallback_cost_v1_1_analysis_20260926.json)

The initial failed gate required positive progress from the global drain even though that call can drain pending work at its opening boundary and settle with zero progress. V1.1 corrects the gate while preserving the same arms and measures; the amended hashes match in the accepted analysis.
