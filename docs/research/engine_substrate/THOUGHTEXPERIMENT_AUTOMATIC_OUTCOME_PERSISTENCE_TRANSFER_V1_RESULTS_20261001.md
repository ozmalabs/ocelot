# Thoughtexperiment automatic outcome persistence transfer v1 — results

**Result:** 11/11 preregistered gates pass.

The production correction hook writes outcome nodes into the training primary. A cold branch forked before correction has no records; the experience branch forked afterward inherits the graph-resident success and failure records. Neither outcome nodes nor their attributes are created or transported by the evaluation harness.

| Arm | Trials to oracle | Inherited history | First candidate | First oracle output | Oracle passes |
|---|---:|---:|---|---|---:|
| `cold` | [2, 2, 2] | [0, 0, 0] | ['episode_scoped_offer_guard', 'episode_scoped_offer_guard', 'episode_scoped_offer_guard'] | [[1, 0], [1, 0], [1, 0]] | 3/3 |
| `experience` | [1, 1, 1] | [2, 2, 2] | ['dedup_identity_fix', 'dedup_identity_fix', 'dedup_identity_fix'] | [[1, 1], [1, 1], [1, 1]] | 3/3 |

The outcome written through the normal scan path changes the later branch ranking: cold evaluation first tries an episode-scoped guard and fails `[1, 0]`, then passes on trial two; the inherited record ranks the candidate-scoped repair first and passes `[1, 1]` on trial one. This demonstrates graph-resident outcome persistence and inheritance through a native thoughtexperiment fork. It remains an authored two-family demonstration with a hand-designed outcome class and task oracle, not autonomous self-improvement or natural-task generalization.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_AUTOMATIC_OUTCOME_PERSISTENCE_TRANSFER_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_automatic_outcome_persistence_transfer_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_automatic_outcome_persistence_transfer_v1_raw_20261001.json)
