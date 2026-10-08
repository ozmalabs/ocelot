# Live strict-route cost and full-graph delta v1.2 — results

Date: 2026-10-02

## Result

The locked confirmatory panel completed 66 unique fresh workers over the preregistered 22 task/condition/provider-count cells with three repeats each. Source/native locks remained stable. The independent analyzer passes **11/12 gates**. Probe, request, signed-label, receipt, authentication, live outcome, and held-out replays all pass. Correct truthful examples were adopted; truthful wrong examples were rejected; conflicting labels were ambiguous; unanimous trusted false labels were accepted and caused wrong adoption, as expected from the evidence policy.

The complete parent-graph delta gate **fails in every cell**. Between the captured pre-call graph and post-call graph, workers add 703–730 nodes and 475–512 edges. One pre-existing `Agent` node gains metadata fields, and the allocator `next_id` advances. The graph delta is therefore much larger than the single code shape recorded in the codebook. No nodes or edges are removed. The capture reveals that the first live call lazily populates a large amount of graph state inside the timed `converse` route, so this before/after boundary conflates lazy initialization with the adoption mutation. It cannot establish adoption-only graph atomicity.

## Timing

Across cells, median live `converse` timings range from 171.9–178.6 ms for parity and 185.5–193.8 ms for threshold. Individual calls show noisy outliers, and three workers per cell do not support a provider-count scaling law. These timings include the existing lazy initialization path and should not be interpreted as steady-state request cost. The raw data retains exact graph snapshots and phase timings for follow-up analysis.

## Interpretation and next gate

The call-level outcome evidence reproduces the expected receipt behavior, including the false-label failure. The failed invariant identifies a measurement-boundary problem and a user-visible cold-path cost: lazy graph population occurs during `converse`. A focused, source-locked [adoption-boundary panel](SUBSTRATE_ADEQUACY_ADOPTION_BOUNDARY_V1_RESULTS_20261002.md) subsequently isolates `_teach_shape` and passes its exact graph-delta gate in three fresh workers. Cold initialization and other per-turn mutations remain mixed into the full `converse` route; measure them separately before claiming steady-state route cost. Do not claim the full-conversation graph-delta gate passes from shape counts alone.

## Artifacts

- [Preregistration](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_2_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_adequacy_live_route_cost_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/substrate_adequacy_live_route_cost_v1_2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/substrate_adequacy_live_route_cost_v1_2_raw_20261002.json)
- [Analysis](../../../evaluation/reports/substrate_adequacy_live_route_cost_v1_2_analysis_20261002.json)
- [v1 partial result and protocol audit](SUBSTRATE_ADEQUACY_LIVE_ROUTE_COST_V1_RESULTS_20261002.md)
