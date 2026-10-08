# Grain-quantised knob step as default: preregistration (2026-10-08)

Written before any run of `evaluation/substrate_capability/knob_grain_promotion_v1.py`. This decides whether `VariationOp{knob_edit}.step_mode = "grain"` (tranche 10, opt-in) becomes the default.

## Corpora

| Corpus | Purpose | Contents | Signal measured beforehand (disclosed) |
|---|---|---|---|
| K1 (independent) | Promotion test | 6 "The <container> contains …" list sentences + 2 simple clauses, different nouns and verb from the tranche-10 probe | `residual_marker_count` ∈ {0, 2, 3, 4, 5, 6} (2 appears twice), `swallowed_ratio` = 0 throughout |
| K2 (regression) | Guard against losing an earlier success | The tranche-7 knob corpus (greeting, moon question, 2 garden-path sentences, centre-embedded committee sentence) | Not re-measured; in tranche 7 the fixed step was supported on it (`reform_swallowed_threshold` 0.5→0.6, reforms 1→0) |

## Arms

Per corpus there are two agents, `fixed` (`step_mode` absent) and `grain` (`step_mode="grain"`). Everything else is as in tranche 10:
- shadow read on;
- retries opted in for reported concerns;
- real child replays and the real judge;
- `OZMA_SEED_PERSIST_DISABLED=1`.

Concerns, filed in sequence on each agent:
- **K1:** (1) "you reform list sentences too eagerly, test whether the residual marker threshold is too low"; (2) "you reform list sentences too rarely, test whether the residual marker threshold is too high".
- **K2:** the tranche-7 text "you reform the topic too eagerly, test whether the threshold is too low".

## Measures

Per (corpus, arm):
- `supported`: the number of concerns ending in a supported, adopted experiment;
- `experiments`;
- `false_adoptions`.

## Promotion rule (all must hold)

| Gate | Condition |
|---|---|
| P1 | K1: `grain.supported > fixed.supported` |
| P2 | K2: `grain.supported >= fixed.supported` (no loss of the tranche-7 success) |
| P3 | `false_adoptions == 0` in every grain run |

If all three hold, `step_mode="grain"` becomes the seed default (`variation_ops`), kept only if the tranche regression shows no new failures. Otherwise it stays opt-in, and the failing gate is reported.

## Risk, stated in advance

On K2 the gated signal took only {0, 0.5}. The grain step's degenerate guard refuses a gate that fires on none of the observed values, but the tranche-7 fixed-step success was exactly such a gate (0.6 > every observed value). P2 may therefore fail. That would be a real conflict between the guard and a previously supported adoption, and it will be reported, not tuned away after the fact.

## Outputs

`evaluation/reports/knob_grain_promotion_v1_20261008.json`. The runner refuses to overwrite.
