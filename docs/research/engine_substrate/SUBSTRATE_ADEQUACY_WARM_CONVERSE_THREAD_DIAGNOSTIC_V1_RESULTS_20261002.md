# Warm converse thread-limit diagnostic v1 — results

**Outcome: 8/8 gates pass.** Six fresh source-locked parity/missing-evidence workers completed with unique PIDs, exact held-out predictions, no codebook growth, and stable worker/native fingerprints. The protocol and runner are [here](SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_DIAGNOSTIC_V1_PREREG_20261002.md) and [here](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_diagnostic_v1.py); the independent [analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_diagnostic_v1.py) validates the compact [capture](../../../evaluation/reports/substrate_adequacy_warm_converse_thread_diagnostic_v1_raw_20261002.json) against its [source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_diagnostic_v1_lock_20261002.json).

| Setting | n | Target wall median (range) | Aggregate process CPU median (range) | CPU/wall median | Maximum sampled OS threads, median |
|---|---:|---:|---:|---:|---:|
| Default Rayon setting | 3 | 112.1 ms (110.7–114.2) | 1,471.7 ms (1,189.3–1,520.3) | 13.29× | 25 |
| `RAYON_NUM_THREADS=1` | 3 | 114.0 ms (109.5–114.6) | 1,653.4 ms (1,596.3–1,667.3) | 14.55× | 25 |

The setting did not reduce the observed process thread count or target wall time in this small run. Process CPU remained 13–15× wall time in every worker. This does **not** prove the Rayon limit was ignored: total OS threads include non-Rayon pools, `/proc` sampling can miss short-lived threads, and the process CPU measurement combines all threads. The sample is too small and variable to claim a treatment effect or assign the CPU cost to matching. It narrows the next experiment: expose `rayon::current_num_threads()` from the active native runtime and capture per-thread CPU deltas (or native per-rule worker counters) over the target call, then repeat with exact process and pool controls.

## Limits

This is one task, one host, three workers per arm. The existing route performs lazy turn-state initialization beyond the initial warm-up; only the target-call CPU/wall comparison is at issue here. No source was changed for the workers, and the existing warm-route protocol-order amendment remains applicable. The capture estimates neither natural-request cost nor engine-wide thread behavior.
