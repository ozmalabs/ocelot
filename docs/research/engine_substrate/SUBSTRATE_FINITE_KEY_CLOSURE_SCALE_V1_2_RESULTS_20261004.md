# Finite-key closure scale v1.2 current-source results

## Result

The source-locked sweep passes all 90 N × topology × literal-signature × replicate cases across 30 cells. Every case is admitted by the finite-fragment checker, reaches native `fixed_point`, exactly matches independently reconstructed terminal nodes and edges, and stays within `B=M+(N+M)^2-e0`. The capture is stable against its lock, including the current native extension and graph/rewrite/substrate/parser source files. The independent analyzer passes all cases and independently reconstructs the bound and graph states.

The tested range is N={4,16,64,128,256}, with cycle and dense directed no-self-loop inputs, M={1,2,4} fixed literal mint signatures, and three substrate constructions per cell. At N=256 the dense inputs contain 65,280 initial edges. For M=4, median measured setup/closure/export time is 2.11 ms at N=64, 3.55 ms at N=128, and 6.95 ms at N=256 on cycles; for dense inputs it is 26.1 ms, 119 ms, and 544 ms. Doubling N in the dense arm increases measured time about 4.56× in each interval, consistent with this workload's quadratic edge count. Every M=4 case has seven progressing firings; the conservative fact bound grows from 596 to 1,172 to 2,324 for dense N=64/128/256. This is empirical scaling for one fixed, positive rule family, not a uniform engine complexity theorem.

The exact finite-key theorem remains conditional: rules use positive graph-edge matches, fixed finite literal mint keys, monotone empty-attribute edge insertion, no deletes/replacements/external state, and a stable graph during one closure call. It is not weak acyclicity for arbitrary existential rules, unrestricted minting termination, or a general CPU-time guarantee. V1.1 through N=64 is retained as historical; v1.2 adds the current-source and larger-size evidence.

## Artifacts

- [V1.2 preregistration](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_2_PREREG_20261004.md)
- [Runner](../../../scripts/verify_mint_termination_scale_v1_2.py) and [independent analyzer](../../../scripts/analyze_mint_termination_scale_v1_2.py)
- [Current-source lock](../../../evaluation/substrate_capability/mint_termination_scale_v1_2_lock_20261004.json)
- [Compressed raw capture](../../../evaluation/reports/mint_termination_scale_v1_2_20261004.json.gz)
- [Independent analysis](../../../evaluation/reports/mint_termination_scale_v1_2_analysis_20261004.json)
- [Earlier v1.1 scale result](SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_1_RESULTS_20260926.md)
