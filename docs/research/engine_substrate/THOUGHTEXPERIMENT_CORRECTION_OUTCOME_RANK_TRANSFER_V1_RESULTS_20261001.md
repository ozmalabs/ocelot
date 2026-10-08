# Thoughtexperiment correction outcome rank transfer v1 — results

**Result:** 8/8 preregistered gates pass.

Three fresh workers each ran a training episode followed by cold and experience-informed episodes on distinct substrate instances. The training candidates actually tried produced typed outcome records, including the adopted successful repair and a failed rehearsal. The transfer arm received those records as `CorrectionOutcome` graph nodes before ranking; host code transported evidence but did not select the candidate.

| Arm | Attempts | Median | Candidate order | Held-out passes |
|---|---|---:|---|---:|
| `cold_rank` | [2, 2, 2] | 2 | [['swap_term_leaf:signature->residual', 'dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:key->signature'], ['swap_term_leaf:signature->residual', 'dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:key->signature'], ['swap_term_leaf:signature->residual', 'dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:key->signature']] | 3/3 |
| `experience_rank` | [1, 1, 1] | 1 | [['dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:signature->residual', 'swap_term_leaf:key->signature'], ['dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:signature->residual', 'swap_term_leaf:key->signature'], ['dedup_identity_fix', 'add_match_guard(control)', 'swap_term_leaf:signature->key', 'swap_term_leaf:signature->name', 'swap_term_leaf:signature->residual', 'swap_term_leaf:key->signature']] | 3/3 |

The result tests outcome-conditioned ordering on repeated instances of one authored correction family. It is evidence that typed prior outcomes can alter a graph-authored rank Program's ordering on fresh graph instances; it is not autonomous memory acquisition, general learning, or evidence of broad task utility. Candidate attempts and held-out correctness are more interpretable here than timing.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CORRECTION_OUTCOME_RANK_TRANSFER_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_correction_outcome_rank_transfer_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_outcome_rank_transfer_v1_raw_20261001.json)
