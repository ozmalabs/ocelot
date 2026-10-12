# Thoughtexperiment correction candidate surface v2 — results

**Corrected review: 9/9 gates pass.** Three fresh processes, locked to current Python/Rust sources and loaded native binary, independently enumerate the same 159 active rules and 545 candidate instances. Each enumeration preserves the primary graph and rule store. An independent corrected review confirms exact parity across workers, source/native stability, reconciliation of candidate-family totals, and exact per-rule parity with the v1 capture on shared schema fields.

| Candidate family | Instances |
|---|---:|
| `add_match_guard(control)` | 159 |
| `dedup_identity_fix` | 1 |
| `drop_match_edge` | 121 |
| `episode_scoped_offer_guard` | 1 |
| `flip_comparison` | 3 |
| `swap_term_leaf` | 260 |
| **Total** | **545** |

Only `sd_mint_quantum` receives the current task-shaped `dedup_identity_fix`. The inventory includes syntactic candidates across all 159 active rules, but it does not evaluate their task utility or safety. The correction-task ranking/transfer studies still cover only two authored families, so this refresh does not meet the four-family proposal-utility admission gate.

The initial analyzer reported 8/9 because it compared a v2-only metadata field against the older v1 schema. The [amendment](THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_AMENDMENT_20261002.md) preserves that analysis and documents the corrected comparison; the independent reviewer passes 9/9 without changing the capture.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_PREREG_20261002.md)
- [Amendment](THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2.py)
- [Initial analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_correction_candidate_surface_v2.py)
- [Corrected independent reviewer](../../../evaluation/substrate_capability/review_thoughtexperiment_correction_candidate_surface_v2.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_raw_20261002.json)
- [Initial analysis](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_20261002.json)
- [Corrected review](../../../evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_analysis_review_20261002.json)
