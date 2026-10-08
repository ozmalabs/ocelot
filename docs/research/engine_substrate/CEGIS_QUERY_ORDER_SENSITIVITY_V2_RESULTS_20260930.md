# CEGIS query order sensitivity v2 results

## Result

All ten fresh-process workers completed without failures. The independent analyzer passed the source-lock, schedule, worker-uniqueness, fixed-literal-set, query/order, row, synthesis-work, and heldout reconstruction checks.

With the same 15-literal set forced into every synthesis call, the ascending policy selected `n=2,3,4` in all five runs. Seeded permutations selected two counterexamples in every run, with varying inputs. Both policies converged to `(n * ((n + 1) / 2))` and scored all six heldout values exactly in all five runs.

| Measure, median across five paired runs | Ascending | Seeded permutation |
|---|---:|---:|
| Counterexample rows added | 3 | 2 |
| Oracle calls on candidate-family values | 20 | 16 |
| Total oracle calls inside CEGIS | 26 | 21 |
| Native candidates explored across synthesis calls | 3,379,115 | 2,758,471 |
| Native synthesis elapsed time | 151.96 s | 102.23 s |
| End-to-end CEGIS wall time | 155.02 s | 104.37 s |

This controlled comparison removes the v1 mechanism where observed labels expanded the available integer literals. The seeded permutation arm used about 18.4% fewer candidate-family oracle calls and 18.4% fewer total oracle calls, and about 18.4% fewer enumerated candidates. On this one task, order can materially affect how quickly informative labels constrain the MDL search. The seeded arm still does not optimize a query objective: its results depend on the selected fixed seed and the authored domain/order. Five repeats of one function do not estimate a general policy advantage. The CEGIS routine continues to query the oracle sequentially while scanning candidates; every call is charged in the capture.

The controlled literal set makes synthesis much slower than the output-derived default in v1: median per-arm CEGIS time is roughly 104–155 seconds here versus 3–7 seconds in v1. This is a strong tractability result for configuration sensitivity on this microtask, not a claim about general synthesis. Follow-up should test several functions, compare order strategies on matched candidate pools, and implement a bounded label-sealed disagreement selector only after the current fixed-order and random-order baselines are reproduced on those task families.

## Artifacts

- Preregistration: `CEGIS_QUERY_ORDER_SENSITIVITY_V2_PREREG_20260930.md`
- Runner: `scripts/cegis_query_order_sensitivity_v2.py`
- Analyzer: `scripts/analyze_cegis_query_order_sensitivity_v2.py`
- Source lock: `evaluation/substrate_capability/cegis_query_order_sensitivity_v2_20260930_lock.json`
- Raw capture: `evaluation/reports/cegis_query_order_sensitivity_v2_20260930_raw.json`
- Analysis: `evaluation/reports/cegis_query_order_sensitivity_v2_20260930_analysis.json`

Claim boundary: one authored triangular-number task and five paired schedules. This measures family-order sensitivity under a fixed literal vocabulary; it does not establish learned query selection, transfer to natural tasks, or general active-learning capability.
