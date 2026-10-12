# Live strict-route evidence-count and cost panel v1 — results

Date: 2026-10-02

## Result and protocol audit

The capture contains 66 unique fresh workers covering the two tasks, four evidence conditions, provider counts 1/3/5 (except the undefined one-provider conflict), and three repeats per cell. Source/native locks are stable. The independent analyzer passes 11/11 implemented checks across 22 cells, recomputing selected probes, requests, signed labels, receipts, provider authentication, actual adoption outcomes, and held-out predictions.

This is a **partial protocol result**. The preregistration also required the parent graph to remain unchanged except for the expected single code-shape adoption. The capture records shape IDs/deltas but contains no before/after parent-graph snapshot or digest, and the analyzer has no whole-graph invariant check. Therefore that preregistered gate is unverified; 11/11 analyzer checks must not be read as all protocol gates passing. A confirmatory, source-locked capture must add canonical parent graph state before and after `converse` before this condition can be closed.

## Observed behavior and cost

Correct truthful examples were accepted and added one shape, with exact held-out behavior. Truthful counterexamples were rejected without shape growth. Conflicting labels were ambiguous and caused no shape growth. When every test signer supplied the same false label, the wrong candidate was accepted and failed held-outs. This directly shows that signature verification establishes who signed a label, not whether it is true.

Median live `converse` time ranged from 171.4–177.7 ms for parity cells and 186.9–193.8 ms for threshold cells. Across provider-count conditions there is no clear latency trend in this small three-repeat panel. Receipt adjudication medians are about 0.06–0.11 ms; adapter setup and the rest of the live path dominate the measured call. Process wall time includes fresh-process startup and is reported separately in the raw capture. These are descriptive timings, not CPU-only measurements or confidence intervals.

## Scope and next gate

The panel uses one host, two authored Boolean task families, finite synthetic domains, deterministic test keys, and harness-generated labels. It does not estimate natural label quality, task prevalence, multi-probe acquisition cost, or full-seed user-request cost. Its false-label result is an adversarial epistemic boundary, not a prevalence estimate.

The confirmatory [v1.2 panel](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_2_RESULTS_20261002.md) records canonical full-graph snapshots. Its full-graph gate fails because lazy state loading occurs during the live call; the call-level delta cannot be attributed to adoption alone. Treat v1 as partial and v1.2 as a failed isolation-boundary check, not as evidence that the adoption transaction itself mutates unrelated state. The next gate is to separate initialization from a warmed adoption transaction, including a cold no-adoption control and separate cold/steady-state timings.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_live_route_cost_v1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_live_route_cost_v1_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_live_route_cost_v1_analysis_20261002.json)
