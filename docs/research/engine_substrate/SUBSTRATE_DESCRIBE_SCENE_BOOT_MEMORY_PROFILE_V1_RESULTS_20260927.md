# Describe-scene boot and request memory profile v1 results (2026-09-27)

## Phase results

The one-worker profile passes all seven gates and keeps the source lock stable. Resident memory is nearly unchanged by adapter construction, rises sharply during seed boot, barely changes on scene attachment, and falls after the completed request schedule despite reaching a higher transient process high-water mark:

| Phase | Current RSS | Anonymous RSS | Process high-water RSS |
|---|---:|---:|---:|
| Interpreter, before adapter | 0.037 GiB | 0.025 GiB | 0.128 GiB |
| Adapter constructed | 0.039 GiB | 0.025 GiB | 0.128 GiB |
| Full seed boot | 1.342 GiB | 1.320 GiB | 1.673 GiB |
| Scene attached | 1.344 GiB | 1.320 GiB | 1.673 GiB |
| Two requests completed | 0.352 GiB | 0.315 GiB | 2.508 GiB |

The 2.508 GiB process peak is independently consistent with the GNU `time -v` cross-check (2,630,800 KiB). Seed boot is the main source of the resident footprint, while the request schedule produces a larger transient peak and then returns current RSS to about 0.35 GiB. This is a phase association, not ownership attribution: the profile does not identify which seed, native/Python structure, allocator, or cleanup step causes either change.

## Correction to the repeated timing interpretation

The v2 timing runner's field named `rss_after_boot_bytes` was computed using `resource.getrusage(...).ru_maxrss`, which is a process high-water value, not current RSS. Its median 1.673 GiB must be called **high-water RSS observed by the end of boot**, not resident RSS remaining after boot. The current-RSS value after boot is 1.342 GiB in this phase profile. After both requests, current RSS is 0.352 GiB, even though peak RSS reached 2.508 GiB during the workload. The evidence does not support a persistent “memory floor.”

The repeated five-process peak distribution remains valid; only the label/interpretation of its boot-phase `ru_maxrss` field is corrected. The phase profile has one process, so its point estimates need replication before being treated as stable phase distributions.

## Artifacts

- [preregistration](SUBSTRATE_DESCRIBE_SCENE_BOOT_MEMORY_PROFILE_V1_PREREG_20260927.md)
- [runner](../../../scripts/substrate_describe_scene_boot_memory_profile_v1.py)
- [lock](../../../evaluation/substrate_capability/describe_scene_boot_memory_profile_v1_lock_20260927.json)
- [phase report](../../../evaluation/reports/describe_scene_boot_memory_profile_v1_20260927.json)
- [independent phase analysis](../../../evaluation/reports/describe_scene_boot_memory_profile_v1_analysis_20260927.json)
- [five-worker timing analysis](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_analysis_20260927.json)
- [OS peak-RSS cross-check](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_os_rss_crosscheck_20260927.json)
