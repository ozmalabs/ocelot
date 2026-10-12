# Thoughtexperiment blinded proposal utility v1.2 — results

**Gate result: pass for this bounded confirmatory panel.** Four independently authored families were run with four workers each. The source lock contains 48 hashes, including the exact runner, adapter, rank-policy, analyzer, task and protocol files, engine inputs, and loaded native binary. Current source hashes match the lock; the order capture was source-stable and held-out blind; the score capture binds to the frozen orders. All 104/104 worker/family/candidate held-out instances were scored exactly once. Every family-worker set included both passing and failing candidates. All 144 policy-prefix trials and all 104 exhaustive-audit branches verified their candidate receipts and preserved the primary state. The analyzer passes all seven checks, including order permutations, stopping prefixes, exhaustive outcome coverage, and selection/audit cost reconciliation.

| Policy | First-choice utility, 16 cells | Median trials to first success | Median policy-selection cost |
|---|---:|---:|---:|
| Experience rank | 8/16 (0.50) | 1.5 | 3.64 s |
| Frozen rank | 0/16 (0.00) | 2 | 75.1 ms |
| Default order | 16/16 (1.00) | 1 | 36.4 ms |
| Random order | 5/16 (0.3125) | 3 | 360 ms |
| Target memoization | 16/16 (1.00) | 1 | 876 ms |

The family pattern is stable: experience ranking gets the first choice in all shape-axis and recurrence workers, but in none of the navigation or control-kind workers. The experience arm improves first-choice utility and trial count over zero-history ranking on this task set. It does not outperform unchanged default ordering or target memoization. Its median selection cost is about 100 times the default median, primarily because the ledger charges the three other families' training-data acquisition. Target memoization also pays for same-family training acquisition. Exhaustively scoring every candidate adds 104 audit branches; this cost is separately recorded and is not credited to any policy as a free operational capability.

The preregistered selection signal is present versus frozen ranking, but there is no transfer or economic advantage over the strongest controls. The four families share a deliberately bounded authored candidate mechanism, and only shape-axis/recurrence have a matching cross-family outcome class. These results are not evidence of natural-task prevalence, broad general capability, or open-ended self-improvement. Candidate generation and utility oracles remain host-authored.

## Family-level first-choice results

| Family | Experience | Frozen | Default | Random | Target memo |
|---|---:|---:|---:|---:|---:|
| Shape-axis | 4/4 | 0/4 | 4/4 | 2/4 | 4/4 |
| Recurrence | 4/4 | 0/4 | 4/4 | 0/4 | 4/4 |
| Navigation | 0/4 | 0/4 | 4/4 | 1/4 | 4/4 |
| Control-kind | 0/4 | 0/4 | 4/4 | 2/4 | 4/4 |

## Artifacts

- [Original preregistration](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_PREREG_20261002.md), [cost amendment](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_AMENDMENT_20261002.md), [exhaustive-scoring amendment](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_AMENDMENT_20261002.md), and [analysis-lock amendment](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_4_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_2.py), [adapter](../../../evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py), [rank policy](../../../evaluation/substrate_capability/thoughtexperiment_blinded_panel_rank_policy_v1_1.py), and [locked analyzer](../../../scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1_2.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_2_lock_20261002.json)
- [Frozen orders](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_orders_20261002.json)
- [Held-out scores and cost ledger](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_scores_20261002.json)
- [Analysis output](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_2_analysis_20261002.json)
