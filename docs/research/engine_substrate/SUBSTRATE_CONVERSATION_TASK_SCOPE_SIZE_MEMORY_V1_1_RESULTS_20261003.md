# Conversation matcher size and memory v1.1 results

Date: 2026-10-03  
Protocol amendment: [memory isolation amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_1_AMENDMENT_20261003.md)  
Runner: [compact fresh-worker runner](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1_1.py)  
Analyzer: [independent v1.1 analysis](../../../evaluation/substrate_capability/analyze_conversation_task_scope_size_memory_v1_1.py)  
Source lock: [v1.1 locked inputs](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1_1_lock_20261003.json)  
Capture: [45-worker compact capture](../../../evaluation/reports/conversation_task_scope_size_memory_v1_1_20261003.json)  
Analysis: [independent analysis JSON](../../../evaluation/reports/conversation_task_scope_size_memory_v1_1_analysis_20261003.json)  
Prior v1 memory-contaminated capture: [compressed raw capture](../../../evaluation/reports/conversation_task_scope_size_memory_v1_20261003.json.gz); corrected v1 analysis: [amended analysis JSON](../../../evaluation/reports/conversation_task_scope_size_memory_v1_amended_analysis_20261003.json)

## Result

The 45-worker run covers five shared-Event decoy counts (0, 256, 1,024, 4,096, 16,384), three scope orders, and three replicates. Independent analysis passes the source lock, worker uniqueness and assignment, exact checkpoint/final graph parity against monolithic closure, lifecycle equality, anchor-path coverage, and verified fallback isolation. The v1.1 workers disable tracing, compact and release each arm's full results before proceeding, and emit only checkpoint digests and summary counters. Their captures total about 1.5 MB rather than 2.5 GB.

| Decoys | Median nodes / edges | Worker peak RSS | Anchor Candidate ratio vs fallback | Anchor Candidate ratio vs monolithic | Anchor wall time vs fallback | Anchor wall time vs monolithic |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 262 / 239 | 32.6 MiB | 0.706× | 2.171× | 1.054× | 16.31× |
| 256 | 519 / 1,008 | 35.6 MiB | 0.667× | 2.721× | 0.849× | 6.83× |
| 1,024 | 1,287 / 3,312 | 44.6 MiB | 0.667× | 2.726× | 0.776× | 6.51× |
| 4,096 | 4,359 / 12,528 | 80.4 MiB | 0.667× | 2.727× | 0.825× | 6.40× |
| 16,384 | 16,647 / 49,392 | 222.1 MiB | 0.667× | 2.727× | 0.810× | 6.61× |

At the largest size, anchor closure totals 17.70M Candidate pairs and 70.79M Term evaluations, versus 26.55M/106.18M for fallback and 6.49M/25.96M for monolithic. Its aggregate wall time is 18.46 s, compared with 22.80 s fallback and 2.79 s monolithic. Therefore anchor cuts about one-third of fallback work and runs about 19% faster than fallback at this size, while remaining 2.73× higher in both work counters and 6.61× slower than monolithic closure.

## Memory interpretation and next gate

With tracing disabled and compact summaries, median whole-worker high-water RSS rises from 32.6 MiB at zero decoys to 222.1 MiB at 16,384. Across nonzero sizes the increase is close to linear, around 11.8 KiB per added decoy for this Python/native runtime, graph representation, and three-arm schedule. This is an end-to-end process measure; it does not separate graph storage from indexes, runtime structures, or temporary matcher allocations, and should not be generalized beyond this fixture.

The v1 run's RSS numbers are withdrawn: its parent retained prior worker captures and forked subsequent workers inherited those pages; trace data and full checkpoint payloads also inflated the 2.5 GB capture. Its graph/work/timing/parity results remain intact. The first v1 analyzer also had a replicate-label validator error, corrected in an independently hashed amended analysis. Both corrections and original artifacts are preserved.

Next measure each arm in its own fresh process to separate the monolithic/fallback/anchor memory curves. Then evaluate independently labeled ownership on naturally harvested task graphs. This synthetic sweep establishes neither cheap-cut prevalence nor general tractability.
