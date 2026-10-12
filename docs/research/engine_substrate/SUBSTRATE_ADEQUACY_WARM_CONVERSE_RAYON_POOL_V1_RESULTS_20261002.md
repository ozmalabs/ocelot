# Warm converse Rayon-pool diagnostic v1 — results

**Outcome: 9/9 gates pass.** Six fresh locked workers confirm the active global Rayon pool is 24 workers by default and 1 under `RAYON_NUM_THREADS=1`. Exact missing-evidence refusal, held-out predictions, source fingerprints, and unique-process gates pass.

| Setting | Rayon workers | OS threads after warm-up/pool query | OS threads after target | Peak sampled OS threads | Target wall median | Aggregate process CPU median |
|---|---:|---:|---:|---:|---:|---:|
| Default | 24 | 25 | 48 | 49 | 107.7 ms | 1,664.2 ms |
| `RAYON_NUM_THREADS=1` | 1 | 2 | 25 | 26 | 111.5 ms | 1,675.7 ms |

The target route adds 23 observed OS threads in both settings, while the known Rayon pool contributes 24 versus 1. The pool cap therefore works, but most target CPU and the added threads are independent of that pool setting. Thread totals do not name the pool or identify CPU use. A companion [caller-thread split](SUBSTRATE_ADEQUACY_WARM_CONVERSE_CALLER_CPU_V1_RESULTS_20261002.md) finds 94.8% median process CPU outside the calling thread in both arms.

See the [preregistration](SUBSTRATE_ADEQUACY_WARM_CONVERSE_RAYON_POOL_V1_PREREG_20261002.md), [runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1.py), [analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_rayon_pool_v1.py), [source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_rayon_pool_v1_lock_20261002.json), [capture](../../../evaluation/reports/substrate_adequacy_warm_converse_rayon_pool_v1_raw_20261002.json), and [analysis](../../../evaluation/reports/substrate_adequacy_warm_converse_rayon_pool_v1_analysis_20261002.json).
