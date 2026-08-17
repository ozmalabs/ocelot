# Arousal-channel retirement (Phase 3) — RESULTS

Registered design: `AROUSAL_CHANNEL_RETIREMENT_PREREG.md`. **All 6
predictions confirmed.**

## 1. Live run (`scripts/arousal_channel_retirement_demo.py`)

```
=== Prediction 1: hostile_weight=0, coupling OFF (default), high arousal ===
kind=smalltalk (old term would have unconditionally produced barb here)

=== Prediction 1b: hostile_weight=0, coupling ON, high arousal -> NOT barb ===
kind=greeting

=== Prediction 2: hostile_weight=1, coupling ON, high arousal -> still barb ===
kind=barb

=== Prediction 4: arousal=0.0 isolation test is untouched by this phase ===
resentful kind=barb  grateful kind=greeting  (still diverge, unaffected by this phase)

=== Prediction 5: retiring the Python max-blend, arousal=0.0 case unaffected ===
kind=greeting (unaffected by max-blend retirement at the isolating arousal=0.0 case)
```

Rung-3 exact tie, recomputed (`scripts/bigville_social_experiment.py`,
Landlord↔Envier, no `social_dispositions` either way):

```
shared_bucket_count=0 -> affect_affection=0.0000 kind=smalltalk  act=topic      text='I discuss Envier.'
shared_bucket_count=3 -> affect_affection=0.3000 kind=greeting   act=greeting   text='I greet Envier.'
```

## 2. Predictions

1. **`hostile_weight≈0`, coupling OFF, high arousal → not unconditionally
   `barb`** — `PASS`. With the old term deleted and coupling never
   armed, `smalltalk` wins on `base_value` alone — the universal
   hostile-by-default is simply gone for the default (coupling-off)
   regime.
2. **`hostile_weight≈0`, coupling ON → not `barb`** — `PASS`, `greeting`.
   Confirms the SAME finding Phase 2 already established, restated here
   as the direct predecessor/successor pair to the retired term.
3. **`hostile_weight≈1`, coupling ON, same inputs → still `barb`** —
   `PASS`. The mechanism (arousal can drive hostility) is preserved; the
   UNIVERSALITY (every resident, regardless of disposition) is removed.
4. **Existing `arousal=0.0` isolation test unaffected** — `PASS`.
   Resentful/Grateful still diverge (`barb`/`greeting`) exactly as in
   `BIGVILLE_SOCIAL_EXPERIMENT_1_RESULTS.md` rung 2 — that test
   deliberately sidestepped the retired channel from the start.
5. **Max-blend retirement, `arousal=0.0` case unaffected** — `PASS`.
6. **Rung-3 exact tie, recomputed and reported as measured** — the tie
   is GONE. `shared_bucket_count=0` now resolves to `smalltalk` (not
   `barb` — the tie's hostile side no longer has a term to contribute
   at all, since coupling is off by default in this experiment script
   and the old universal channel is deleted). `shared_bucket_count=3`
   resolves to `greeting` (`FAMILIARITY_CAP`'s own warm_aff contribution,
   an untouched, pre-existing mechanism from rung 3, now simply visible
   without a competing hostile term). Neither number was adjusted to
   produce this outcome — it is the direct, mechanical consequence of
   deleting the term that caused the original tie.

## 3. Honesty notes

**Does establish**: the rung-2-diagnosed defect (a resident with ZERO
disposition information defaults to hostile speech) is now GONE for the
default, coupling-off regime — not because disposition sensitivity was
added to the default path, but because the universal, undifferentiated
channel that CAUSED the defect no longer exists. When coupling IS armed
(Phase 5's eventual live-cast regime), disposition genuinely gates the
outcome (`hostile_weight` divergence, confirmed prediction 2/3). Confirms
`decide_speech`'s Python max-blend was safely removable — its only
effect was feeding into the now-deleted term.

**Does NOT establish**: any claim about which outcome is "more correct"
psychologically — Phase 2's coupling must be armed (`coupling_on=1`) for
the disposition-sensitive path to apply at all; with coupling off (the
current default everywhere except Phase 2/3's own tests), a neutral
resident simply falls back to `base_value` alone (`smalltalk`/`greeting`
territory), which is itself a different, not-yet-evaluated default
regime. Phase 5 (live 100-cast) is where `coupling_on` would actually
need to be armed for real play. Does NOT extend coupling to target-scoped
Concepts (Phase 4).

## 4. Files

- `docs/research/psychology_affect/AROUSAL_CHANNEL_RETIREMENT_PREREG.md`
- `docs/research/psychology_affect/AROUSAL_CHANNEL_RETIREMENT_RESULTS.md` (this file)
- `bigville/seeds/bigville_speech_decide.json` +
  `bigville/bigville/seeds/bigville_speech_decide.json` (v1.2.0, both copies)
- `worlds/bigville_ocelot_adapter.py` (edited)
- `scripts/arousal_channel_retirement_demo.py` (new)
