# Conversation guard sequential overhead preregistration

## Question

What incremental per-turn latency does `WorldAdapter.converse`'s per-instance RLock add in sequential use, relative to the same decorated conversation body using a no-op context manager?

## Procedure

In one fresh process, boot the full seed set once, attach a fixed three-percept scene, warm the route twice, then run 20 paired comparisons of identical `describe what you see` instruction turns on the same adapter. Each pair contains one guarded turn and one no-op-lock turn; deterministic shuffled pair order limits order bias. Record individual nanosecond durations, reply text, process/platform metadata, graph node count, and input fingerprints before and after capture. This isolates lock-wrapper cost in a sequential workload; graph state continues to evolve across turns, so the estimate is a small within-adapter paired measurement rather than a broad latency benchmark.

## Gates and limits

Require 40 timed calls, non-empty replies, stable fingerprints, and analyzer reproduction of paired deltas and summary statistics. Report median and p90 for each condition and the paired median delta. Do not infer concurrent throughput, other routes, different workloads, or native API safety from this result.
