# CAN runtime access-trace overhead preregistration

**Status:** protocol frozen before the four-arm timing extension.  
**Purpose:** estimate the incremental cost of the bounded access trace separately from the existing scale audit on the authored CAN closure workload.

## Question and hypotheses

On the existing CAN envelope (N=8/16; path/complete topology; two-/three-state updates), what measured wall and process-CPU cost is added by the access trace, apart from scale-audit instrumentation? No minimum speed or overhead threshold is asserted. The primary report will be per-cell paired ratios and raw timings, with instrumentation state/progress parity as a hard gate.

## Arms and pairing

Each deterministic graph instance is rebuilt independently in four arms:

1. `plain`: trace off, scale audit off;
2. `scale_only`: trace off, scale audit and per-rule counters on;
3. `trace_only`: trace on, scale audit off;
4. `both`: trace and scale audit on.

Use six seeds per each of eight N/topology/mode cells (48 graph instances, 192 arm runs). Rotate arm order by replicate modulo four to reduce fixed-order bias. Fixture generation, seed loading, graph construction, and final readback are outside the timed interval; the interval covers `run_rules(100_000)`. Record wall and process CPU nanoseconds. Retain every paired value; summarize medians and ranges, and do not pool unlike cells into a single estimate.

## Correctness and measurement gates

- All four arms for an instance must return the same progress count and final CAN state vector.
- Every arm must reach zero terminal progress and pass the independently coded local-update fixed-point check.
- The trace must drop zero events and preserve the already established per-rule conservation identities for pattern edges, Attr reads, SetAttr writes, and AddEdge attempts whenever scale audit is enabled.
- The event trace remains explicitly partial. JIT predicates, most aggregate/traversal reads, and uninstrumented effect families are outside this protocol.
- Preserve the raw JSON, runner/analyzer hashes, exact native binary/build manifest, seed file hash, and all source hashes. Failed cells remain in the raw record and invalidate the paired overhead summary.

## Analysis

For each workload cell report median `trace_only/plain`, `scale_only/plain`, `both/scale_only`, and `both/trace_only` ratios separately for wall and CPU time, plus paired differences and all six raw observations. Timing is descriptive on one host. No extrapolation to larger graphs or CPU commodity-scale claims is permitted. A semantic or event-accounting failure blocks overhead interpretation.

The earlier 16-pair CAN trace study is exploratory and informed the choice of workload strata; it is not part of the four-arm timing estimate. This protocol measures instrumentation cost only. It does not establish natural frame locality, trace completeness, task-level frame semantics, or partitioned-execution benefit.
