# Mixed-kind variation credit on real verdicts: preregistration (2026-10-09)

Written before any run of `evaluation/substrate_capability/variation_credit_mixed_kind_v1.py`.

## Question

The v1–v3 credit gates each used concerns of a single kind (`instruction`). Credit is keyed by (family, concern kind). On one agent that handles an **interleaved stream of two kinds**, does outcome credit still correct a misordered prior for each kind, without credit learned on one kind degrading the other?

## Design

- **Boot.** A lab boot: the full seed set plus `variation_ops`, `variation_credit` and `instruction_repair_retry` loaded explicitly. The production default is unchanged.
  - Shadow read on.
  - Retries opted in for both kinds (`InstructionRetryPolicy.concern_kinds = ["instruction", "reported"]`), with at most 3 experiments per concern.
  - `OZMA_SEED_PERSIST_DISABLED=1`.
- **Corpus heard first.** The K1 list sentences from the grain promotion gates.
- **Misordered prior in both arms.** `reply_ablation.priority = 8`, which beats `cue_set_edit` (10) and `knob_edit` (15).
- **Stream**, interleaved, in this fixed order, on one agent per arm:
  1. I: "Condense the data."
  2. R: "you reform list sentences too eagerly, test whether the residual marker threshold is too low"
  3. I: "Tabulate the data."
  4. R: "... too rarely ... is too high"
  5. I: "Shorten the data."
  6. R: "... too eagerly ... is too low"
  7. I: "Alphabetise the data."
  8. R: "... too rarely ... is too high"

  Each instruction concern is steered with "Work on the <verb> data gap.". Each reported concern is filed as `SelfConcern{kind: reported}` and promoted.
- **Arms.**

  | Arm | `use_credit` | `exclude_refuted` | `credit_internal_exempt` | `exclude_inconclusive` |
  |---|---|---|---|---|
  | A | 0 | 1 | 0 | 0 |
  | C | 1 | 1 | 1 | 1 (the seed defaults) |

## Measures (per arm, per kind)

- `handled`:
  - instruction: the final turn is handled;
  - reported: the concern ends in a supported, adopted experiment.
- `experiments`.
- `false_adoptions`.
- `late_first_pick_correct`: over concerns 5–8, whether the first-picked family is the kind's working family (`cue_set_edit` for instruction, `knob_edit` for reported).

## Gates (each reported)

| Gate | Condition |
|---|---|
| M1 | `C.handled > A.handled` for instruction |
| M2 | `C.handled > A.handled` for reported |
| M3 | 0 false adoptions in C |
| M4 | `C.late_first_pick_correct >= 3` of 4 (credit learned per kind steers each kind's later first pick) |

## Caveat

There is one deterministic stream per arm, with 4 concerns per kind. A pass shows that per-kind credit works on a mixed stream. It is not an effect size.

## Outputs

`evaluation/reports/variation_credit_mixed_kind_v1_{A,C}_20261009.json` and `..._gate_20261009.json`.
