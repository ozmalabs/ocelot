# Conversation matcher size and memory v1 results

Date: 2026-10-03  
Protocol: [size/memory preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_PREREG_20261003.md)  
Runner: [size/memory runner](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1.py)  
Locked analyzer: [original analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_size_memory_v1.py)  
Amended independent analyzer: [v1 amended analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_size_memory_v1_amended.py)  
Source lock: [locked inputs](../../../evaluation/substrate_capability/conversation_task_scope_size_memory_v1_lock_20261003.json)  
Capture: [45-worker gzip archive](../../../evaluation/reports/conversation_task_scope_size_memory_v1_20261003.json.gz)  
Analysis: [amended independent analysis](../../../evaluation/reports/conversation_task_scope_size_memory_v1_amended_analysis_20261003.json)

## Result

The locked run completed all 45 fresh workers: five decoy sizes × three scope orders × three replicates. Runner gates pass exact checkpoint/final graph equality against monolithic closure for both declared-anchor and verified fallback arms; goal statuses match; anchor trace-on/off states match; the anchor path is exercised; and fallback checkpoints have zero anchor attempts/rejections and positive full-fallback calls. The independent v1.1 analyzer passes after correcting its replicate-label expectation. The initial analyzer incorrectly expected replicate labels to restart at each size, while the runner numbers replicate blocks across the full schedule. The raw capture, original lock, and original analyzer are preserved. The 2.5 GB JSON capture is gzip-compressed with a verified round trip: uncompressed SHA-256 `ba9e260f2086dfec0d89379930b82127efe6bb8af025e7b9ef8f864a479bcb7e`. The compressed archive is about 32 MB. The amended analyzer independently decompresses it, verifies that content hash, and passes all gates.

| Shared-Event decoys | Median graph nodes | Median graph edges | Anchor Candidate pairs (9 runs) | Anchor / fallback | Anchor / monolithic | Anchor / fallback wall time | Anchor / monolithic wall time | Median worker peak RSS* |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 262 | 239 | 2,325 | 0.706× | 2.171× | 1.090× | 21.749× | 34 MiB |
| 256 | 519 | 1,008 | 278,877 | 0.667× | 2.721× | 0.971× | 7.460× | 68 MiB |
| 1,024 | 1,287 | 3,312 | 1,108,317 | 0.667× | 2.726× | 0.807× | 6.474× | 195 MiB |
| 4,096 | 4,359 | 12,528 | 4,426,077 | 0.667× | 2.727× | 0.840× | 6.719× | 661 MiB |
| 16,384 | 16,647 | 49,392 | 17,697,117 | 0.667× | 2.727× | 0.849× | 7.255× | 2,384 MiB |

At 16,384 decoys, anchor evaluates 70,788,810 Terms versus 106,180,443 for fallback and 25,955,892 for monolithic. Thus the anchor pruning retains a one-third work reduction against fallback, but its candidate and Term totals are both about 2.73× monolithic. Aggregate checkpoint wall time at this size is 19.79 s anchor, 23.31 s fallback, and 2.73 s monolithic. The v2.2 result's work reduction does not translate into a useful overall speedup over monolithic closure on this schedule.

## Memory and claim limits

`ru_maxrss` is the high-water RSS of the whole worker, which executes all arms and retains the returned checkpoint and trace payloads. The complete JSON capture is 2.5 GB. Consequently the table's RSS column is a harness/instrumentation ceiling, not a substrate-only or per-arm memory estimate; do not use it to claim linear or superlinear substrate memory complexity. Graph node/edge counts are recorded directly, but memory attribution remains open. The wall-time comparison also includes the scoped resweep/quiescence schedule and is specific to this authored task; timings are descriptive, not a general CPU benchmark.

Next create a lightweight memory probe that runs one arm per fresh process, disables trace capture, streams checkpoint summaries instead of retaining graph payloads, and samples peak RSS at matched graph states. Then repeat the high-degree scaling with natural task graphs and independently established ownership labels. This synthetic result establishes linear construction growth in decoy count and near-proportional matcher work for the tested schedule; it does not establish natural cheap-cut prevalence or general tractability.


## Follow-up correction

The RSS figures in this v1 report are withdrawn as substrate-memory evidence: the parent retained earlier results and child workers inherited those pages, in addition to trace and checkpoint serialization overhead. The v1.1 protocol reran the complete schedule with tracing disabled, compact summaries, and per-size fresh workers; see [v1.1 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_1_RESULTS_20261003.md). V1 work counters, graph-size records, wall times, and semantic parity remain valid.
