# Bigville high induced-boundary-width v1.1 results

## Result

The provenance-only v1.1 rerun passes all 11 runner checks and all 12 independent-analyzer checks across 72 cases: N=12/20, boundary dimensions k=2/4/6/8, chain/cycle/clique topologies, and three fresh workers. Exact energies agree with global junction-tree inference and an independent energy calculation. The source lock is stable before, during, and after every worker. The shared manifest and hashed parent log are independently verified; every explicitly hashed input exists and still matches its recorded digest, and the native engine reports current source provenance. The analyzer also reconstructs each child worker's stdout hash from the raw worker record and confirms empty stderr hashes.

At k=8, the chain has induced boundary width 1 and 66 elimination row evaluations versus 6,561 exhaustive boundary assignments; the cycle has width 2 and 174 rows; the clique has width 7 and 9,840 rows. At N=20,k=8, median message construction plus elimination takes 5.81 ms for chain, 6.47 ms for cycle, and 51.26 ms for clique; global JT takes 5.24, 5.79, and 35.71 ms respectively. The high-width clique remains slower than global inference. These medians are descriptive for three workers and this authored family.

The v1.1 run preserves the v1 design, conditions, and claim boundary while recording standard provenance. The v1 original result and its initial undercoverage failure remain unchanged.

## Limits

This is controlled offline inference evidence. It shows sensitivity to induced width in the declared structures; it does not establish natural task boundary prevalence, learned frame discovery, native boundary scheduling, or general CPU/memory speedup. The shared manifest captures the benchmark inputs and parent stdout/stderr; worker stdout is retained as structured per-worker output and worker stderr was empty in all three workers. Unrelated untracked workspace artifact contents are not hashed.

## Artifacts

- Provenance amendment: [v1.1 amendment](SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_V1_1_AMENDMENT_20260926.md)
- Original design: [v1 preregistration](SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_PREREG_20260926.md)
- Runner: [`substrate_bigville_high_boundary_width_v1.py`](../../../scripts/substrate_bigville_high_boundary_width_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_high_boundary_width_v1_1.py`](../../../scripts/analyze_substrate_bigville_high_boundary_width_v1_1.py)
- Current-source lock: [v1.1 lock](../../../evaluation/substrate_capability/bigville_high_boundary_width_v1_1_lock_20260926.json)
- Raw workers and shared manifest: [v1.1 report](../../../evaluation/reports/substrate_bigville_high_boundary_width_v1_1_20260926.json)
- Independent analysis: [v1.1 analysis](../../../evaluation/reports/substrate_bigville_high_boundary_width_v1_1_analysis_20260926.json)
- Parent process log: [stdout/stderr](../../../evaluation/run_logs/substrate-bigville-high-boundary-width-v1-1-20260926.stdout_stderr.log)
- Preserved original: [v1 results](SUBSTRATE_BIGVILLE_HIGH_BOUNDARY_WIDTH_V1_RESULTS_20260926.md)
