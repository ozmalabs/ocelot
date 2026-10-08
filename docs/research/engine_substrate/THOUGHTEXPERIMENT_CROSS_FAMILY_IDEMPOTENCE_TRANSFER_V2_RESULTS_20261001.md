# Thoughtexperiment cross-family idempotence transfer v2 — results

**Result:** 9/9 preregistered gates pass; task staging follows the [amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_AMENDMENT_20261001.md).

The two-candidate recurrence task makes global idempotence insufficient: its oracle requires exactly one offer for each candidate.

| Arm | Trials to oracle | First candidate | First candidate's offers | Cross-target prior success | Oracle passes |
|---|---:|---|---|---:|---:|
| `cold` | [2, 2, 2] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [[1, 0], [1, 0], [1, 0]] | [0.0, 0.0, 0.0] | 3/3 |
| `experience` | [1, 1, 1] | ['dedup_identity_fix', 'dedup_identity_fix', 'dedup_identity_fix'] | [[1, 1], [1, 1], [1, 1]] | [1.0, 1.0, 1.0] | 3/3 |

The cold ranker first selects the smaller episode-scoped guard, which suppresses the second valid offer; it then finds the candidate-scoped repair. Transferred outcome history ranks the candidate-scoped repair first and passes immediately. This demonstrates measured search-cost improvement across these two authored families (two trials to one), under explicit shared class labels and host-managed evidence transport. It does not demonstrate autonomous discovery or natural-task generalization.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_PREREG_20261001.md)
- [Amendment](THOUGHTEXPERIMENT_CROSS_FAMILY_IDEMPOTENCE_TRANSFER_V2_AMENDMENT_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_cross_family_idempotence_transfer_v2.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_cross_family_idempotence_transfer_v2_raw_20261001.json)
