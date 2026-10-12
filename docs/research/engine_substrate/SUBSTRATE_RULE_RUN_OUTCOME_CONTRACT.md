# Proposed rule-run outcome contract

**Status:** additive Rust and PyO3 report API implemented; pilot parity measured. Focused unit-test coverage, broader rule-family coverage, and public contract review remain outstanding.

## Evidence motivating the contract

The native `Substrate::run_rules` / PyO3 `run_rules(max_steps)` path returns an integer progress count. The loop checks `steps < max_steps` at the start of an outer pass, then attempts every dirty rule in that pass; each progressing rule increments `steps`. Therefore a pass can take the returned count past the requested value. On a two-rule toggle, requested caps 1 and 3 returned 2 and 4 respectively. A positive post-run probe showed remaining work in each condition. With opt-in repeated graph-state detection, the same cycle returned after 2 progress events, but the integer did not explain why it returned. See [`SUBSTRATE_CYCLIC_CAP_PILOT_RESULTS.md`](SUBSTRATE_CYCLIC_CAP_PILOT_RESULTS.md) and the raw [pilot records](../../../evaluation/reports/substrate_cyclic_cap_pilot_20260924.json).

## Proposed additive result

Keep existing integer-returning methods and their behavior for compatibility. Add a report-returning method whose result contains:

| Field | Meaning |
|---|---|
| `status` | `fixed_point`, `repeated_graph_state`, or `progress_budget_reached`. |
| `progress_steps` | Number of rule applications that changed state; may exceed the requested budget by work in the final complete pass. |
| `requested_progress_budget` | The value supplied by the caller. |
| `budget_overshoot` | `max(progress_steps - requested_progress_budget, 0)`. |
| `passes_completed` | Number of complete outer rule passes entered, for interpreting pass-granularity work. |
| `cycle_detection_enabled` | Whether repeated graph-state checking was requested. |

`progress_budget_reached` is deliberately conservative: if the budget becomes exhausted after a progressing pass, return that status even if the state might also be a fixed point. Proving fixed point may require another pass and hence extra unbudgeted work. A zero budget returns `progress_budget_reached` without attempting work. `fixed_point` is returned only when the ordinary no-progress or no-dirty condition is actually observed. `repeated_graph_state` means only that the opted-in fingerprint of the graph state repeated; it does not claim a fixed point. Since the current fingerprint does not include all possible external mutable inputs, retain the existing restriction and caveat for rules whose truth depends on external state.

This API reports the current soft, pass-boundary budget. It does not claim a hard CPU, wall-time, memory, or per-rule-attempt limit. Those remain supervisor/resource controls. Do not rename the legacy argument or change its behavior in this step.

## Why not break mid-pass to make the integer cap strict?

The runner snapshots dirty rule indices and clears their dirty bits before executing the pass. A mid-pass exit would need to restore dirty state for every unattempted rule, preserve mutations that re-dirty already attempted rules, and define whether a rule attempt or a progressing application consumes budget. Counting only progress cannot bound non-progressing match work; counting attempts changes the API's existing unit. This requires an explicit scheduling invariant and focused regression coverage, not a local `break`.

If a future hard work cap is required, define it separately as a budget over observable work units (for example, attempted rules or candidate bindings), persist unconsumed scheduling work, and test resume equivalence against an uncapped run. Keep resource termination (wall/CPU/RSS) in a supervising process because native matching work may occur inside a single rule attempt.

## Implementation and measurement sequence

1. **Done:** added `RuleRunStatus`, `RuleRunReport`, and `Substrate::run_rules_report`; the integer APIs continue to return their original progress count through the shared loop.
2. **Done:** exposed `Substrate.run_rules_report(max_steps, detect_cycles)` through PyO3 and `substrate_rs.ext.run_rules_report` as a dictionary with status, progress count, budget, overshoot, passes, and detection flag.
3. **Partly done:** the cyclic-cap pilot exercises ordinary overshoot, repeated graph state, immediate fixed point, zero budget with resume, and an exact-boundary one-shot rewrite. These are executable diagnostic cases, not a substitute for focused Rust/Python unit tests. Broader external-state cases remain open.
4. **Partly done:** release build and focused workload comparisons succeeded. A seven-repeat caller-visible overhead pilot found 2.72× median ratio but only on a very short synthetic cycle; broader semantic equivalence and representative workload timing remain open ([`SUBSTRATE_RULE_RUN_REPORT_OVERHEAD_RESULTS.md`](SUBSTRATE_RULE_RUN_REPORT_OVERHEAD_RESULTS.md)).
5. **Partly done:** the harness now records the typed report alongside the legacy integer path and keeps the terminal probe as an independent cross-check. Migrate other benchmark scripts after the API's focused test gate passes.

Legacy calls share the reporting loop and construct a small stack report before returning the integer. Their behavior is preserved. The paired pilot isolates caller-visible typed-result overhead, but not that common Rust construction cost. The audit-on/off and instrumented-build comparisons should include this API change before a no-cost claim is made.

No termination theorem follows from this interface. Weak-acyclicity or another proven restriction is still needed for a static mint-termination claim; caps only bound observed execution according to their stated unit.
