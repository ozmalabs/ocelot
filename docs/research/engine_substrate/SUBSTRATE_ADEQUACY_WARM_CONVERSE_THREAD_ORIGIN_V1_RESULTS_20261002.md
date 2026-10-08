# Warm converse thread-origin diagnostic v1 — results

**Independent review outcome: 12/12 gates pass.** The raw panel contains 12 fresh source-locked workers across Rayon default/one-thread and OpenBLAS environment-unset/one-thread conditions. Held-out predictions, missing-evidence refusal, zero codebook growth, source/native fingerprints, event boundaries, pthread stack sizes, and the two interventions all pass. The original preregistered analyzer had a tooling/source-list defect and did not resolve native offsets; the separately hashed [review analyzer](../../../evaluation/substrate_capability/review_substrate_adequacy_warm_converse_thread_origin_v1.py) revalidates the complete pre-capture lock, rebuilds and hashes the interposer, and symbolizes the captured addresses with `addr2line`.

## Thread creation sources

With the default OpenBLAS configuration (environment unset), every target call creates 23 pthreads from NumPy's bundled `libscipy_openblas` `blas_thread_init`. With `OPENBLAS_NUM_THREADS=1`, these calls fall to zero. Independently, every target call creates 117 native JSON parser threads through `substrate_rs::py::pyobj_to_json`, each requesting a 256 MiB stack. Their symbolized PyO3 parent methods per call are:

| Parent method | Parser threads per target call |
|---|---:|
| `add_production` | 94 |
| `add_rule` | 16 |
| `graph_from_dict` | 6 |
| `import_rules` | 1 |

The 117 parser spawns are unchanged by either Rayon or OpenBLAS settings. The OpenBLAS thread pool initializes from its own `gotoblas_init` path; the Rayon worker setting does not control it. These call-site observations explain the earlier unnamed off-caller threads and show that the text route performs substantial lazy rule/production materialization and JSON conversion.

## CPU intervention signal

With backtrace interposition active, median aggregate process CPU is 1,239 ms (Rayon 24) and 1,335 ms (Rayon 1) when OpenBLAS is unrestricted, versus 125 ms and 110 ms with OpenBLAS capped at one. That is a 9.9× and 12.1× CPU ratio in this instrumented fixture. The 117 JSON parser spawns remain, isolating the large CPU difference to the OpenBLAS setting at the environment-intervention level. The follow-up uninstrumented, six-process comparison passes 9/9 gates and confirms the same route-specific effect: median process CPU is 1,359.5 ms uncapped versus 101.8 ms capped (13.35×), while median wall falls from 129.9 ms to 103.8 ms. This supports OpenBLAS as the main source of the earlier process-CPU/wall gap on this one host and task; it is not a general speedup estimate. The 117 per-call, 256 MiB-stack parser threads remain the next cost target. See [the uninstrumented result](SUBSTRATE_ADEQUACY_WARM_CONVERSE_OPENBLAS_V1_RESULTS_20261002.md); next benchmark a reusable stack-safe parser worker with exact semantic parity and repeat the BLAS comparison across another workload or host.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_ORIGIN_V1_PREREG_20261002.md)
- [C interposer](../../../evaluation/substrate_capability/thread_origin_pthread_probe.c)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1.py)
- [Original preregistered analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_origin_v1.py)
- [Corrected independent review analyzer](../../../evaluation/substrate_capability/review_substrate_adequacy_warm_converse_thread_origin_v1.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_origin_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_raw_20261002.json)
- [Corrected analysis](../../../evaluation/reports/substrate_adequacy_warm_converse_thread_origin_v1_analysis_review_20261002.json)

Timing columns in the analysis are instrumentation-affected. The source/call-site and exact-outcome gates, rather than those timings, are the primary result of this diagnostic.
