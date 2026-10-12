# Code-write acquisition controls v1 — results

The four-worker, source-locked panel completed with no worker errors and stable worker source fingerprints. Two fresh workers read the externally supplied parity function without teaching; both remained unable to compose the parity request and added zero code-write construction shapes. In two other fresh workers, the same parity source was taught with a clamp request. Both calls were accepted, both resulting shapes were selected for clamp, and both native Term and generated Python failed all 12 independent clamp cases: 0/24 exact in each route.

| Arm | Workers | Codebook result | Held-out oracle |
|---|---:|---|---:|
| Read only | 2 | No new construction; parity request still unsupported | Not applicable |
| Parity source taught as clamp | 2 | Accepted and selected for clamp in both | Native 0/24; Python 0/24 |

Median full-seed boot was 18.05 s and median peak RSS was about 1.81 GB. Median read-only intervention time was 7.31 ms; median mismatched teach time was 46.07 ms. These are four-process measurements from one host and should not be treated as stable service-cost estimates.

## Interpretation and limitation

This directly supports two narrow conclusions. Reading executable code does not itself grow this write codebook. The teaching path can attach a successfully parsed and internally write-validated Term to a request that it does not implement: teaching validates agreement between Term evaluation and emitted code at one sample, but does not establish semantic agreement with `request_text`. This is a demonstrated semantic admission gap for one deliberately mismatched pair, not an estimate of its frequency. The next capability gate should add an independent request/behavior check or uncertainty/refusal policy before durable codebook adoption, then evaluate aligned and mismatched examples across held-out families. Preserve provenance, false-admission rate, refusal rate, and total acquisition cost.

The first analyzer pass failed because of an incorrect field path. Its correction is disclosed in the [analysis amendment](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_ANALYSIS_AMENDMENT_20261001.md); raw worker data is unchanged and the original lock is preserved.

## Artifacts

- [Preregistration](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_PREREG_20261001.md)
- [Analysis amendment](SUBSTRATE_CODE_WRITE_ACQUISITION_CONTROLS_V1_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_code_write_acquisition_controls_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_code_write_acquisition_controls_v1.py)
- [Capture](../../../evaluation/reports/substrate_code_write_acquisition_controls_v1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_code_write_acquisition_controls_v1_analysis_20261001.json)
