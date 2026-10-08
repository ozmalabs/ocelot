# Shape-decoding rehearsal phase profile v1 — results

**Result:** 6/6 gates pass across six fresh processes. All runs apply the positive `dedup_identity_fix`, converge, and preserve the primary. Source and native binary fingerprints match the pre-run lock. Values below are medians across three runs per backend; timings are instrumented.

| Backend | Total ms | Snapshot/setup ms | Candidate patch ms | Model-after prediction ms | Bounded forward look ms | Structural scan ms |
|---|---:|---:|---:|---:|---:|---:|
| `native_full_copy_scoped` | 219.1 | 37.9 | 18.7 | 162.9 | 148.9 | 14.0 |
| `native_shared_graph_pages_scoped` | 99.7 | 10.2 | 20.1 | 68.1 | 51.0 | 15.2 |

Shared pages reduce measured snapshot/setup from 37.9 to 10.2 ms and model-after prediction from 162.9 to 68.1 ms in this fixture. The bounded forward look is the largest subphase of model-after prediction (149.0 ms full-copy; 51.0 ms shared pages). Candidate patching remains about 19–20 ms. These phase timings explain where the single-rehearsal CoW savings occur, but do not identify the cause of the threaded slowdown: this probe is sequential and instrumentation can affect timings. A concurrent phase-contention measurement remains necessary.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_SHAPE_DECODING_PHASE_PROFILE_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_phase_profile_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_shape_decoding_phase_profile_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_shape_decoding_phase_profile_v1_raw_20261001.json)
- [Parallel wave motivating this profile](THOUGHTEXPERIMENT_SHAPE_DECODING_PARALLEL_WAVE_V1_RESULTS_20261001.md)
