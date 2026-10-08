# Finite-key degree-matched join results (2026-09-26)

## Question

Does native finite-key rule-join work change across graph degree profiles when node count and edge count are fixed? This comparison follows the join-arity/topology sweep and its direct work-attribution extension. It measures one authored positive-join family; it does not estimate natural task graph distributions.

## Protocol and lineage

The preregistered matrix fixes N=32/64/128/256 and exactly 2(N−1) directed edges in each of three connected bidirected trees: path, star, and balanced binary tree. Each graph is queried with one-, two-, and three-edge path-shaped rules, five replicates per cell. Each replicate runs an audit-off timing arm and a separate audit-on counter arm. Two independent process captures are compared. The full design and claim limits are in the [preregistration](SUBSTRATE_FINITE_KEY_DEGREE_MATCHED_PREREG_20260926.md).

The first v1 launch is retained as a disclosed harness failure: its independent oracle counted walks that revisit nodes, while the native matcher enforces distinct bindings for distinct pattern variables. The [v1.1 amendment](SUBSTRATE_FINITE_KEY_DEGREE_MATCHED_V1_1_AMENDMENT_20260926.md) corrected the oracle to count injective node-simple paths and made the star's three-edge rule a zero-match/no-effect control. The first pair of amended captures is also retained; analysis found and disclosed a JSON integer/string key normalization bug in the checker. A second pair, taken after the checker fix, is the confirmatory pair reported here.

## Result

Both confirmatory captures contain all 180 cases and pass every runner gate. The independent analysis passes 6,487 checks: exact injective-path counts and terminal sets, projected final graph hashes, progress bounds, audit counter identities, timed/audited semantic parity, source/native hashes, and exact cross-process semantic replication. Audit counters replicate exactly between processes.

The following N=128 medians show candidate-pair expansion and audit-off closure time. All graphs have 128 nodes and 254 directed input edges.

| Topology | Join edges q | Complete injective bindings | Candidate pairs | Audit-off closure median |
|---|---:|---:|---:|---:|
| Path | 1 | 254 | 508 | 0.173 ms |
| Path | 2 | 252 | 1,520 | 0.235 ms |
| Path | 3 | 250 | 3,536 | 0.339 ms |
| Star | 1 | 254 | 508 | 0.163 ms |
| Star | 2 | 16,002 | 33,020 | 8.496 ms |
| Star | 3 | 0 | 48,768 | 2.777 ms |
| Balanced tree | 1 | 254 | 508 | 0.161 ms |
| Balanced tree | 2 | 376 | 1,768 | 0.291 ms |
| Balanced tree | 3 | 492 | 4,764 | 0.530 ms |

The star's high-degree center drives a large intermediate join population. The q=3 star is useful as a negative control: native candidate expansion remains substantial even though injectivity makes the complete query unsatisfiable. Across N=32→256, the star q=2 median candidate count rises 62.4× for an 8× node increase; its closure median rises 103.8× in these captures. At N=256 this cell reaches 131,580 candidate pairs and 59.09 ms median. These are finite-range observations, not asymptotic bounds. Paths and balanced trees remain far cheaper for these same q values, demonstrating that N and E alone do not predict this matcher workload.

The source counters distinguish candidate-pair visits from complete bindings. Candidate pairs here equal candidate tests; edge-only matches perform no Term evaluations. The timing arm is uninstrumented, so the counter collection does not contaminate its closure measurement. These times include native closure/report work after graph/rule setup; setup is separately recorded in raw captures.

## Interpretation and limits

This result establishes degree/topology sensitivity for a specific variable-order join on authored bidirected trees. It is consistent with intermediate partial joins, rather than only final match count or edge count, controlling much of the work. It does not isolate degree as a sole causal factor: path, star, and balanced-tree graphs also differ in distance distribution, branching arrangement, and neighborhood overlap. Timing distributions are from one machine/software build and remain descriptive.

The result narrows the cheap-cut/tractability claim: bounded total graph size and sparse edge count do not ensure cheap matching when a rule joins through a high-degree hub. A realistic tractability claim needs workload-derived graph and rule-shape distributions, structural-width/boundary measures, and measurements of intermediate candidate populations. Rung 3/4 induction remains untouched.

## Reproduction artifacts

- Runner: [`substrate_finite_key_degree_matched_v1_1.py`](../../../scripts/substrate_finite_key_degree_matched_v1_1.py)
- Independent analyzer: [`analyze_substrate_finite_key_degree_matched_v1_1.py`](../../../scripts/analyze_substrate_finite_key_degree_matched_v1_1.py)
- Confirmatory raw captures: [process C](../../../evaluation/reports/mint_termination_degree_matched_v1_1_c_20260926.json), [process D](../../../evaluation/reports/mint_termination_degree_matched_v1_1_d_20260926.json)
- Independent analysis and 6,487 gates: [analysis JSON](../../../evaluation/reports/mint_termination_degree_matched_v1_1_analysis_20260926.json)
- Preserved initial amended captures: [process A](../../../evaluation/reports/mint_termination_degree_matched_v1_1_a_20260926.json), [process B](../../../evaluation/reports/mint_termination_degree_matched_v1_1_b_20260926.json)

## Next measurement

Use runtime-derived rule/graph instances from independently authored task families. Match or stratify by N, E, maximum degree, degree quantiles, rule join arity, and estimated separator width; report candidate-pair distributions and closure time. Include high-degree negative controls and separately measure frame extraction/partition cost. Do not generalize this synthetic matrix to the frequency of hub-shaped workloads without that corpus.
