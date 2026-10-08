# Size/memory v1.1 amendment: isolate worker memory and stream summaries

Date: 2026-10-03  
Status: amendment written after v1 capture and analysis, before v1.1 implementation/capture.  
Prior record: [v1 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_SIZE_MEMORY_V1_RESULTS_20261003.md)

## Reason

The v1 size/work capture passes parity, but its `ru_maxrss` is not interpretable as a one-worker bound. The parent process retains every prior worker's parsed checkpoint/trace payload while launching the next child. Forked workers inherit those copy-on-write pages, and their RSS high-water therefore rises with worker index. The traced arm also records a large access trace. The full v1 JSON reaches 2.5 GB. The apparent RSS scaling is a capture-process artifact and is withdrawn as evidence about either substrate or single-worker memory scaling. V1's graph dimensions, work counters, wall times, and exact semantic parity remain usable; its source lock and raw capture are retained.

The first independent analyzer also rejected the valid globally numbered replicate labels. Its replicate validator has been corrected in a separately hashed v1.1 analyzer; all other v1 gates remain the same. The corrected analysis accepts the 45-worker schedule.

## Corrective protocol

Repeat the five sizes (0, 256, 1,024, 4,096, 16,384), three scope orders, and three replicates using one fresh worker process per size/order/replicate. Run monolithic, fallback, and anchor arms with tracing disabled. In each worker, summarize and discard each arm's full result before starting the next arm; preserve checkpoint/final digests, lifecycle statuses, graph sizes, work counters, and wall time only. Sample `ru_maxrss` before JSON serialization. The parent must stream each worker's compact JSON directly to the capture file and retain only its small integrity summary; it must not parse and retain all worker payloads before launching later children.

Keep the same source stability and exact parity gates. The independent analyzer recomputes the schedule, unique process IDs, final/checkpoint parity, anchor/fallback isolation, per-size work and graph summaries, and memory summaries from the compact raw capture. The primary memory value is still whole-worker high-water across all three arms, not per-arm allocation; report this remaining limit. If memory remains dominated by baseline runtime or allocator behavior, treat it as an upper bound and add per-arm fresh-process measurement before making component attribution claims.
