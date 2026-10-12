# Bigville high induced-boundary-width results

## Result

The corrected 72-case capture passed all nine independent analysis gates across N=12/20, k=2/4/6/8, chain/cycle/clique boundaries, and three fresh workers. The analyzer independently checks the exact topology edge set, boundary sizes, min-fill order, bucket scope sizes and evaluation counts, component message work, source stability, complete states, and whole-model energy agreement to global JT.

At k=8, the chain has induced boundary width 1 and uses 66 elimination row evaluations versus 6,561 exhaustive boundary assignments. The cycle has width 2 and uses 174 rows. The clique has width 7 and uses 9,840 rows. Thus the controlled data show the expected dependence on induced width: increasing boundary cardinality is manageable for chain/cycle, while a dense boundary incurs exponential-sized buckets. For N=20,k=8, the clique message+VE median is 52.44 ms against 38.00 ms for global JT; chain is 6.31 ms against 5.54 ms. No partitioned speed advantage is established.

At N=20,k=8, the direct repeated-interior assignment-count estimate is about 20.1M for chain, 20.7M for cycle, and 23.4M for clique. That count is an algorithmic estimate, not a timed direct-oracle run. The initial harness launch covered only 24 rather than the preregistered 72 cases; its gate failure is retained as `substrate_bigville_high_boundary_width_v1_design_failure_20260926.json`. The runner was corrected to replicate all three topologies in each worker before the passing replay.

## Limits

This is a controlled augmentation of deterministic authored Bigville CANs. It demonstrates exact component-message correctness and a width-sensitive work envelope only for k≤8 and these topology families. It does not estimate natural task boundary widths, validate learned frame discovery, implement native boundary scheduling, or establish end-to-end CPU/memory benefits. Dense-boundary results align with the expected hard case; natural connected task graphs remain necessary before making a workload claim.

## Artifacts

- Protocol: [preregistration](SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_PREREG_20260926.md)
- Runner: [`substrate_bigville_high_boundary_width_v1.py`](../../../scripts/substrate_bigville_high_boundary_width_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_high_boundary_width_v1.py`](../../../scripts/analyze_substrate_bigville_high_boundary_width_v1.py)
- Source lock: [lock JSON](../../../evaluation/substrate_capability/bigville_high_boundary_width_v1_lock_20260926.json)
- Raw capture: [JSON report](../../../evaluation/reports/substrate_bigville_high_boundary_width_v1_20260926.json)
- Preserved initial coverage failure: [JSON capture](../../../evaluation/reports/substrate_bigville_high_boundary_width_v1_design_failure_20260926.json)
- Analysis: [analysis JSON](../../../evaluation/reports/substrate_bigville_high_boundary_width_v1_analysis_20260926.json)
