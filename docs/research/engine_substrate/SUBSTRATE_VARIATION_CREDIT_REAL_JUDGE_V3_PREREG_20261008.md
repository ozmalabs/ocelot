# Variation credit on real verdicts, v3: preregistration (2026-10-08)

Written before any run of `evaluation/substrate_capability/variation_credit_real_judge_v3.py`. Follows [v2](SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V2_PREREG_20261008.md), which passed on one sentence frame ("<Verb> the <object>.").

## Questions

1. Does the v2 result hold on **different sentence frames**: a polite imperative and a polar request?
2. Should the tranche-9 policy (`credit_internal_exempt=1`, `exclude_inconclusive=1`) become the **default**? This is decided by the promotion rule below.

## Design

- **Streams.** Each runs on one fresh full-seed agent per arm, in this fixed order.
  - F1, frame "Please <verb> the notes.", steered with "Work on the <verb> notes gap.": outline, digest, sort, index, gloss, tally
  - F2, frame "Could you <verb> the report?", steered with "Work on the <verb> report gap.": redact, excerpt, rank, outline, collate, itemise
- **Choice of frames.** The frames were chosen after a feasibility check that they file an instruction gap and that the steering phrase promotes it; the check used the verb `outline`/`redact`. The verbs were not pre-checked under these frames. A verb whose gap is not filed is skipped and reported.
- **Everything else as in v2:**
  - the prior is misordered (`reply_ablation.priority=8`);
  - retries are the agent's own, with `max_retries=2`;
  - there is no human retry;
  - `exclude_refuted=1` in every arm;
  - `OZMA_SEED_PERSIST_DISABLED=1`.
- **Arms.** A = no credit, B = per-trial credit, C = credit plus the tranche-9 policy.
- The tranche-10 changes are present in every arm: `irr_cancel_stale_retry`, and grain knob attributes, which are inert because `step_mode` is absent.

## Measures

As in v2, per arm and pooled over F1 and F2:
- handled;
- experiments;
- false adoptions;
- skipped verbs.

## Gates (each reported separately)

| Gate | Condition |
|---|---|
| G1 | `B.handled > A.handled` (replication on new frames) |
| G2 | `C.handled >= B.handled` |
| G3 | `C.experiments <= B.experiments` |
| G4 | `B.false_adoptions == 0` and `C.false_adoptions == 0` |

## Promotion rule (fixed in advance)

If G2, G3 and G4 hold here, **and** they also held in v2 (they did), then `credit_internal_exempt=1` and `exclude_inconclusive=1` become the defaults on `seeds/variation_credit.json`'s `VariationPolicy`. This is kept only if the tranche regression shows no new failures; otherwise it is reverted and reported.

If any of G2–G4 fails, the policy stays opt-in.

## Outputs

`evaluation/reports/variation_credit_real_judge_v3_{A,B,C}_{F1,F2}_20261008.json` and `..._v3_gate_20261008.json`. Runners refuse to overwrite.
