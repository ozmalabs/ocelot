# Borrowed scoped-rule path results

**Confirmation protocol:** [`SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_PREREG_20260926.md`](SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_PREREG_20260926.md)  
**Change:** scoped basic and delta-report paths now pass original active-rule references into the matcher instead of cloning every active `RewriteRule`. The reference list preserves each original vector slot. It is not retained between calls, so no cache invalidation is required.

## Semantic and provenance gates

- No-op sweep: **294/294** checks pass across 7 rule counts, 3 APIs, audit on/off, and 7 repeats. Candidate and Term work remain zero and state is unchanged.
- Topology matrix: **480/480** checks pass across chain/tree/star, N=8/16/32/64, five repeats, event/full arms, and omission controls. State parity, fixed points, owner notifications, and omission sensitivity all pass.
- Per-rule attribution: **180/180** checks pass across 30 N=64 event/full pairs. Original active slots `{0,2,3,4}` remain correct after tombstoning slot 1; per-rule/global counters conserve exactly.
- Source/native/build hashes and current build provenance pass in all three independent analyses.

## Setup cost

Against the preserved pre-change no-op analysis, the fitted audit-off slope falls from 180.3 to 21.2 ns per active rule for `scoped_basic` (8.5× lower), and from 188.7 to 23.2 ns/rule for `scoped_report` (8.1× lower). At 512 active rules, medians move from 92.97 to 11.37 μs for basic calls and 100.25 to 16.13 μs for report calls. Full-report calls remain about 4.1 μs at 512 rules.

With global audit on, fitted slopes are 42.2 and 43.3 ns/rule for basic/report. The residual relative to audit-off shows that audit instrumentation itself now forms a meaningful fraction of the small borrowed path; those timings should not be used as ordinary runtime estimates.

## Work-volume boundary

Borrowing removes rule-body clone/copy cost, but it does not reduce scoped matcher work. At N=64, the event/full candidate ratios remain 1.88× (chain), 17.79× (tree), and 68.61× (star), identical to the previous count profile. Instrumented wall ratios are 2.13×, 14.83×, and 43.89×, respectively. Therefore this change materially improves the no-match rule-count setup axis; it does not fix topology-sensitive scheduler work or demonstrate event-scheduling speedup.

The implementation reads live active rules under an immutable borrow and mutably borrows disjoint execution state. It avoids the invalidation hazard of a retained clone cache despite public/direct `rules` mutations elsewhere in the crate. Evidence remains generated workload evidence, not a production-distribution or natural frame-locality result.

## Reproduction artifacts

- No-op raw/analysis: [`borrowed v2 raw`](../../../evaluation/reports/substrate_scoped_noop_setup_cost_borrowed_v2_20260926.json), [`independent analysis`](../../../evaluation/reports/substrate_scoped_noop_setup_cost_borrowed_v2_20260926_analysis.json).
- Topology raw/analysis: [`borrowed v2 raw`](../../../evaluation/reports/substrate_frame_topology_borrowed_v2_20260926.json), [`independent analysis`](../../../evaluation/reports/substrate_frame_topology_borrowed_v2_20260926_analysis.json).
- Per-rule raw/analysis: [`borrowed v2 raw`](../../../evaluation/reports/substrate_frame_topology_cost_attribution_borrowed_v2_20260926.json), [`independent analysis`](../../../evaluation/reports/substrate_frame_topology_cost_attribution_borrowed_v2_20260926_analysis.json).
- The clone-only v1 profiler remains a counterfactual measurement of the former copied snapshot path; it is not a runtime component in the borrowed implementation.
