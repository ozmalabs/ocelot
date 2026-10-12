# Native candidate-adequacy query v1.4 results

## Result

The fresh 40-panel, three-arm capture passes all five run gates, and the independent analyzer passes all 14 checks. All 120 source-locked workers completed. Native and host candidate-positive query order and decisions match on all 40 paired panels; query receipts, task-identity exclusion, score/prediction replay, and held-out transfer checks pass.

On the 10 fresh opposition panels, two are initially accepted with the wrong candidate. Native and host candidate-positive arms both find the two counterexamples and request help using two labels total. Uniform finds one and leaves one false accept. The prior v1.3 seed cohort had three false accepts; these varying small counts are not prevalence estimates. Additive and product controls select correctly in all 20 panels without false help, and inequality controls request help in all 10.

## Cost after the matcher fast path

| Native candidate-positive worker metric | v1.3 median | v1.4 median | Change |
|---|---:|---:|---:|
| Total CPU | 375.17 ms | 291.29 ms | −22.4% |
| Candidate eligibility closure | 75.31 ms | 6.72 ms | 11.2× faster |
| Query selection closure | 20.23 ms | 12.17 ms | 1.66× faster |
| Query adjudication closure | 18.61 ms | 12.31 ms | lower in this cohort |
| Probe prediction closure | 18.96 ms | 19.66 ms | similar |
| Peak RSS median | 155.5 MiB | 155.1 MiB | similar |

The host candidate-positive arm median CPU is 280.09 ms in v1.4, so the native arm is now about 4% higher in this workload, compared with about 34% higher in v1.3. Since the task seeds and engine builds differ, these are descriptive cross-capture comparisons, not counterbalanced estimates. Native eligibility is no longer the dominant end-to-end cost component here.

## Interpretation and next gate

The end-to-end replication supports the scale result: the generic fully bound edge lookup retained exact query behavior and materially reduced native eligibility and total worker CPU on this workload. This remains one authored numeric task suite with a supplied menu and host-prepared rank/labels. It does not establish broad matcher correctness, general query competence, natural-task prevalence, or autonomous hypothesis acquisition.

Next add or run differential matcher coverage for fully bound match clauses across present/missing edges, repeated variables, parallel edge types, and mutation/retraction pathways. Then repeat the fast-path comparison on independently authored graph workloads and the broader native capability set. Continue the self-improvement responsibility transfer gate separately: diagnosis is bounded here, candidate generation remains supplied.

## Reproduction and evidence

The [v1.4 protocol](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_4_PREREG_20261005.md), [runner](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_4.py), [source lock](../../../evaluation/substrate_capability/native_candidate_adequacy_query_v1_4_lock_20261005.json), [raw capture](../../../evaluation/reports/native_candidate_adequacy_query_v1_4_20261005.json), and [independent analysis](../../../evaluation/reports/native_candidate_adequacy_query_v1_4_analysis_20261005.json) preserve the experiment. Compare with the [v1.3 results](SUBSTRATE_NATIVE_CANDIDATE_ADEQUACY_QUERY_V1_3_RESULTS_20261005.md) and the [matcher scale v3 results](SUBSTRATE_NATIVE_QUERY_ELIGIBILITY_SCALE_V3_RESULTS_20261005.md).

