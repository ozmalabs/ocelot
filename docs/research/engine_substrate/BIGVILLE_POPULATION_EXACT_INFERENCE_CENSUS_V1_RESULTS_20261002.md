# Bigville population exact-inference census v1 results (2026-10-02)

## Outcome

Three fresh processes each rebuilt and measured the entire 100-resident cast. Every one of the 300 resident-specific exact MAP results matched an independent exhaustive 3-state enumeration over 3^5 assignments; returned states rescored to the same energies. Whole-population JT matched the sum of the per-resident oracle energies in all three processes. The independent analyzer passes 16/16 checks, and each run preserves the model state and source/native lock.

All runs extracted 500 Concepts, 500 undirected pair factors (1,000 directed causal edges), and 100 five-node frames with no cross-frame factors. Every frame and the concatenated graph has width 2. Across the full generated population, effective resolution bins are distributed as 2:18, 3:29, 4:19, 5:5, 6:9, 7:4, 8:4, 9:6, 10:3, 11:3.

Median per-worker measurements are 56.9 ms to build the population, 7.50 ms to extract all 100 runtime networks, 75.6 ms to find a whole-graph min-fill order, and 10.05 ms for the ensuing whole-population JT call. The sum of 100 per-resident JT calls is 10.58 ms median, excluding each local order-finding cost. These measurements show that exact 3-state inference integrates over this full authored population and that decomposition/order preparation is a separate cost. They do not show that partitioning saves total cost.

## Scope

This is a complete census of one authored/generated Bigville population. Its five-topic resident model and lack of cross-frame factors are properties of the builder, not a finding about natural task structure. The result is an integration positive control using real cast parameters, not evidence that natural tasks have cheap cuts, that frame discovery is correct, or that partitioned inference is faster. It measures only width-2 3-state inference and one host; high-width multi-state growth and representative connected workload graphs remain open.

## Reproduction artifacts

- [Preregistration](BIGVILLE_POPULATION_EXACT_INFERENCE_CENSUS_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/bigville_population_exact_inference_census_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_bigville_population_exact_inference_census_v1.py)
- [Source lock](../../../evaluation/substrate_capability/bigville_population_exact_inference_census_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/bigville_population_exact_inference_census_v1_20261002.json)
- [Analysis](../../../evaluation/reports/bigville_population_exact_inference_census_v1_20261002_analysis.json)
