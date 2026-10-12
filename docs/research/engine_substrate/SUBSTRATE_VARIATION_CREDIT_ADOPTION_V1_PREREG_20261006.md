# Outcome-credited variation policy: held-out adoption gate v1 — preregistration (2026-10-06)

Plan: [RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md](RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md), WP2 and WP4.

## Question

When the substrate's own variation-choice policy (`variation_pick`, now
reading `VariationCredit` derived by graph rules from judged experiments) is
adopted, does it make later improvement episodes succeed with fewer
experiments, on held-out concerns, under the P3-E1 decision rule?

This is a second-order measurement: the thing being improved is the process
that chooses how to improve.

## What is authored (disclosed)

- The experiment WORLD: each concern has a hidden fixing family drawn from a
  distribution; a trial is `supported` iff the tried family is the fixing
  one, else `refuted`. This replaces child-process dispatch and the family
  judges, which are not measured here.
- The eligible family menu: all eight VariationOps (`ALL_HEADS`; cue_set_edit
  only for `instruction` concerns).
- The harness (`domains/variation_credit_lab.py`) creates StandingConcerns and
  Experiment/SeedDelta/Run records and writes `outcome`, as the dispatcher and
  judges do.

What the substrate decides: which family to try (held Program), the credit
(graph rules), and how credit changes the next choice (held Program).

## Arms

Both arms load `variation_credit`, so both credit outcomes and both exclude a
family already refuted for the same concern.

- **pre (frozen):** `VariationPolicy.use_credit = 0`.
- **adopt (candidate):** `use_credit = 1`.

The proposal is the single attribute change `use_credit: 0 → 1`. Rollback
restores it to 0.

## Distributions (12)

Training: 8 episodes per distribution (seeds disjoint from evaluation).
Evaluation: 30 held-out concern seeds per distribution. Each held-out episode
runs on a fresh substrate that replays the identical training trials, so
held-out episodes do not learn from each other. Pairs share the hidden
fixing family.

| d | kind | fixing-family distribution |
|---|---|---|
| 1 | reply_fix | threshold_shift 0.8 |
| 2 | reply_fix | structural_edit 0.8 |
| 3 | performance | reply_ablation 0.9 |
| 4 | performance | rule_literal_edit 0.7 |
| 5 | comprehension | shape_mint 0.8 |
| 6 | comprehension | threshold_shift 0.6 |
| 7 | instruction | knob_edit 0.8 |
| 8 | instruction | structural_edit 0.9 |
| 9 | reply_fix | threshold_shift 0.5, structural_edit 0.5 |
| 10 | performance | uniform (control) |
| 11 | comprehension | knob_edit 0.9 (default already first: control) |
| 12 | instruction | uniform (control) |

Remaining mass is spread uniformly over the other eligible families.

## Score and decision rule

Score per held-out episode: `S = 100·(1 − (k−1)/(M−1))`, with k the number of
experiments until `supported` and M the number of eligible families. A
concern not fixed within M experiments scores 0. Δ_d is the paired mean
difference adopt − pre over 30 pairs.

The P3-E1 decision rule, as written in
`GENERAL_INTELLIGENCE_EXPANSION_PLAN.md`:

- 10,000 paired-bootstrap resamples, seed 20261006.
- 100,000 sign permutations, one-sided for improvement and for harm.
- Holm–Bonferroni across the 12 distributions at α = 0.05, separately for the
  improvement family and the harm family.
- **improve** iff Δ ≥ +5, bootstrap lower bound > 0, and Holm p ≤ 0.05.
- **harm** iff Δ ≤ −5, bootstrap upper bound < 0, and Holm p ≤ 0.05.
- otherwise **inconclusive**.

Gate: ≥ 8/12 improve; 0 harm; aggregate mean Δ ≥ 5 with distribution-level
bootstrap lower bound > 0. Every non-improve distribution must roll back to a
byte-identical graph (`graph_to_dict` digest equal to the pre snapshot).

Predicted: d10–d12 inconclusive.

## Descriptive extras

- **Interference:** retrain d1 then d2 (same kind), then re-evaluate d1.
- **Recovery:** evaluate d2 after training on d1 only. This measures how
  stale credit costs under a shift.

## Not a P3-E1 pass

P3-E1 requires signed P2/P0/P1 custody evidence, real toy-domain tasks,
retention across 12 sequential shifts, and an independent evaluator. None of
that exists here. This applies P3-E1's statistics to a graph-level policy
adoption in an authored experiment world.
