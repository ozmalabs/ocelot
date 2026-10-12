# Thoughtexperiment blinded proposal utility v1 — results

**Status: descriptive panel; confirmatory gate failed.** Four independently authored task families were run with four order workers each, five policies, and separate held-out scoring. The source-locked order capture contains no held-out labels; all 16 order records have the preregistered family/worker seed; every policy order is a complete candidate permutation; source hashes are stable across both stages. Across 80 family/worker/policy cells, every policy eventually found a passing candidate. Every attempted trial preserved the primary graph and verified the applied rule receipt.

| Policy | First-choice utility, 16 cells | Median trials to first success | Median recorded selection cost |
|---|---:|---:|---:|
| Experience rank | 8/16 (0.50) | 1.5 | 3.63 s |
| Frozen rank | 0/16 (0.00) | 2 | 89.7 ms |
| Default order | 16/16 (1.00) | 1 | 37.9 ms |
| Random order | 5/16 (0.3125) | 3 | 326 ms |
| Target memoization | 16/16 (1.00) | 1 | 862 ms |

These are descriptive pooled counts, not population estimates; there are only four task families, so no broad generalization follows. Experience rank improves on the frozen rank in this bounded candidate set, but does not beat the unchanged default order or same-target memoization on first-choice utility or trial count. It has no demonstrated transfer advantage: the experience records supply a relevant authored outcome class only for shape-axis and recurrence, while navigation and control-kind have no matching cross-family class. The only strong measured result is that the substrate's graph-resident ranker responds to the available outcome records in some families.

First-choice successes / four workers by family:

| Family | Experience | Frozen | Default | Random | Target memo |
|---|---:|---:|---:|---:|---:|
| Shape-axis | 4/4 | 0/4 | 4/4 | 2/4 | 4/4 |
| Recurrence | 4/4 | 0/4 | 4/4 | 0/4 | 4/4 |
| Navigation | 0/4 | 0/4 | 4/4 | 1/4 | 4/4 |
| Control-kind | 0/4 | 0/4 | 4/4 | 2/4 | 4/4 |

The cost ledger includes setup/enumeration, policy-order generation, the stated policy's training acquisition, and the candidate trials actually attempted. Median experience cost is dominated by acquiring and scoring the three other families' training records (3.29 s); the corresponding median is zero for default/frozen ordering. These figures do not include production commit/adoption, which was outside the preregistered selection experiment. They therefore show no economic advantage for experience ranking on this panel.

## Integrity limitation

The preregistration requires the independent scorer to recompute every candidate outcome on held-out behavior. The scorer instead stopped each policy arm at its first passing candidate. Across workers, the union of attempted held-out candidates covers 70 of 104 candidate instances (67%): shape-axis 13/24, recurrence 28/32, navigation 16/24, and control-kind 13/24. The frozen order capture and paired first-choice comparisons remain inspectable, but this missed gate invalidates the confirmatory claim under the preregistration. No unregistered post-hoc scoring is used to repair the gate.

The harness continues to use host-authored candidate enumeration and evaluator-authored task oracles. The panel establishes neither autonomous candidate generation nor self-improvement. A confirmatory rerun should amend the runner before locking so held-out scoring evaluates every candidate on the held-out instance set independently of policy stopping, then derives policy trial counts from the complete outcome matrix. It should retain the same source-separation, receipt, primary-isolation, and complete cost requirements.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_PREREG_20261002.md) and [cost/randomization amendment](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1.py), [adapter](../../../evaluation/substrate_capability/thoughtexperiment_blinded_panel_adapters_v1.py), and [rank policy](../../../evaluation/substrate_capability/thoughtexperiment_blinded_panel_rank_policy_v1_1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_blinded_proposal_utility_v1_lock_20261002.json)
- [Frozen orders](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_orders_20261002.json)
- [Held-out scores and cost ledger](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_scores_20261002.json)
- [Reproducible analysis](../../../scripts/analyze_thoughtexperiment_blinded_proposal_utility_v1.py) and [analysis output](../../../evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_analysis_20261002.json)
