# GenInfer shared-codebook versus frame-isolated comparison v1.1 (2026-10-03)

## Result

The source-locked paired comparison passes all gates. It combines the prior
shared-codebook capture (15 K/repeat groups) with 93 fresh-process isolated
frame closures. All **93/93** isolated outputs and **93/93** matching shared
outputs settle through the expected transform path and match their exact
matrix oracle. Each isolated graph contains one eligible shape part and one
observation. The native binary matches the shared baseline.

Median native closure wall time, summing the K isolated one-frame closures,
compares with one closure over K frame-tagged parts and observations:

| Frames K | Shared closure | Isolated total | Shared / isolated |
|---:|---:|---:|---:|
| 1 | 10.06 ms | 10.74 ms | 0.95× |
| 2 | 27.40 ms | 21.13 ms | 1.28× |
| 4 | 82.30 ms | 40.71 ms | 2.02× |
| 8 | 282.35 ms | 84.48 ms | 3.34× |
| 16 | 1,052.92 ms | 164.15 ms | 6.42× |

The direct diagnostic queried `GenInfer.checked` before closure. With K parts
and K observations, the shared graph reports K²×2,400 candidate checks
(614,400 at K=16). The isolated total is K×2,400 (38,400 at K=16). These are
pre-closure candidate-volume diagnostics; production closure can reuse newly
minted generators, so they are not an instrumented count of every production
Term invocation. Even with that reuse, the measured shared closure cost grows
more quickly than the isolated closure sum as K increases.

## Interpretation and limits

This shows a concrete cost opportunity for frame locality: keeping each
four-relation task in a separate codebook avoids unrelated eligible parts in
the GenInfer candidate loop. At K=16, isolated closure sums are about 6.4×
cheaper than one shared graph closure on this workload. The engine path tested
here accepts `frame_id` tags but does not use them to restrict the codebook
scan; the isolated condition is achieved with independent full-seed graphs,
not a production frame scheduler. The timed totals exclude boot, process
startup, data construction, scheduling, and result aggregation. Therefore
this is not an end-to-end speedup or proof that discovering and maintaining
frames is economical. It identifies a measurable missing boundary between
the cheap-cut hypothesis and current GenInfer execution.

The next gate should implement a source-explicit frame/codebook scope for
GenInfer and compare shared-scope versus scoped execution on the same locked
multi-frame tasks. It must retain exact results and report scope-selection,
graph-maintenance, and scheduler overhead alongside closure savings. If frame
boundaries are not available from actual task structure, the system should
not be credited with the isolated upper-bound result.

## Artifacts

- [Protocol](SUBSTRATE_GENINFER_FRAME_ISOLATION_COMPARISON_V1_1_PREREG_20261003.md)
- [Runner](../../../evaluation/substrate_capability/substrate_geninfer_frame_isolation_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_geninfer_frame_isolation_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/geninfer_frame_isolation_v1_1_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/geninfer_frame_isolation_v1_1_20261003.json)
- [Analysis](../../../evaluation/reports/geninfer_frame_isolation_v1_1_analysis_20261003.json)
