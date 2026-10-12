# Variation credit on real verdicts, v1: preregistration (2026-10-08)

Written before any run of `evaluation/substrate_capability/variation_credit_real_judge_v1.py`.

## Question

When the agent's prior over variation families is wrong, does outcome credit learned from **real** judged experiments (two independent child boots, the corrected judge) correct it within one stream of problems? The tranche 1–2 credit gates used a simulated judge.

## Design

- **Problems:** a stream of 5 unhandled instruction verbs on ONE agent, in this order: `condense, tabulate, shorten, alphabetise, paraphrase`. Each verb: "<Verb> the data." files a gap; "Work on the <verb> data gap." steers it into a promoted concern. Retries are the agent's own (`irr_request_retry`, `max_retries=2`, so at most 3 experiments per verb). No human retry.
- **Competing families** for an `instruction` concern: `cue_set_edit` (held priority 10) and `reply_ablation` (20).
- **Misordered prior (both arms):** the agent's own `VariationOp{reply_ablation}.priority` is set to 8, so the prior prefers the family expected to be wrong for a routing gap. This is a data edit on the probe agent only.
- **Arms:** `OFF` = `VariationPolicy.use_credit=0`; `ON` = `use_credit=1`. Both keep `exclude_refuted=1`. Same corpus, same order, separate boots.
- `OZMA_SEED_PERSIST_DISABLED=1`. n = 1 stream per arm.

## Measures

- `experiments`: total real child experiments to process the stream.
- `handled`: verbs whose final "<Verb> the data." is handled (not the gap floor, not the error surface).
- `first_pick_cue`: verbs whose first experiment used `cue_set_edit`.
- `false_adoptions`: an adoption whose verdict was not supported, or an adopted verb that is not handled afterwards.

## Gate (all must hold)

1. `ON.handled >= OFF.handled`
2. `ON.experiments < OFF.experiments`
3. `ON.false_adoptions == 0`

Expected mechanism if it passes: after `reply_ablation` fails on the first verb, its credit factor 2(t−s+1)/(t+2) exceeds 10/8 and later verbs try `cue_set_edit` first. If `reply_ablation` turns out to be *supported* on these gaps, the gate measures something else, and the result is reported as found.

## Reporting

The report goes to `evaluation/reports/variation_credit_real_judge_v1_20261008.json` (the runner refuses to overwrite). A failure is reported as a failure. This is n = 1 per arm: a pass shows that credit learned from real verdicts can steer the pick, not an effect size.
