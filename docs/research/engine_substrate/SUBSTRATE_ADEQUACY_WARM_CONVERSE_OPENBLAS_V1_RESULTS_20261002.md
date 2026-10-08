# Warm converse uninstrumented OpenBLAS cap v1 — results

**Outcome: all 9/9 gates pass.** Six fresh source-locked workers use the exact same warm parity/missing-evidence route, Rayon stays at 24 workers in every process, and held-out predictions, codebook non-growth, refusal-state parity, CPU split reconciliation, and source fingerprints all pass. The only assigned intervention is `OPENBLAS_NUM_THREADS=1`; no profiler or interposer is loaded.

| OpenBLAS setting | Median wall | Range wall | Median process CPU | Range process CPU | Caller CPU | Other-thread CPU | Other-thread share |
|---|---:|---:|---:|---:|---:|---:|---:|
| Unset (library default) | 129.9 ms | 127.0–130.2 ms | 1,359.5 ms | 1,190.3–1,360.0 ms | 101.6 ms | 1,256.5 ms | 92.4% |
| `OPENBLAS_NUM_THREADS=1` | 103.8 ms | 99.9–107.4 ms | 101.8 ms | 100.2–103.3 ms | 97.1 ms | 4.4 ms | 4.4% |

The median aggregate process CPU falls **13.35×** with the cap, while caller-thread CPU changes only slightly. The target wall median is 20% lower. This uninstrumented intervention confirms that OpenBLAS configuration is the main cause of the earlier CPU/wall anomaly on this route. It also confirms the practical thread-creation cost: with BLAS capped, aggregate process CPU is approximately equal to wall time, while uncapped workers consume about 1.26 seconds of additional CPU per roughly 130 ms target interval.

The conclusion is deliberately narrow: one host, one authored target conversation, three repeats per setting. It establishes an actionable runtime configuration sensitivity, not a general capability or natural-task workload distribution. The separate thread-origin capture shows the OpenBLAS setting removes 23 OpenBLAS pthread creations while leaving 117 large-stack JSON parsing thread spawns unchanged. The next tractability experiment should reduce that per-call parser-thread churn, retaining deep-input safety and exact semantic parity, and then replicate the OpenBLAS intervention across more task families and a second host.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_WARM_CONVERSE_OPENBLAS_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_openblas_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_openblas_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_openblas_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_warm_converse_openblas_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_warm_converse_openblas_v1_analysis_20261002.json)
