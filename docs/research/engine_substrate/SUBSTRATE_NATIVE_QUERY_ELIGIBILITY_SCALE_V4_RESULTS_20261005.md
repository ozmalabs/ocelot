# Native query-eligibility scaling v4 results

## Result

The current-build scale capture passes all eight runtime gates over 25 workers. Independent analysis passes all eight checks, including current source/build provenance and exact seed-based eligible-set digest and selected-node replay. This is the source-current reference after the repeated-variable incremental matcher correction.

| Probe examples | Eligibility median / p90 | Argmin selection median / p90 | Graph build median | Worker CPU median | Peak RSS median |
|---:|---:|---:|---:|---:|---:|
| 512 | 0.82 / 1.00 ms | 0.107 / 0.138 ms | 2.99 ms | 56.58 ms | 35.0 MiB |
| 1,024 | 1.27 / 1.49 ms | 0.109 / 0.114 ms | 6.18 ms | 58.88 ms | 35.2 MiB |
| 2,048 | 2.46 / 4.25 ms | 0.189 / 0.328 ms | 12.17 ms | 64.63 ms | 36.7 MiB |
| 4,096 | 5.29 / 8.54 ms | 0.356 / 0.582 ms | 30.91 ms | 92.93 ms | 38.5 MiB |
| 8,192 | 10.34 / 12.00 ms | 0.677 / 1.108 ms | 56.05 ms | 131.35 ms | 42.7 MiB |

The v4 16× population range raises eligibility closure about 12.6×; selection rises about 6.3×. Graph construction rises about 18.8× and is the largest of the separately measured build, eligibility, and selector phases at 8,192 probes. The earlier v3 capture measured 15.59 ms eligibility at 8,192, versus 10.34 ms here, but the captures were run separately. The repeated-variable correction is not claimed to explain that difference. Keep the v4 values as the current baseline and collect paired counterbalanced repetitions before interpreting small timing shifts.

## Interpretation and next gate

The optimized fully bound membership path remains fast with exact eligibility and selection parity on this synthetic rule. At this scale, graph construction is the largest separately measured phase; this points to API call and graph-build cost as the next local performance question. It does not establish natural-task scaling, general locality, or large-graph substrate performance.

Next use counterbalanced A/B repetitions for any construction optimization, while retaining semantic parity and separate build/closure measurements. Extend to representative graph topology and actual task traces before extrapolating beyond this authored route.

## Evidence

See the [v4 protocol](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V4_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_query_eligibility_scale_v4.py), [source lock](../../../evaluation/substrate_capability/native_query_eligibility_scale_v4_lock_20261005.json), [raw capture](../../../evaluation/reports/native_query_eligibility_scale_v4_20261005.json), and [independent analysis](../../../evaluation/reports/native_query_eligibility_scale_v4_analysis_20261005.json). Compare the [v3 scale results](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V3_RESULTS_20261005.md) and [matcher v3 differential](SUBSTRATE_BOUND_EDGE_MATCHER_DIFFERENTIAL_V3_RESULTS_20261005.md).
