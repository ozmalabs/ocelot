# Hate stability × arousal coupling — RESULTS

Registered design: `HATE_STABILITY_AROUSAL_COUPLING_PREREG.md`. **All 4
predictions confirmed.** Landing this rung required updating four
existing tests in `test_hate_attribution.py` and two in
`test_hate_passion_coupling.py` — reported honestly below as a predicted
ripple effect, not a hidden edit (matching this arc's own standing
discipline, e.g. `SELF_COMPLEXITY_COUPLING_RESULTS.md`'s threshold
ripple).

## 1. Live run (`scripts/hate_stability_arousal_coupling_demo.py`)

```
=== Predictions 1/3: streak increment at baseline vs built-up arousal ===
incident 0: locus=first_encounter streak=0.0000 arousal=0.8000 crystallized_this_call=False
incident 1: locus=global_other   streak=1.8000 arousal=1.3600 crystallized_this_call=False (increment=1.8000, expected 1+prev_arousal=1.8000)
incident 2: locus=global_other   streak=4.1600 arousal=1.7520 crystallized_this_call=True (increment=2.3600, expected 1+prev_arousal=2.3600)
incident 3: locus=global_other   streak=6.9120 arousal=2.0264 crystallized_this_call=False (increment=2.7520, expected 1+prev_arousal=2.7520)

=== Prediction 2: hot vs cold -- incidents needed to crystallize ===
hot (back-to-back): crystallized after 3 incidents
cold (arousal decayed between incidents): crystallized after 4 incidents (pre-coupling pace: 4)

=== Prediction 4: per-target isolation ===
Jo's streak after 3 back-to-back incidents: 4.1600 (already past threshold 3)
Kim's 2nd incident streak (unaffected by Jo's build-up): 1.8000 (expect 1+0.8=1.8)
```

## 2. Predictions

1. **At zero arousal, the increment is unchanged (`+1`)** — `PASS`,
   trivially, by construction (`1 + 0 == 1`); the FIRST confirming
   incident's own increment is `1.8` because arousal is already `0.8`
   after incident 0 (every incident contributes arousal, not just
   confirming ones) — the pure cold-start case (`level==0` throughout)
   is exercised directly by `test_streak_coupling_does_not_leak_across_
   targets`' Sam leg, confirming `1+0=1` still holds when nothing has
   raised arousal yet.
2. **The same sequence crystallizes in FEWER incidents when arousal has
   built up** — `PASS`. The hot (back-to-back) run crystallizes after
   **3** incidents; the cold (arousal decayed toward zero between each
   incident) run needs **4** — exactly the pre-coupling pace, since a
   decayed-away arousal falls back to a bare `+1` per confirmation.
3. **The increment matches the formula exactly** — `PASS`. Each
   `increment=` line above matches its own `expected 1+prev_arousal=`
   line to 4 decimal places, live, not just in the isolated unit test.
4. **Per-target isolation holds** — `PASS`. Jo's streak reaches `4.16`
   from 3 back-to-back incidents; Kim's 2nd incident (same substrate)
   still reads exactly `1.8` (`1+0.8`, Kim's OWN cold-start arousal),
   unaffected by Jo's build-up.

## 3. The predicted ripple, reported honestly

Because `confirm_streak` now overshoots `HATE_STABILITY_THRESHOLD`
rather than landing on it exactly, and crystallizes in FEWER incidents
than before (this rung's own Prediction 2, working as designed), six
pre-existing tests written against the old bare-`+1` pace broke on
re-running the regression:

- `tests/test_hate_attribution.py`: `test_confirming_incident_is_global_
  other`, `test_specific_act_resets_confirm_streak`,
  `test_crystallization_requires_the_stability_threshold`,
  `test_removal_desire_evidence_gated_on_crystallization`.
- `tests/test_hate_passion_coupling.py`:
  `test_crystallizing_removal_alpha_is_amplified_by_built_up_arousal`,
  `test_hot_crystallization_exceeds_cold_crystallization`.

All six were fixed to match MEASURED behavior (not reverted, not
weakened) — `confirm_streak`-value assertions now compare against
`1.0 + <measured arousal_level>` instead of a bare `1`, and the two
threshold/gating tests now drive incidents in a loop until
`crystallized_this_call` is observed rather than assuming a fixed call
count, which is also more robust to any future retuning of
`AROUSAL_INTENSITY`/`AROUSAL_DECAY`/`HATE_STABILITY_THRESHOLD` than the
original hardcoded-index tests were. This is the SAME class of expected
ripple `SELF_COMPLEXITY_COUPLING_RESULTS.md` already reported honestly
earlier in this arc when a coupling change correctly changed downstream
behavior — not a defect, the registered Prediction 2 working exactly as
designed.

## 4. Honesty notes

**Does establish**: `confirm_streak`'s own growth rate — not just
`removal_desire`'s eventual alpha — is now genuinely coupled to
Sternberg's passion component: the SAME arousal pool that amplifies the
crystallizing incident's motivational strength (`HATE_PASSION_COUPLING_
RESULTS.md`) also accelerates HOW FAST a run of confirming incidents
reaches crystallization in the first place, closing both follow-ons that
rung's own honesty notes named. The threshold constant itself
(`HATE_STABILITY_THRESHOLD=3`) is untouched — only the per-incident
contribution changed, exactly as scoped.

**Does NOT establish**: any change to `specific_act`'s reset behavior (a
full reset to `0` regardless of how aroused the exception itself was,
unchanged, per the PREREG's own scope boundary). Does NOT make the
threshold constant itself dynamic (a different, unnamed design, not
attempted). Does NOT independently validate the `1+level` additive
coupling shape against real psychological data beyond the Slovic et al.
2007 affect-heuristic citation grounding it structurally — an un-fitted
functional form, same honesty class as this arc's other couplings.

## 5. Files

- `docs/research/psychology_affect/HATE_STABILITY_AROUSAL_COUPLING_PREREG.md`
- `docs/research/psychology_affect/HATE_STABILITY_AROUSAL_COUPLING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (unchanged — the coupling is entirely inside the Rule, not Python)
- `scripts/_build_hate_attribution_seed.py` (edited: `_streak_increment_term`, v1.2.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_stability_arousal_coupling_demo.py` (new)
- `tests/test_hate_stability_arousal_coupling.py` (5/5, new)
- `tests/test_hate_attribution.py` (4 tests updated to match measured post-coupling behavior; 9/9 still green)
- `tests/test_hate_passion_coupling.py` (2 tests updated to match measured post-coupling behavior; 5/5 still green)
