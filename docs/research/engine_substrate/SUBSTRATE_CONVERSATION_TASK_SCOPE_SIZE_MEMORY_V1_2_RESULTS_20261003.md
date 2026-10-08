# Conversation matcher per-arm size and memory v1.2 results

Date: 2026-10-03  
Protocol: [per-arm amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_2_AMENDMENT_20261003.md)  
Runner: [one-arm-per-worker runner](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1_2.py)  
Independent analyzer: [v1.2 analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_size_memory_v1_2.py)  
Source lock: [locked inputs](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1_2_lock_20261003.json)  
Capture: [135-worker compact capture](../../../evaluation/reports/conversation_task_scope_size_memory_v1_2_20261003.json)  
Analysis: [independent analysis](../../../evaluation/reports/conversation_task_scope_size_memory_v1_2_analysis_20261003.json)

## Result

All 135 workers ran in unique fresh processes: five decoy sizes × three frame orders × three replicates × three arms. Independent analysis passes the lock and schedule checks, exact checkpoint/final graph parity across monolithic, fallback, and anchor arms for all 45 matched cells, goal lifecycle parity, anchor-path exercise, and verified fallback isolation. Each worker ran one arm with trace capture disabled and emitted only compact checkpoint digests/counters.

| Decoys | Median nodes / edges | Monolithic RSS | Fallback RSS | Anchor RSS | Anchor / fallback wall time | Anchor / monolithic wall time |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 262 / 239 | 32.2 MiB | 32.1 MiB | 32.2 MiB | 0.950× | 20.01× |
| 256 | 519 / 1,008 | 34.6 MiB | 34.6 MiB | 34.7 MiB | 0.834× | 6.70× |
| 1,024 | 1,287 / 3,312 | 43.0 MiB | 42.8 MiB | 43.0 MiB | 0.834× | 6.78× |
| 4,096 | 4,359 / 12,528 | 74.0 MiB | 74.3 MiB | 74.6 MiB | 0.823× | 7.16× |
| 16,384 | 16,647 / 49,392 | 201.6 MiB | 202.0 MiB | 201.9 MiB | 0.830× | 7.11× |

At 16,384 decoys, anchor uses 17.70M Candidate pairs and 70.79M Term evaluations, versus 26.55M/106.18M in fallback and 6.49M/25.96M in monolithic closure. Aggregate checkpoint wall time is 20.17 s anchor, 24.29 s fallback, and 2.84 s monolithic. Anchor reduces matcher work by one-third versus fallback and runs about 17% faster, but remains 2.73× higher in both counters and 7.11× slower than monolithic closure.

## Memory interpretation

Fresh-process median peak RSS rises with the constructed graph from about 32 MiB at zero decoys to about 202 MiB at 16,384. The three arms' medians differ by at most 0.62 MiB across sizes; at the largest size the anchor median is 0.08% below fallback and 0.12% above monolithic. This indicates that input graph construction/runtime footprint dominates any arm-specific memory difference on this schedule. The increase is approximately 10.6 KiB per added decoy between the endpoints, but this is an end-to-end Python/native process estimate that includes graph materialization, runtime/index structures, and temporary closure state. It does not isolate native graph storage or explain which structures account for the increase.

The v1 RSS series is withdrawn due parent-retained payloads inherited by forked children and trace/checkpoint output. V1.1 fixed parent retention and tracing but still combined three arms in each process; v1.2 supersedes its arm-memory estimate with matched one-arm-per-process measurements. Both earlier captures remain documented, and the 2.5 GB v1 raw capture is preserved as a verified gzip archive.

Next move from synthetic decoys to naturally harvested task graphs with independently reviewed ownership labels, while keeping the same per-arm process isolation and parity gates. Report the observed distribution and coverage failures; do not infer that these authored cheap cuts represent natural workloads.
