# Shape-decoding Thoughtexperiment scale v1 — results

**Result:** 9/9 gates pass across 60 fresh processes. Every size/backend/mode cell preserves the positive `dedup_identity_fix` success and negative `add_match_guard(control)` failure. Exact branch signatures agree across backends and execution modes, primary state is unchanged, and source/native locks match.

| Unrelated nodes | Full-copy sequential / concurrent positive wave (ms) | Full-copy CPU/wall concurrent | Shared pages sequential / concurrent positive wave (ms) | Shared pages CPU/wall concurrent |
|---:|---:|---:|---:|---:|
| 0 | 280 / 360 | 1.12× | 294 / 361 | 1.06× |
| 10k | 424 / 417 | 1.46× | 288 / 420 | 1.00× |
| 50k | 873 / 581 | 2.29× | 319 / 416 | 1.02× |
| 100k | 1,532 / 900 | 2.49× | 317 / 423 | 1.09× |
| 200k | 2,784 / 1,573 | 2.74× | 385 / 465 | 1.07× |

Negative-candidate waves show the same structural pattern. Full-copy concurrent/sequential throughput improves as unrelated graph size grows: at 200k nodes the eight-branch concurrent wave is about 1.77× faster for the positive candidate and 1.99× for the negative candidate. At 0 nodes, concurrent scheduling overhead makes the wave slower. Shared graph pages have low size sensitivity, as expected from scoped branches, but concurrent waves remain slower than sequential at every tested size (positive concurrent/sequential ratios 0.69–0.83; negative 0.72–0.84), and CPU/wall stays about 1.00–1.09×.

The two backends therefore serve different measured regimes. At 200k unrelated nodes, shared pages remain substantially faster in absolute wave time (465 ms vs 1,573 ms concurrent; 385 ms vs 2,784 ms sequential), while full-copy derives much greater CPU overlap and gains more from concurrent batches as copy work grows. This is evidence of a scale-dependent throughput tradeoff on one graph family, not a universal backend ranking. The benchmark does not measure memory use, natural graph topology, candidate diversity beyond one positive/negative pair, or sizes above 200k.

Next extend candidate families and graph topology, sample branch memory at these sizes, and profile the remaining shared-page model-after prediction work. Keep the full-copy parallel path and shared-page low-latency path as distinct measured operating points.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_SCALE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_scale_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_scale_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_scale_v1_raw_20261001.json)
- [Native rule-store summary profile](THOUGHTEXPERIMENT_SHAPE_DECODING_PYTHON_NATIVE_PROFILE_V3_RESULTS_20261001.md)
