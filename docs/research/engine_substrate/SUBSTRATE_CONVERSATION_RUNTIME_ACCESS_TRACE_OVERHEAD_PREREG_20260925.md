# Conversation runtime access-trace overhead protocol

**Status:** protocol fixed before running the four-arm conversation timing capture.  
**Purpose:** estimate trace collection cost separately from scale-audit cost for the authored conversation deliberation rule family.

## Design

Use the existing deterministic one- and two-deliberation fixtures, each rebuilt on a fresh substrate in four arms: `plain` (both off), `scale_only`, `trace_only`, and `both`. Run six replicates per size (12 fixtures, 48 arm runs); rotate arm order by replicate modulo four. Time only `run_rules_report(100_000)` using wall and process CPU nanoseconds. Setup, terminal probe, projection, and counter snapshot remain outside the timed interval. Do not pool sizes into a single estimate.

## Gates and analysis

- All arms for each fixture must match progress, fixed-point status, and exact task projection, including selected answer and both rejection reasons.
- Plain/scale-only must emit no trace events; trace-only/both must emit events without overflow. Scale-only/both must expose counters; plain/trace-only must leave scale counters empty.
- In `both`, per-rule trace totals must reconcile with available scale-audit counts for accepted pattern edges, Attr evaluations, SetAttr attempts, AddEdge attempts, and node insertions. Every event resource must be contained in the static rule access projection or wildcard.
- Preserve each paired timing, arm order, environment, and source/native hashes. Report paired ratios/differences and medians/ranges by size. A failure invalidates the timing interpretation for that fixture.

The result is descriptive on one host and one small authored workload. It does not establish overhead at larger graph sizes, natural-task representativeness, complete trace coverage, frame locality, or partitioning benefit. The CAN four-arm study already exists; this run is a cross-family replication, not independent confirmation of universal cost.
