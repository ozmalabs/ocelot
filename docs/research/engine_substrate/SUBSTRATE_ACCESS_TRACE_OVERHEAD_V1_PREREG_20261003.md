# Access-trace overhead replay v1 preregistration

Date: 2026-10-03  
Status: preregistered before matched on/off workers.

## Question

What is the descriptive request-time and event-capture cost of enabling concrete access tracing on the existing two-prompt fixture, holding the source-built engine, task, rule exports, and scheduler/work tracing constant?

## Design

Run three replicate pairs in fresh subprocesses. Each pair uses the same seed/replicate and ordered prompts, once with `OZMA_ACCESS_TRACE=1` and once with `OZMA_ACCESS_TRACE=0`. Randomize the six worker order with a fixed seed. The off arm disables concrete access event recording but retains operation-work tracing and all task execution. The on arm must emit direct `NodesOfType` events 36/37. Retain per-request elapsed nanoseconds, event/work rows, graph digests, task outcomes, and rule exports.

## Gates

1. Six distinct process IDs; stable lock and current engine provenance.
2. Each replicate pair has identical final semantic graph digest, matching the source-specific capture v2 digest.
3. Both arms reproduce the exact two-prompt schedule, lifecycle, shortfall, and existing semantic controls.
4. On arms emit concrete access events; off arms emit none. Scheduler/work rows have zero drops in both arms.
5. Report per-prompt and per-replicate latency pairs, ratios, medians, and ranges. Do not impose a speedup threshold or infer significance from three pairs.
6. Preserve all raw records and source hashes.

## Interpretation boundary

This estimates end-to-end request latency difference for enabling the access trace on this one authored fixture. It does not isolate individual event-site cost, generalize to other tasks, or measure release-mode throughput without capture/export overhead. All differences are descriptive at n=3 matched pairs.
