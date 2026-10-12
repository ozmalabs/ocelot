# Uninstrumented describe-scene timing replication v2 results (2026-09-27)

## Gates and source identity

All seven gates pass across five fresh worker processes: unique PIDs, stable source locks at worker and parent boundaries, successful joins, two expected replies per worker, and one resolved request-bound Goal with selection/execution/action-result events for each inbound. The exact source closure, native extension, and build manifest match the passing v2.4 trace capture. The timed calls use no access trace, per-rule audit, measurement lock proxy, selection barrier, or graph readback.

## Measured envelope

| Measure | Median | Range across 5 workers |
|---|---:|---:|
| Seed boot wall time | 12.284 s | 11.950–13.246 s |
| Seed boot process CPU | 13.248 s | 12.984–14.186 s |
| Higher-CPU request thread | 11.108 s | 10.676–12.175 s |
| Lower-CPU request thread | 0.278 s | 0.262–0.292 s |
| Combined caller thread CPU for two-call schedule | 11.370 s | 10.961–12.467 s |
| Maximum caller wall interval | 11.463 s | 11.069–12.631 s |
| Boot-phase process high-water RSS | 1.673 GiB | 1.673–1.674 GiB |
| Process peak RSS | 2.508 GiB | 2.508–2.509 GiB |

The A/B label receiving the high-CPU request changes between replicates. Reporting fixed-label CPU medians would therefore be misleading; results are sorted by CPU role. Both caller wall intervals are about 11–12 seconds because a waiting caller includes its wait. The runner does not record an independent outer batch timer, so `maximum caller wall interval` is only a close workload-duration proxy, not a separately measured schedule wall time. These numbers describe two concurrent calls on one adapter and should not be read as isolated per-request service times.

The `resource.getrusage(RUSAGE_SELF)` peak-RSS value is independently corroborated by GNU `/usr/bin/time -v` on a sixth fresh worker: both report 2,630,800 KiB. That worker used 22.14 s user CPU, 3.47 s system CPU, 24.35 s elapsed wall time, and zero major page faults. This validates the RSS measurement method; it does not add another member to the five-worker distribution.

## Interpretation and limits

The full-seed process reaches 1.67 GiB *high-water RSS* during boot and 2.51 GiB peak while handling only two requests on a 25,201-node final graph. A separate phase profile measures current RSS as 1.342 GiB after boot but only 0.352 GiB after both requests, so the evidence supports a large boot-associated footprint and transient request peak, not a persistent memory floor. Neither capture attributes memory to seed objects, graph state, allocator behavior, or native structures; nor do they imply a reduced profile or incremental process would have the same footprint. See the [phase profile and correction](SUBSTRATE_DESCRIBE_SCENE_BOOT_MEMORY_PROFILE_V1_RESULTS_20260927.md).

The stable five-worker envelope strengthens the current-source fixture evidence, but a single task family and one graph size cannot establish tractability on natural-task distributions or 10⁷–10⁸ nodes. Next attribute memory by seed/graph components, add an outer schedule timer, replicate phase sampling, repeat with a minimal profile, then run a controlled graph-size/rule-count sweep and independent task families.

## Artifacts

- [preregistration](SUBSTRATE_DESCRIBE_SCENE_UNINSTRUMENTED_TIMED_REPLICATION_V2_PREREG_20260927.md)
- [runner](../../../scripts/substrate_describe_scene_uninstrumented_timing_v2.py)
- [independent analyzer](../../../scripts/analyze_substrate_describe_scene_uninstrumented_timing_v2.py)
- [analysis](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_analysis_20260927.json)
- [raw five-worker report](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_20260927.json)
- [OS RSS cross-check](../../../evaluation/reports/describe_scene_uninstrumented_timing_v2_os_rss_crosscheck_20260927.json)
