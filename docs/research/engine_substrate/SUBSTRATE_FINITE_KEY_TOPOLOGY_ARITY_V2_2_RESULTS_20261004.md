# Finite-key topology and match-arity v2.2 current-source results

## Result

The current-source, source-locked replay passes 171/171 topology/size/arity/repeat cells. Every plain and audit-on closure reaches `fixed_point`, stays within the finite-fact bound, and matches the independent injective-binding terminal-graph oracle. The independent analyzer passes all nine checks, including the balanced 57-cell × 3-replicate inventory, exact matched-arm state, randomized arm order, source lock, fresh native build, loaded extension hash, and parent log integrity.

At N=256, path/cycle candidate-test medians remain approximately linear with match length (path: 510/1,018/1,524; cycle: 512/1,024/1,536 for arity 1/2/3), with plain closure medians 0.287/0.343/0.386 ms for paths and 0.303/0.377/0.408 ms for cycles. Out-stars have a different join shape: at N=256, candidate counts are 510/255/255 and plain time is 0.333/0.041/0.037 ms. Complete graphs are much more expensive despite their smaller maximum N=20: candidate counts are 760/15,200/289,560 and plain time 0.317/5.157/173.199 ms at arities 1/2/3. Term evaluations are zero because the rule uses only positive edge matches.

This reproduces the finite-key topology/arity findings against current source and makes the join-cost sensitivity concrete. It does not support a single polynomial exponent independent of arity/topology, or natural topology prevalence. The observed candidate growth is for one fixed finite-key mint effect and four authored graph families; Term-heavy, multiple-edge-type, interacting-rule and runtime-derived graph distributions remain open.

## Artifacts

- [V2.2 protocol](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_2_PROTOCOL_20261004.md)
- [Runner](../../../scripts/substrate_finite_key_topology_arity_v2_2.py) and [independent analyzer](../../../scripts/analyze_substrate_finite_key_topology_arity_v2_2.py)
- [Current-source lock](../../../evaluation/substrate_capability/mint_termination_topology_arity_v2_2_lock_20261004.json)
- [Compressed capture](../../../evaluation/reports/mint_termination_topology_arity_v2_2_20261004.json.gz)
- [Independent analysis](../../../evaluation/reports/mint_termination_topology_arity_v2_2_analysis_20261004.json)
- [Historical v2.1 result](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_1_RESULTS_20260926.md)
