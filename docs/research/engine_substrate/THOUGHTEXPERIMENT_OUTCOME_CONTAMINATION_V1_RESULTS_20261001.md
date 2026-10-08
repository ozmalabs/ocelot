# Thoughtexperiment outcome contamination v1 — results

**Result:** 9/9 preregistered gates pass.

A production correction wrote two authentic outcomes. The treatment then received one deliberately misattributed positive outcome for the episode-scoped guard, whose staged-task oracle suppresses the later valid candidate. This tests sensitivity to one false positive; the perturbation is an explicit evaluation intervention, not a naturally observed record.

| Arm | Inherited records | First candidate | First oracle output | Trials to oracle |
|---|---:|---|---|---:|
| `clean` | [2, 2, 2] | ['dedup_identity_fix', 'dedup_identity_fix', 'dedup_identity_fix'] | [[1, 1], [1, 1], [1, 1]] | [1, 1, 1] |
| `contaminated` | [3, 3, 3] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [[1, 0], [1, 0], [1, 0]] | [2, 2, 2] |

Interpretation is limited to this authored candidate pair and task. If the contaminated arm regresses, one false positive can overturn useful transfer under the current ranking policy; the study does not estimate how often such records arise. Both arms are required to eventually pass the independent oracle, and all rehearsal branches must preserve their primary state.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_OUTCOME_CONTAMINATION_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_outcome_contamination_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_outcome_contamination_v1_raw_20261001.json)
