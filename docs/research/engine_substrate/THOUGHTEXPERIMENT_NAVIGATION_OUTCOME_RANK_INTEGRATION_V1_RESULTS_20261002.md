# Navigation outcome-ranker integration v1 — results

**Independent review: 13/13 outcome and integrity checks pass.** Three fresh, source/native-locked workers integrated the navigation correction candidates with the production `rank_candidates` function and the graph-authored `self_correct_rank_*` Program. Training used Up and Left; held-out evaluation used Down and Right. The unchanged generator emitted six variants. The successful `flip_comparison` edit passed both training and both held-out directions; all five other candidates failed the two held-out cases.

| Policy | First candidate | First-candidate held-out utility | Attempts to pass both held-out cases |
|---|---|---:|---:|
| Default generator order | `flip_comparison` | 1.0 | 1 |
| Cold graph rank, zero outcomes | `swap_term_leaf:_adist->flood_epoch` | 0.0 | 2 |
| Graph rank with candidate-specific training outcomes | `flip_comparison` | 1.0 | 1 |

The cold graph ranker's structural-cost preference creates a measured first-candidate error. Candidate-specific `CorrectionOutcome` records from disjoint training directions reverse that ordering, and experience rank reduces attempts from two to one versus the cold ranker in all three workers. It ties the unchanged default order, which already starts with the successful candidate. This shows the graph-resident rank Program can consume outcome records and improve on its own cold structural-cost policy within this family; it does not show benefit over the task's default order, cross-family transfer, autonomous outcome collection, or candidate generation. The host still enumerates candidates and transports typed records. The four-family utility gate remains unmet.

The runner omitted the preregistered per-policy ordering latency. This was found during audit and is documented in the [capture amendment](THOUGHTEXPERIMENT_NAVIGATION_OUTCOME_RANK_INTEGRATION_V1_AMENDMENT_20261002.md). The source-locked capture is preserved unchanged; no post-hoc timing is supplied. Candidate attempts and held-out utility remain measured, but the capture cannot support a full cost or economic comparison.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_NAVIGATION_OUTCOME_RANK_INTEGRATION_V1_PREREG_20261002.md)
- [Capture amendment](THOUGHTEXPERIMENT_NAVIGATION_OUTCOME_RANK_INTEGRATION_V1_AMENDMENT_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_navigation_outcome_rank_integration_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/thoughtexperiment_navigation_outcome_rank_integration_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_raw_20261002.json)
- [Independent review](../../../evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_analysis_review_20261002.json)
