# Bounded prefix-cost selector v1 results

Date: 2026-10-01  
Protocol: [preregistration](PREFIX_COST_SELECTOR_V1_PREREG_20261001.md)  
Runner: [source-locked selector and held-out panel](../../../evaluation/substrate_capability/prefix_cost_selector_v1.py)  
Analyzer: [independent gates](../../../scripts/analyze_prefix_cost_selector_v1.py)  
Capture: [three-worker raw data](../../../evaluation/reports/prefix_cost_selector_v1_workers_20261001.json)  
Analysis: [selector regret and overhead](../../../evaluation/reports/prefix_cost_selector_v1_analysis_20261001.json)  
Input lock: [source, native, and historical-capture lock](../../../evaluation/substrate_capability/prefix_cost_selector_v1_lock_20261001.json)

## Result

All **14/14 gates pass**. The frozen selector uses a beam of eight prefixes and at most 128 sampled partial bindings. It is tested against the historical CAN and retinal captures, then against a new 16-column retinal support profile over three fresh workers, each also measuring all 120 exact clause orders.

| Evaluation | Selector order/work | Reference | Outcome |
|---|---|---|---|
| CAN, 22 nonempty cases across cyclic/hub/clustered layouts and N=32/64/128 | Selected order matches measured-best in 22/22 | Recorded productive CAN best order | Exact order match on these bounded fixtures |
| Retinal uniform | 54 candidates | Exact minimum 54 | 0% regret |
| Retinal correlated | 364 candidates | Exact minimum 364 | 0% regret |
| Retinal rotated | 58 candidates | Exact minimum 57 | 1.75% regret |
| Held-out retinal, N=16 | 92 candidates | Exact minimum 65; default order 72 | 41.5% regret vs optimum; 27.8% more work than default |

The held-out selector choice is reproducible across all three workers: `[has_retinal_percept, rod_receptor, m_receptor, l_receptor, s_receptor]`. The exhaustive minimum is `[has_retinal_percept, s_receptor, m_receptor, l_receptor, rod_receptor]`. The sample-scaled estimate is 722 candidate tests, 7.8× the selector's measured 92 and 11.1× the exact 65. All orders preserve the real epoch guard and productive percept update, so this is a work-estimation and ranking failure rather than semantic drift.

## Selection cost

The Python prototype's median edge-index construction takes about 73 μs, and beam search takes about 2.25 ms; median total selection time is about 2.33 ms, with p95 around 3.25 ms across 21 repeated calls per worker. The historical N=12 retinal exact matcher measured roughly 0.12–1.40 ms for best-order closure depending on the support profile, so this prototype can cost more than one application of the rule on these small graphs. The estimator's structural scoring omits `where` predicates, and its Python index construction is not a native engine measurement.

## Interpretation

This is a useful negative result for the first general selector design. Sampled prefix expansion matches the recorded best order in the bounded CAN cases and is nearly optimal on the three original retinal profiles, but it fails on a new support alignment. Beam pruning keeps a locally cheap extension that excludes the globally cheaper suffix; the estimated-work value also substantially mispredicts actual candidate work. The small historical set was not enough to validate the heuristic. It should not be integrated as the default order policy.

The result sharpens the open problem: per-edge cardinality is insufficient, and bounded local samples can still miss higher-order cross-relation structure. A better design needs a calibrated estimator with uncertainty and a fallback, or an explicit runtime budget for exact prefix probes. Any successor should keep default order as control and report held-out regret and selector cost before engine integration. The scope here remains one five-edge pattern family plus CAN's four-edge motif, synthetic fixtures, and one host.
