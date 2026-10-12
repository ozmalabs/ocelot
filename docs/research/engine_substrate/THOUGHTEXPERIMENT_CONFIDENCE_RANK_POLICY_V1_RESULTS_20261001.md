# Thoughtexperiment confidence ranking policy v1 — results

**Execution completed: 10/11 preregistered behavioral and integrity gates passed.** The sole failed gate was the predicted discriminator: after a known-bad candidate produced an independently verified [1,0] task-oracle result and that negative was recorded, the current raw-count policy was expected to keep choosing it first. It did not.

All three fresh workers trained through production scan_and_self_correct and persisted the two authentic production outcomes. Each evaluation branch then received one controlled unverified positive for episode_scoped_offer_guard. The calibration task selected that candidate first and independently measured [1,0]; only after observing this failure did the harness add the verified negative outcome. Matched branches inherited identical evidence. One branch retained the current graph-authored raw-count score; the other replaced the rank Program inside that branch with a graph-authored Beta(1,1) smoothed utility-mean score, with structural cost as a tiny tie breaker. Both arms passed the task oracle and left the primary unchanged.

| Policy | First candidate (all 3 workers) | First oracle output | Trials to success |
|---|---|---|---:|
| Current raw-count score | dedup_identity_fix | [1,1] | 1 |
| Branch-local smoothed mean | dedup_identity_fix | [1,1] | 1 |

The calibration probe provides the key context: before the verified negative was available, the current policy did select episode_scoped_offer_guard first and failed [1,0], then used fallback to pass. After that independent negative was added, both policies selected dedup_identity_fix first. The experiment therefore does **not** demonstrate a benefit from the proposed smoothed policy. It does show that the current ranker can respond to one verified negative in this fixture despite the preceding unverified positive. The preregistered expectation to the contrary remains recorded as a failed gate; see the [amendment](THOUGHTEXPERIMENT_CONFIDENCE_RANK_POLICY_V1_AMENDMENT_20261001.md).

This is a narrow mechanism comparison over one authored candidate pair and one recurrence task. The harness supplied the controlled unverified positive and persisted the independently verified negative; the production outcome path did not autonomously adjudicate that independent task utility. The smoothed score is authored, and three workers cannot establish probability calibration or general robustness. Candidate costs and evidence values were not varied. The result argues for testing policy behavior over candidate-cost gaps, contradictory evidence doses, and independent task families before changing the production ranking rule.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CONFIDENCE_RANK_POLICY_V1_PREREG_20261001.md)
- [Amendment](THOUGHTEXPERIMENT_CONFIDENCE_RANK_POLICY_V1_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_confidence_rank_policy_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_confidence_rank_policy_v1_lock_20261001.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_confidence_rank_policy_v1_raw_20261001.json)
