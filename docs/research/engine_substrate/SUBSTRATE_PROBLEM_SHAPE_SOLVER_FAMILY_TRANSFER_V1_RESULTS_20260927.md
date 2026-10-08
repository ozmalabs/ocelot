# ProblemShape solver-family transfer v1 results

## Integrity and outcome

Two fresh workers ran against the immutable, source-locked snapshot. All registered integrity gates pass: parent pre/post locks match; both workers use the same read-only snapshot lock; the full seed profile loads 731 manifests with the same 11 reported failures; and the independent analyzer verifies raw/lock and runner/analyzer hashes. All eight underlying solver Goals per worker resolve through the registered paths.

The seeded exact-CAN positive control is recognized as `ps_has_targets_mt=yes` without a mint. The bridge results repeat exactly across both workers:

| Observation | Initial status | Final status | Shape coverage | Mint delta |
|---|---|---|---|---:|
| First `can_to_deduction` Goal | residual | recognized after recurrence | `ps_has_direction=can_to_deduction_has_targets_mt=yes` | 0 |
| Second `can_to_deduction` Goal | recognized | recognized | same acquired shape | 1 |
| Third, held-out resident | recognized | recognized | same acquired shape | 0 |
| Opposite `deduction_to_can` Goal | residual | residual | none | 0 |

The first two distinct resident networks establish recurrence; the third different settled network transfers to the minted shape. The opposite-direction Goal also resolves, but its different structural signature remains residual and does not cause another mint. The full schedule is replicated in both independent processes.

## Operation and resource measurements

Full seed indexing/boot takes 11.86 and 11.93 s wall (13.17 and 13.18 s process CPU), before counting Python import startup. Each process reports a 1.754 GiB peak RSS. Per-observation medians/ranges in this two-worker panel span 13.04–17.28 ms wall; these are instrumented observation calls, not uninstrumented service latency. ProblemShape candidate-pair / Term-evaluation counts repeat exactly by stage: seeded exact 7/71; first bridge 16/139; recurrence/minting bridge 36/540; held-out bridge 28/195; opposite-direction control 40/289. This is a single small graph and does not support an asymptotic inference or a locality claim.

## Interpretation and limits

This is evidence that the current ProblemShape path can acquire one real solver Goal structure from recurrence, re-decode its first residual, reuse it on a third settled CAN instance, and leave an opposite-direction solver Goal distinct. It extends prior schema-induction results beyond CAN relax/BP to the real reasoning bridge interface. It does not validate whether the bridge's inferred predications are factually correct, show downstream task benefit, estimate how often natural work enters this rung, or establish general concept invention. Full-seed boot dominates measured observation work in this small sample; application-versus-acquisition economics remain a separate question.

## Artifacts

- [Preregistration](SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_problem_shape_solver_family_transfer_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_problem_shape_solver_family_transfer_v1.py)
- [Runtime lock](../../../evaluation/substrate_capability/problem_shape_solver_family_transfer_v1_lock_20260927.json)
- [Raw workers](../../../evaluation/reports/problem_shape_solver_family_transfer_v1_20260927.json)
- [Analysis](../../../evaluation/reports/problem_shape_solver_family_transfer_v1_analysis_20260927.json)
