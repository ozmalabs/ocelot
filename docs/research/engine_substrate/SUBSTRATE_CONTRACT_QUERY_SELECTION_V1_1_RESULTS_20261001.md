# Contract query selection v1.1 — results

All eight native-runtime workers completed with stable source fingerprints. V1's three small operator families remain included: each identified its target in one selected query, but a random input order also succeeded in one query on 92.9% of trials across those easy families (mean 1.071 queries). They show correct maximum-disagreement selection but little practical advantage over random search on that candidate grid.

The added sparse-information family has eight hypotheses that agree on the two initial observations and on six of the nine unused inputs. Only `-5`, `-4`, and `-3` expose successive bits of the hypothesis identity. Both workers chose exactly `[-5, -4, -3]`, each with a balanced maximum-entropy split, and identified hidden target `h5` in three oracle queries. Across 4,000 seeded random query sequences, the mean was 7.496 queries; none identified the target in one query. The selector's median measured loop time was 168.6 microseconds on this host.

| Family | Hypotheses | Active queries | Random mean queries | Result |
|---|---:|---:|---:|---|
| Curvature | 3 | 1 | 1.107 | Target identified |
| Direction | 3 | 1 | 1.106 | Target identified |
| Polynomial | 3 | 1 | 1.000 | Target identified |
| Sparse coded set | 8 | 3 | 7.496 | Target identified |

The new [selector](../../../domains/contract_query.py) filters hypotheses by observed labels and chooses the unused finite-grid input with maximum entropy over their native Term predictions. The hidden target is available to the harness oracle only after a query is selected; the selector receives neither its ID nor the expected output. The independent analyzer recomputes the score, labels, and random baseline from the locked candidate definitions.

## Claim boundary

This is an initial, small finite-version-space result. Hypotheses, candidate inputs, initial observations, and target families were supplied by the harness. The method neither invents hypotheses nor establishes that the intended program is among them. The easy families show that maximum entropy does not automatically improve query count; the sparse family shows a clear benefit when informative inputs are rare. Next vary hypothesis-set size, expression depth, candidate-grid sparsity, and model misspecification, then measure end-to-end cost and verify that oracle labels come from a distinct evaluator path.

The first random-baseline analysis used JSON-sorted task order instead of the task declaration order used to seed workers. The corrected independent replay and preserved pre-correction lock are documented in the [analysis amendment](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_ANALYSIS_AMENDMENT_20261001.md).

## Artifacts

- [V1 preregistration](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_PREREG_20261001.md)
- [V1.1 preregistration](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_PREREG_20261001.md)
- [Analysis amendment](SUBSTRATE_CONTRACT_QUERY_SELECTION_V1_1_ANALYSIS_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/substrate_contract_query_selection_v1_1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_substrate_contract_query_selection_v1_1.py)
- [Lock](../../../evaluation/substrate_capability/substrate_contract_query_selection_v1_1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/substrate_contract_query_selection_v1_1_raw_20261001.json)
- [Analysis](../../../evaluation/reports/substrate_contract_query_selection_v1_1_analysis_20261001.json)
