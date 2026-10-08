# Warm converse external per-thread CPU diagnostic v2 — results

**Outcome: 8/9 preregistered gates pass.** The six-worker capture is source-locked, has unique child PIDs, exact prediction/refusal controls, observes Rayon at 24 workers by default and 1 when capped, and stays within the sampled-CPU reconciliation bound. The sampling-quality gate fails: all capped-Rayon runs reach the 20-sample minimum, but the three default-Rayon runs record 14, 18, and 15 samples.

| Setting | Median target wall | Median process CPU | Median caller CPU | Median parent samples | Median sampled thread CPU | Median thread instances |
|---|---:|---:|---:|---:|---:|---:|
| Default Rayon (24) | 137.1 ms | 1,242.4 ms | 100.8 ms | 15 | 1,022.2 ms (86.2%) | 48 |
| Rayon capped at 1 | 136.2 ms | 1,201.0 ms | 102.5 ms | 25 | 1,116.9 ms (93.0%) | 25 |

The parent-process sample supports the earlier conclusion that most process CPU accrues outside the caller. It observes 25 distinct OS thread instances in the capped-Rayon calls and 48 in the default calls. These are identities seen across interval samples, not a simultaneous-thread count; they cannot establish an extra pool or separate Rayon from other sources. The sample does not identify code ownership; `/proc` `comm` is the generic `python` label. The failed default-arm sample gate limits per-thread distribution claims, and CPU-share figures are sampled estimates rather than exact accounting.

Do not attribute these thread instances to the cognitive-task executor, Rayon, or a Python pool yet. Next repeat the thread-creation probe under a source lock, also intercept `_thread.start_new_thread`, then inspect native thread-spawn sites on the live route. If OS workers remain unexplained, add narrowly scoped Rust task/rule counters before changing scheduler capacity.

## Follow-up probe (exploratory, one capped-Rayon worker)

A separate instrumented run wrapped `threading.Thread.start` during the target `converse` and captured `threading.enumerate()` at both boundaries. It observed no Python `Thread.start` calls and only `MainThread` before and after, while the corresponding external-sampler panel observes 25 distinct OS thread instances in the capped-Rayon setting. This narrows the likely producer away from the standard Python `threading.Thread` API, but it is one exploratory process and does not exclude `_thread`, C-extension, Rust, or threads created outside the marked interval. It is not a preregistered gate and does not attribute the OS threads.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_WARM_CONVERSE_THREAD_CPU_V2_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_warm_converse_thread_cpu_v2.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_warm_converse_thread_cpu_v2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v2_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_warm_converse_thread_cpu_v2_analysis_20261002.json)
