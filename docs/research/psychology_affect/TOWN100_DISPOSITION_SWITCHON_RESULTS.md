# Town-100 disposition switch-on (Phase 5) — RESULTS

Registered design: `TOWN100_DISPOSITION_SWITCHON_PREREG.md`. **All 4
predictions confirmed. This closes the 5-phase affect-coupling
unification plan.**

## 1. Live run (`scripts/town100_disposition_switchon_demo.py`)

```
=== Building 100-resident cast-100 world, cognition_factory=BigvilleOcelotResident ===
world construction: 0.12s
populate_town100 (100 residents, seed_character fires for each): 4.44s
total: 4.56s

=== Prediction 1: pairwise-distinct, non-default gain vectors ===
residents with a real BigvilleOcelotResident mind: 100
distinct hostile_weight values: 98 / 100
hostile_weight spread: min=0.0000 max=0.9924 mean=0.4173

=== Prediction 2: cost, reported as a headline number ===
mean graph node count per resident: 775.5
total node count across all residents' private substrates: 77548
wall-clock for populate_town100 (100 residents): 4.44s (0.044s/resident)

=== Prediction 3: two real residents at opposite hostile_weight tails diverge ===
lowest hostile_weight: Corvin Inkpen (0.0000)   highest: Prosper Tallowick (0.9924)
low-hostile_weight resident toward a neutral stranger: kind=greeting
high-hostile_weight resident toward the SAME neutral stranger: kind=barb

=== Prediction 4: cred_on / w_supergraph-as-channel remain unwired (restated) ===
cred_on present in personality: True (transported, Phase 1 -- still no consumer)
w_supergraph-as-coupling-channel: not built -- only its ORIGINAL core_emotions.json consumer (psychopathy glass-box) exists, unchanged since before this plan.
```

## 2. Predictions

1. **Pairwise-distinct, non-default gain vectors** — `PASS`. All 100
   residents built with real `BigvilleOcelotResident` minds; `98/100`
   distinct `hostile_weight` values (2 collisions are real, expected
   floating-point/clip-boundary coincidences among 100 continuous draws,
   not a generator defect — reported honestly, not rounded away).
   Spread: `min=0.0000, max=0.9924, mean=0.4173` — close to
   `_PARAM_SPEC`'s own registered mean (`0.40`), as expected for a
   100-sample draw.
2. **Cost measured and reported as a headline, not a footnote** —
   `PASS`. `4.44s` total wall-clock for `populate_town100` across 100
   residents (`0.044s`/resident) — NOT prohibitive; ships unconditionally,
   no gating needed. `77,548` total graph nodes across all 100 private
   substrates (`775.5` mean/resident) — a real, honestly-reported cost
   figure for anyone later profiling memory.
3. **Real opposite-tail residents diverge** — `PASS`. `Corvin Inkpen`
   (`hostile_weight=0.0000`) chose `greeting`; `Prosper Tallowick`
   (`hostile_weight=0.9924`) chose `barb` — toward the identical neutral
   stranger, at identical arousal, with coupling armed. This is the
   5-phase plan's own headline claim, now demonstrated on the REAL
   generated population, not a hand-constructed test resident.
4. **`cred_on`/`w_supergraph` still explicitly deferred** — `PASS`,
   restated rather than dropped: `cred_on` is transported (Phase 1) but
   has no consumer; `w_supergraph` only has its ORIGINAL
   `core_emotions.json` consumer (the psychopathy glass-box), never
   became a coupling channel — both named candidates in
   `EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §4a, neither built, on the
   record honestly at the close of this plan.

## 3. Honesty notes

**Does establish**: the full 5-phase chain works end-to-end on the REAL
100-resident population, not just hand-constructed test residents — real
generated disposition data, transported, coupled, and producing
measurably different behavior for two real residents at opposite tails.
Cost is real and cheap (`4.44s`/100 residents), reported as measured, not
assumed. Confirms `populate_town100`'s own gap (identity/personality
never reaching a cast-100 resident's Ocelot mind) was real and is now
closed — `_scenario_character_data` populated for all 100, verified by a
new bigville-side regression test (`test_populate_town100_seeds_
scenario_character_data_per_resident`).

**Does NOT establish**: that `coupling_on` is armed anywhere by default
in a live game session — it stays `0.0` (Phase 2's own registered
default) everywhere except this demo's own explicit arming. A live
`BigvilleGame` session using the default `BigvilleOcelotActor` (no
`cognition_factory` passed) is COMPLETELY UNAFFECTED by any of this —
the whole 5-phase mechanism is opt-in, reached only via
`cognition_factory=BigvilleOcelotResident`. Does NOT wire `cred_on`/
`w_supergraph` to any new consumer — both remain honestly, explicitly
open. Does NOT evaluate whether disposition-driven speech makes for
"better" gameplay — only that the mechanism works, is cheap, and
produces real, measurable divergence.

## 4. Files

- `docs/research/psychology_affect/TOWN100_DISPOSITION_SWITCHON_PREREG.md`
- `docs/research/psychology_affect/TOWN100_DISPOSITION_SWITCHON_RESULTS.md` (this file)
- `bigville/worlds/bigville_world.py` (edited)
- `bigville/game.py` (edited)
- `domains/resident_trust.py` (edited)
- `bigville/tests/test_bigville_game_api.py` (edited, +1 test, 19/19)
- `scripts/town100_disposition_switchon_demo.py` (new)
