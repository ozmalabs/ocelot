# Label-blind query ranking v1 results

## Result

The source-locked confirmatory panel completed all 120 workers with zero failures. The independent analyzer passed all 2,707 integrity and reconstruction checks: exact task-policy-replicate schedule, unique fresh PIDs, source lock, candidate pool, known-row fit, deterministic random choices, entropy calculations/order, oracle-call/answer accounting, oracle-best upper-bound selection, survivor sets, and independently reconstructed task labels from triangular numbers, Python population variance, and simplicial Euler characteristic.

The new `rank_queries_by_disagreement` sees only an explicit four-hypothesis set, candidate inputs, and native Term predictions. It ranked 11–13 candidates, requiring 44–52 Term evaluations per selection. Its median selection wall time was 0.77–1.20 ms on this host. Each non-oracle policy used exactly one oracle call; the oracle-best diagnostic used 11–13.

| Task | Policy | Unique true hypothesis after one answer | Mean survivors |
|---|---|---:|---:|
| Triangular number | Fixed first | 10/10 | 1.0 |
|  | Seeded random | 10/10 | 1.0 |
|  | Entropy ranked | 10/10 | 1.0 |
|  | Oracle best | 10/10 | 1.0 |
| Population variance | Fixed first | 10/10 | 1.0 |
|  | Seeded random | 9/10 | 1.1 |
|  | Entropy ranked | 10/10 | 1.0 |
|  | Oracle best | 10/10 | 1.0 |
| Euler characteristic | Fixed first | 0/10 | 2.0 |
|  | Seeded random | 2/10 | 1.8 |
|  | Entropy ranked | 10/10 | 1.0 |
|  | Oracle best | 10/10 | 1.0 |

The true hypothesis survived the answer in all 120 workers. The selector's largest difference is on Euler: the caller's first family member cannot separate the true Euler formula from the constant/cell-count alternatives, but the entropy-ranked query uniquely identifies it in all ten replicates with one oracle answer. On the triangular task, every policy happens to be sufficient; on variance, random selection leaves an ambiguity once. These controls show that entropy ranking can find an informative query when the family contains one, rather than that it always improves outcomes.

## Interpretation and limits

This is a functioning substrate-side, label-blind query-ranking component, not just a proposed experiment. It supplies a clear decision boundary: given candidate hypotheses and a finite query pool, score inputs by predictive entropy without seeing target labels, then request one label and report the surviving hypotheses. Its scoring cost is linear in hypothesis count times candidate count.

The hypotheses, candidate pools, descriptors, and target task families are supplied and authored; the true hypothesis is included by construction. The selector uses equal hypothesis weights, not an inferred posterior. It is not yet integrated into `cegis_synthesize`, does not generate or maintain a version space, and does not show transfer to unseen functions. Python orchestration uses native Term evaluation, but the selector itself is not graph-authored or a Rust primitive. The oracle-best row is an upper bound that spends an oracle call on every candidate, not an eligible deployment policy.

The initial harness launch failed on a `Times` constructor mismatch; a later smoke exposed an Euler hypothesis that did not fit the disclosed known rows. Both were corrected before the refreshed source lock and confirmatory run. The failed lock and pilot-history record remain preserved; none of those smoke workers enter the confirmatory analysis.

## Artifacts

- Preregistration: `SUBSTRATE_LABEL_BLIND_QUERY_RANKING_V1_PREREG_20260930.md`
- Selector: `domains/query_selection.py`
- Runner: `scripts/substrate_label_blind_query_ranking_v1.py`
- Analyzer: `scripts/analyze_substrate_label_blind_query_ranking_v1.py`
- Source lock: `evaluation/substrate_capability/substrate_label_blind_query_ranking_v1_20260930_lock.json`
- Raw capture: `evaluation/reports/substrate_label_blind_query_ranking_v1_20260930_raw.json`
- Analysis: `evaluation/reports/substrate_label_blind_query_ranking_v1_20260930_analysis.json`
- Pilot audit: `evaluation/reports/substrate_label_blind_query_ranking_v1_20260930_pilot_history.json`

Claim boundary: this demonstrates a useful finite-pool query-selection mechanism for three authored hypothesis sets. It does not establish open-ended active learning, hypothesis acquisition, or generalization.
