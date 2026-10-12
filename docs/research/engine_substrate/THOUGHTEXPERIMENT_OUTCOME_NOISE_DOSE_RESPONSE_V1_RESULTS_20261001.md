# Thoughtexperiment outcome noise dose-response v1 — results

**Result:** 9/9 preregistered gates pass.

All conditions fork from the same production-trained primary. The false-positive dose adds one or two positive rows for the known-bad episode guard; the false-negative condition changes the genuine candidate-scoped success to zero utility; mixed noise applies both interventions. These are controlled sensitivity conditions, not natural error-rate samples.

| Arm | History rows | First candidate | Prior successes / failures | First oracle output | Trials to success |
|---|---:|---|---|---|---:|
| `clean` | [2, 2, 2] | ['dedup_identity_fix', 'dedup_identity_fix', 'dedup_identity_fix'] | [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0)] | [[1, 1], [1, 1], [1, 1]] | [1, 1, 1] |
| `false_positive_1` | [3, 3, 3] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0)] | [[1, 0], [1, 0], [1, 0]] | [2, 2, 2] |
| `false_positive_2` | [4, 4, 4] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [(2.0, 0.0), (2.0, 0.0), (2.0, 0.0)] | [[1, 0], [1, 0], [1, 0]] | [2, 2, 2] |
| `false_negative_1` | [2, 2, 2] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)] | [[1, 0], [1, 0], [1, 0]] | [2, 2, 2] |
| `mixed` | [3, 3, 3] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [(1.0, 0.0), (1.0, 0.0), (1.0, 0.0)] | [[1, 0], [1, 0], [1, 0]] | [2, 2, 2] |

Interpretation is limited to this candidate pair and task. Compare the false-positive 1/2 arms for saturation, and false-negative/mixed arms for the effect of removing reliable positive evidence. The panel neither estimates natural noise prevalence nor supports broad learning claims.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_OUTCOME_NOISE_DOSE_RESPONSE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_outcome_noise_dose_response_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_outcome_noise_dose_response_v1_raw_20261001.json)
