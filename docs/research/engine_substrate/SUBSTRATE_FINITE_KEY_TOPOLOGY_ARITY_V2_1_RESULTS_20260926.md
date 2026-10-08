# Finite-key topology and match-arity scale results v2.1

Date: 2026-09-26

## Result

The preregistered matrix contains four directed graph topologies, match arities 1/2/3, and three repeats: 171 cells total. The runner passed all 171 cells against its case oracle. The independent v2.1 analysis passes nine integrity, provenance, and exact terminal-graph checks for both uninstrumented and audit-on arms. The analyzer's tuple/list comparison failure and its analysis-only correction are disclosed in the [amendment](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_1_AMENDMENT_20260926.md); the raw capture was not changed.

On paths and cycles at N=256, median audit candidate tests are 510/1,018/1,524 for arities 1/2/3; median plain closure times are 0.174/0.217/0.253 ms (path) and 0.175/0.215/0.281 ms (cycle). On the out-star at N=256, candidate counts are 510/255/255 and plain times are 0.174/0.040/0.033 ms. The complete directed cases use smaller N; at N=20, arities 1/2/3 produce 760/15,200/289,560 candidate tests and median plain times of 0.223/3.733/118.723 ms. Term evaluations are zero throughout because this edge-only rule has no Term-valued predicates.

These figures show strong sensitivity to topology and intermediate join work for this authored finite-key rule family. They do not establish a general polynomial time bound, natural-task topology prevalence, or costs for Term-heavy rules. The capture records separate plain and audit-on wall/CPU cost; candidate counters are from the audit arm.

## Artifacts

- [Protocol](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_PROTOCOL_20260926.md)
- [Runner](../../../scripts/substrate_finite_key_topology_arity_v2.py)
- [Raw capture](../../../evaluation/reports/mint_termination_topology_arity_v2_20260926.json)
- [Corrected independent analysis](../../../evaluation/reports/mint_termination_topology_arity_v2_1_analysis_20260926.json)
- [Analysis amendment](SUBSTRATE_FINITE_KEY_TOPOLOGY_ARITY_V2_1_AMENDMENT_20260926.md)
- [Source lock](../../../evaluation/substrate_capability/mint_termination_topology_arity_v2_lock_20260926.json)

## Next measurement

The next tractability gate should separate topology from density and degree: compare edge-count-matched graph families, add runtime-derived rule/graph samples, and report separator or treewidth proxies alongside candidate distributions. Retain Term-heavy and non-mint controls so the finite-key insertion rule does not stand in for the whole closure engine.
