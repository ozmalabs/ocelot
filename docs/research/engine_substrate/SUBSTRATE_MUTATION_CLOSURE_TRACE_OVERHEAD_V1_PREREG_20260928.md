# Mutation-to-fixpoint trace overhead v1 preregistration

Date: 2026-09-28  
Status: preregistered controlled native factorial.

## Question

What wall and process-CPU time does scoped scheduler/deferred-work tracing add to mutation-to-fixpoint closure, for one sparse-positive family and one matcher-dense family, as rule count grows?

## Workloads

Use rule counts N={8,32,128}, four arms (baseline, scale audit only, work trace only, both), and three fresh worker processes. Each cell times 32 independently constructed fixtures. Construction is outside timing; the single trigger-edge insertion and complete `run_rules_report` call are inside. Arm order is rotated within worker and size/family. All sources and the native extension are hashed before/after every worker. See the amendment for the corrected rule-progress oracle and timed-batch/work-attribution refinement.

* Sparse positive: N one-edge rules with distinct trigger/effect types; one timed trigger insertion enables one rule and exactly one derived edge.
* Matcher-dense: N two-edge rules with distinct types. For rule 0, fixture parameter D=8 provides D−1 `a` edges and D `b` edges from a common source to disjoint y/z sets; the timed insertion completes the a fanout. The two-clause join should produce D distinct derived edges after D² candidate pair combinations. Other rules have no a edges. This isolates matcher work while preserving a simple independent output oracle. One rule application may insert all D output edges: require one progress step and D derived edges, not D progress steps.

The principal contrast is trace-only versus baseline; trace-with-audit versus audit-only estimates the conditional trace effect. Audit-only versus baseline and the interaction are descriptive. Do not pool families or rule counts into one overhead number.

## Gates

1. Three distinct fresh processes, complete N×family×arm grid, eight calls per cell, source/native hashes stable throughout.
2. Every call reaches `fixed_point`; sparse calls report one progress step and one derived edge; dense calls report one progress step and D derived edges.
3. Final graph digests and reports match exactly across arms within each family/size/replicate.
4. Scale-audit integer counters match between audit-only and both arms. Trace-only scheduler pass/slot totals match audit-only counters. Audit-only `cand_tested` equals 32 per sparse cell and `32*(D²+D)` per dense cell.
5. Trace rows are empty when disabled, present when enabled, and have zero drops.
6. Report block and per-call timing deltas with all three process-block values and ranges. The sample is a pilot, not a general hardware or engine bound.

## Claim limits

Synthetic authored fixtures are not natural task distributions. The experiment times Python-to-native edge insertion plus complete closure, but not construction, boot, queues under load, memory/energy, scoped scheduling, or wall time at commodity-scale graphs. The matcher-dense family probes one two-clause join shape and D=8 only. Instrumentation changes are judged against exact state and work parity; timing alone cannot establish trace completeness outside recorded scheduler measures.
