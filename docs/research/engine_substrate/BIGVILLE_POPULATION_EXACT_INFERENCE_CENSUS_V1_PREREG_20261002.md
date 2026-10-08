# Bigville population exact-inference census v1 preregistration (2026-10-02)

## Question

Can the current exact solver recover exact MAP assignments from every resident CAN in the registered 100-resident Bigville population, and does a whole-population junction tree agree with per-resident junction trees and an independent exhaustive oracle?

## Sampling frame and design

The sampling frame is the complete committed `seeds/bigville_cast100.json` population (100 residents), using the existing `worlds.bigville_can_beliefs` mechanical model builder and `seeds/can_native_reimplementation.json` rule vocabulary. No resident or graph is sampled by observed width or outcome. Three fresh processes rebuild the entire population independently. The resident CANs use 3-state vocabulary, real cast parameters, and the five-topic/five-coupling template. Extract the actual runtime model from every Microtheory after construction.

For each worker, measure all 100 resident networks independently; concatenate their extracted nodes/factors without adding edges to construct a whole-population disconnected control. Run exact MAP with min-fill and a certified per-resident order, and separately run one certified junction tree per resident. Independently enumerate all 3^5 assignments for each resident, compute its objective directly, and compare exact energies plus direct rescoring. Record each resident's effective resolution-bin count, graph size, certified width, and inference time. Also record whole-population min-fill width and complete source/native provenance.

All 100 residents per worker must pass exact fixture extraction, width and graph counts, energy/oracle agreement within 1e-8, valid 3-state outputs, and no mutation. Whole-population and per-resident results must have equal summed oracle energy. Require three fresh PIDs and pre/post source-lock equality. Report all residents and their distribution; there is no performance pass threshold.

## Claim boundary

This is a complete census of one authored/generated simulation population, not a random sample of natural cognitive tasks. Its per-resident topology is authored and disconnected by construction, so this cannot validate natural cheap-cut prevalence, discovered frame quality, boundary maintenance, or end-to-end partition savings. It tests integration and exactness on task-embedded parameters and 3-state values; it does not validate 3-state scaling at high width.

## Artifacts

- Runner: [bigville_population_exact_inference_census_v1.py](../../../evaluation/substrate_capability/bigville_population_exact_inference_census_v1.py)
- Analyzer: [analyze_bigville_population_exact_inference_census_v1.py](../../../evaluation/substrate_capability/analyze_bigville_population_exact_inference_census_v1.py)
- Lock: [bigville_population_exact_inference_census_v1_lock_20261002.json](../../../evaluation/substrate_capability/bigville_population_exact_inference_census_v1_lock_20261002.json)
- Capture: [bigville_population_exact_inference_census_v1_20261002.json](../../../evaluation/reports/bigville_population_exact_inference_census_v1_20261002.json)
- Analysis: [bigville_population_exact_inference_census_v1_20261002_analysis.json](../../../evaluation/reports/bigville_population_exact_inference_census_v1_20261002_analysis.json)
