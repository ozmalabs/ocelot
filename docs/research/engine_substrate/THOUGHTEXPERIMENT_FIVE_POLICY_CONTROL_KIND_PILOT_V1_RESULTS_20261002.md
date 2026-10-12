# Thoughtexperiment five-policy control-kind pilot v1 — results

**Result:** independent review passes 14/14 integrity gates.

Four fresh order workers produced five complete candidate permutations; four separate scoring processes consumed those saved orders. The order capture contains no held-out fields, the score capture binds to its exact SHA-256, and all five policies eventually solve the held-out control-name cases in all four workers.

| Policy | First candidate passes | Attempts to success by worker | Median attempts |
|---|---:|---|---:|
| Experience rank | 0/4 | 2, 2, 2, 2 | 2 |
| Frozen rank | 0/4 | 2, 2, 2, 2 | 2 |
| Default order | 4/4 | 1, 1, 1, 1 | 1 |
| Random order | 2/4 | 3, 1, 5, 1 | 2 |
| Target memoization | 4/4 | 1, 1, 1, 1 | 1 |

Experience rank received 20 training records from recurrence, navigation, and shape-axis. None matched the control-kind target or candidate outcome class, so all control candidates had zero prior counts and experience order exactly equaled frozen rank. The first candidate failed; the second, comparison flip passed. Target memoization used six same-target control-kind training outcomes and ranked the known successful comparison flip first, matching default order. This is a measured cross-family transfer null on one bounded lexical task, consistent with the separate v1.2 null-transfer probe.

Median policy trial time is not used to claim efficiency: each timed trial includes fresh substrate setup and oracle scoring, not a common isolated branch/adoption cost, and one default-order worker had a large scheduling outlier. This pilot validates five-policy ordering, target memoization, and the order-before-score interface on one family; it does not replace the four-family panel or establish general self-improvement.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_FIVE_POLICY_CONTROL_KIND_PILOT_V1_PREREG_20261002.md)
- [Order-policy core](../../../evaluation/substrate_capability/thoughtexperiment_blinded_panel_rank_policy_v1.py)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_five_policy_control_kind_pilot_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_five_policy_control_kind_pilot_v1_lock_20261002.json)
- [Frozen orders](../../../evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_orders_20261002.json)
- [Held-out scores](../../../evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_scores_20261002.json)
- [Independent reviewer](../../../evaluation/substrate_capability/review_thoughtexperiment_five_policy_control_kind_pilot_v1.py)
- [Review capture](../../../evaluation/reports/thoughtexperiment_five_policy_control_kind_pilot_v1_review_20261002.json)
