# Thoughtexperiment correction candidate surface audit v1 — results

**Result:** 5/5 preregistered gates pass.

Across three fresh processes, the standard core fixture exposes 159 active rules and 545 candidate instances. The generic generator returns at least one candidate for 159 rules, but only 1 rule has the current task-shaped `dedup_identity_fix` candidate.

| Candidate family | Count |
|---|---:|
| `add_match_guard(control)` | 159 |
| `dedup_identity_fix` | 1 |
| `drop_match_edge` | 121 |
| `episode_scoped_offer_guard` | 1 |
| `flip_comparison` | 3 |
| `swap_term_leaf` | 260 |

The audit now includes a plausible episode-scoped recurrence guard beside the candidate-scoped repair. The later staged two-candidate oracle shows why generation is not validation: episode-scoped suppression yields offer counts [1, 0], while the candidate-scoped repair yields [1, 1]. This read-only surface inventory itself measures no applicability, convergence, task preservation, or adoption safety; those properties require the separate task-specific thoughtexperiment panels.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v1_raw_20261001.json)
