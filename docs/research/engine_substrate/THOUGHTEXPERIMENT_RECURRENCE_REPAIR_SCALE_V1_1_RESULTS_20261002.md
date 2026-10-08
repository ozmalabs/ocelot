# Thoughtexperiment recurrence repair scale v1.1 results

All six fresh-process workers pass the locked gates at 1,000,000 unrelated nodes. Full-copy and shared-page branches each restore the exact authored `mrl_offer_due_once` guard, emit one offer, reach a zero-progress fixed point, and preserve primary graph counts, rule vector, and revision. Closure outcomes match across backends and all three paired repetitions. This is a controlled recurrence correction, not autonomous diagnosis or candidate invention.

## Memory and runtime

| Backend | Median sampled peak PSS increase | Median PSS after explicit branch release | Median rehearsal time | Median samples |
|---|---:|---:|---:|---:|
| Full copy | 360.0 MiB | 193.1 MiB | 677.8 ms | 38 |
| Shared graph pages | 19.3 MiB | 1.3 MiB | 19.5 ms | 5 |

The worker explicitly deletes both the branch wrapper and its inner native substrate before garbage collection and the post-release sample. Shared pages return close to baseline process PSS. Full-copy residency falls substantially from peak but remains about 193 MiB above baseline; at capture time, PSS alone did not distinguish live objects from allocator-retained pages; the later [allocator follow-up](THOUGHTEXPERIMENT_RECURRENCE_ALLOCATOR_RECLAMATION_V1_RESULTS_20261002.md) found that the full-copy residual matched free glibc arena pages. Shared-page operations finish quickly enough that the 10 ms sampler gathers only about five readings, so the measured peak may miss transients. Do not infer an exact 18.7× peak ratio from these samples.

Compared with the earlier same-task memory panel, peak PSS rises from 32.1/62.9 MiB at 100k/200k to 360.0 MiB at 1m under full copy, and from 2.7/4.1 MiB to 19.3 MiB under shared pages. Median time at 1m is 677.8 ms full copy and 19.5 ms shared pages; prior 100k/200k values were 56.2/108.2 ms and 5.0/6.1 ms. These are descriptive measurements from one host and one synthetic linked-noise topology. They do not support a complexity bound, concurrent throughput claim, or natural-task estimate.

V1's apparent post-drop samples were taken while its `bn = branch._inner` alias remained live. V1 is retained as valid branch-resident peak and semantic evidence; its post-drop field is not reclamation evidence. V1.1 corrects this lifetime flaw with a new lock and capture; see the [amendment](THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_1_AMENDMENT_20261002.md).

## Artifacts

The preserved v1 run remains auditable as branch-resident peak and semantic evidence: [v1 protocol](THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_PREREG_20261002.md), [v1 runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_repair_scale_v1.py), [v1 lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_lock_20261002.json), [v1 capture](../../../evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_20261002.json), and [v1 analysis](../../../evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_analysis_20261002.json).

- [Original preregistration](THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_PREREG_20261002.md)
- [V1.1 amendment](THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/measure_thoughtexperiment_recurrence_repair_scale_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_repair_scale_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_1_analysis_20261002.json)
