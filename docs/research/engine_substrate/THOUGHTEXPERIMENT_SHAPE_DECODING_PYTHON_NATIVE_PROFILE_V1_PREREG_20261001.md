# Shape-decoding Python/native CPU attribution v1 — preregistration

**Date:** 2026-10-01  
**Question:** In the shape-decoding rehearsal, how much worker CPU is attributed to Python frames versus C-extension calls, sequentially and in a synchronized fanout-8 wave?

## Design

Use the same 100k-node shape-axis fixture and `dedup_identity_fix`; compute the baseline prediction outside the timed/profiled interval. Cross full-copy/shared-graph-page backends with sequential/concurrent fanout-8 execution and three fresh processes per cell (12 total). Profile each worker independently using `cProfile.Profile(timer=time.thread_time_ns, timeunit=1e-9)`. Record thread CPU per rehearsal, wave wall, Python-frame self CPU, C-call self CPU, and top per-thread call sites. Concurrent workers synchronize at a barrier before enabling profiles. Preserve the v2 native binary (which releases the GIL around the graph-then-struct cycle) and source lock.

## Gates

- 12 unique fresh processes; source/native binary lock and build freshness pass.
- All eight rehearsals per wave satisfy the positive task oracle and preserve the primary graph/rules/revision.
- Sequential/concurrent and both-backend signatures match.
- CPU-profile records are nonempty and nonnegative; Python-frame and C-call CPU totals remain within 5% of the enclosing per-thread CPU measurements.
- Report medians and top profile sites. Profiling overhead is not used for production throughput claims.

## Interpretation limits

`cProfile` attributes C-call duration to C functions but does not show whether a C function held or released the GIL. Python-frame time also includes profiler overhead. This can identify major call sites and where CPU accrues, but causal GIL ownership requires a GIL-aware sampler, which is unavailable under current host policy. One task and host; three repeats are exploratory.
