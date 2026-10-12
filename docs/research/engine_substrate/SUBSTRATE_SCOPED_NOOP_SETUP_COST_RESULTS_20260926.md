# Scoped no-op setup cost results

**Protocol:** [`SUBSTRATE_SCOPED_NOOP_SETUP_COST_PREREG_20260926.md`](SUBSTRATE_SCOPED_NOOP_SETUP_COST_PREREG_20260926.md)  
**Runner:** [`substrate_scoped_noop_setup_cost_v1.py`](../../../scripts/substrate_scoped_noop_setup_cost_v1.py)  
**Independent analysis:** [`substrate_scoped_noop_setup_cost_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_noop_setup_cost_v1_20260926_analysis.json)

The seven active-rule counts (0–512), three APIs, two global-audit modes, and seven repeats pass all 294 independent checks. Scoped calls make no candidate or Term evaluations and preserve the graph exactly. With audit enabled, scoped rule enumeration equals active rules × 50 calls; per-rule auditing is disabled. Thus this is a no-match dispatch/setup measurement, not a matching-work measurement.

Median `scoped_basic` latency grows from 0.42–0.46 μs at zero rules to 93–107 μs at 512 rules. The fitted slope across the seven counts is about 180 ns/rule with audit off and 207 ns/rule with audit on. `scoped_report` grows from 3.97–4.02 μs to 100–112 μs, with fitted slopes about 189 and 210 ns/rule. `full_report` stays near 3.3–4.2 μs after warm-up over the same counts. The report API's paired incremental cost over basic is roughly 3.5–8.0 μs/call and is variable; do not interpret it as a constant or pure serialization cost.

This isolates a substantial linear dependence on active rule count in the scoped no-op path, even when no rule matches. It does not identify the share due to rule-list cloning versus filtering, dispatch, or audit hooks. Audit-on/off timing differences are descriptive only. Next, profile/measure the implementation components and prototype a cached eligible-rule view or cursor with rule mutation/invalidation controls; then rerun matched topology workloads, including audit-off timings. No general frame-locality or natural-task claim follows.
