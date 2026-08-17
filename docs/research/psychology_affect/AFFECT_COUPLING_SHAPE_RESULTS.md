# Affect-coupling shape (Phase 2) — RESULTS

Registered design: `AFFECT_COUPLING_SHAPE_PREREG.md`. **All 9 predictions
confirmed** (as originally designed — but predictions 6 and 9 encoded a
design choice the user correctly identified as wrong; see the correction
below, made during Phase 3, before this doc's own numbers were converted).

## 0. CORRECTION (made during Phase 3, not silently applied)

**The original design was wrong, not just under-tuned.** Predictions 6/9
below tested and confirmed that a `gain_cap=2.0` clamp made it
architecturally IMPOSSIBLE for any disposition, however extreme, to
override a real relationship. The user's objection, verbatim: *"A maxed
gain SHOULD flip a relationship though - also how is it maxed, that's a
violation of the principle."* Both halves are correct:

1. **`gain_cap=2.0` was itself an invented, undocumented, ungrounded
   number** — exactly the "hand-tuned coefficient per decision" anti-
   pattern this whole 5-phase plan exists to eliminate. It had no
   citation, no derivation, nothing behind it except "seemed safe."
2. **A hard architectural override-guarantee ("disposition can never
   beat evidence, no matter how extreme") contradicts the design doc's
   own §3b tails evidence** — psychopathy, mania, and the vmPFC/somatic-
   marker literature all describe REAL cases where an extreme
   disposition/mood state DOES override normal relationship-based
   restraint. Architecturally guaranteeing it never can, regardless of
   magnitude, is not a neutral safety choice; it is smuggling a
   substantive psychological claim into the engine as an unstated
   constant.

**Fix, landed in Phase 3** (`scripts/_build_affect_coupling_seed.py`,
`worlds/bigville_ocelot_adapter.py`): `gain_cap` REMOVED entirely, not
raised. Every trait `psi_resolve_disposition_gains` normalises is already
drawn via `_draw_clip` against an explicit `[0,1]` bound
(`bigville_town100_world.py::_PARAM_SPEC`), so a REAL, population-drawn
resident's gain is ALREADY naturally bounded (`hostile_gain <= 1.0/0.40 =
2.5`) with no extra clamp needed. A deliberately out-of-population value
(a genuine tail case) now produces a genuinely unbounded gain, and WHICH
side wins — disposition or real relationship history — is decided by the
actual relative magnitudes at `Sum`-time, never pre-decided by this rule.
Re-verified: a natural-population-max resident (`hostile_weight=1.0`,
gain `2.5`) still does NOT flip a moderate real relationship; a
pathological one (`hostile_weight=5.0`, gain `12.5`) DOES — see the
corrected §1 transcript and §2 predictions 6/9 below, both updated in
place with the new live output (this is current, reproducible behavior
being reported accurately, not a historical measurement being converted
— the narrative analysis in §2 is kept alongside, not deleted).

## 1. Live run (`scripts/affect_coupling_demo.py`)

```
=== Prediction 1: same rule couples SpeechOption AND Concept generically ===
Concept affect_bias=0.4000  SpeechOption(barb) affect_bias=0.4000

=== Prediction 2: coupling_on=0 -> affect_bias stays 0.0 ===
barb affect_bias=0.0000 (coupling never armed)

=== Prediction 3: untagged node -> affect_bias == 0.0 exactly ===
untagged affect_bias=0.0000

=== Prediction 4: disposition/arousal isolation ===
identical arousal=0.4: hostile_weight=0.0 -> barb=0.0000, hostile_weight=0.8 -> barb=0.4000
identical hostile_weight=0.4: arousal=0.0 -> barb=0.0000, arousal=0.9 -> barb=0.4500

=== Prediction 5: population-mean resident -> gains exactly neutral ===
reactivity_gain=1.0000 hostile_gain=1.0000 warmth_gain=1.0000 trait_valence=0.0000 mood_bias=0.0000

=== Prediction 6 (CORRECTED -- relative magnitude decides, not a cap) ===
hostile_gain=0.0000
real feud relationship -> kind=barb
natural-population-max hostile_gain=2.5000, moderate real warmth -> kind=greeting
out-of-population hostile_gain=12.5000, SAME moderate real warmth -> kind=barb

=== Prediction 7: settling order -- first and second call agree ===
first=0.5000 second=0.5000 match=True

=== Prediction 8: missing reference mean -> Div-by-zero -> gain silently 0 ===
hostile_gain=0.0000 (expect 0.0, fail-quiet)

=== Prediction 9 (CORRECTED -- natural bound, no cap) ===
hostile_weight=1.0 (_draw_clip's own max) -> hostile_gain=2.5000 (natural bound, unclamped)
hostile_weight=5.0 (out-of-population) -> hostile_gain=12.5000 (genuinely unbounded)
```

## 2. Predictions

1. **Genericity** — `PASS`. The unmodified `psi_couple_affect_to_tagged`
   rule produced IDENTICAL `affect_bias=0.4000` on a throwaway `Concept`
   and on the `barb` `SpeechOption` (both `affinity_hostile=1.0`) in one
   fixpoint — `MatchEdge`'s type-agnostic endpoints (`rewrite.rs:31`)
   confirmed live, not just in source.
2. **Off by default** — `PASS`. `barb` stays `0.0000` with `coupling_on`
   never armed, byte-identical to Phase 1.
3. **Untagged ⇒ zero** — `PASS`, exactly `0.0000`. Confirms the `P0`
   guard is doing its job everywhere it's needed.
4. **Disposition/arousal isolation** — `PASS`, both directions. At
   identical arousal (`0.4`), `hostile_weight` alone moved `barb` from
   `0.0000` to `0.4000`. At identical `hostile_weight` (`0.4`), arousal
   alone moved it from `0.0000` to `0.4500`. Neither channel alone
   explains both divergences — confirmed, not asserted.
5. **Population mean is neutral** — `PASS`, all three gains exactly
   `1.0000`, both additive channels exactly `0.0000`.
6. **`PASS` as originally worded, but RETRACTED — see §0.** Originally:
   "additive, never overriding." A real feud relationship
   (`strength=-2.0`) still routed `barb` with `hostile_gain` forced to
   `0.0000` — that half stands (the EXISTING, untouched `affect_gain ×
   resentment × hostile_aff` term carried it, unrelated to this phase's
   own channel). But the SECOND half — "a maxed `hostile_gain=2.0000`
   did NOT flip a strongly-warm real relationship, real relationship
   history dominates the coupling channel in both directions, AS
   DESIGNED" — encoded an architectural override-guarantee the user
   correctly rejected. **Corrected**: a natural-population-max
   `hostile_gain=2.5000` (uncapped) still does NOT flip a MODERATE real
   relationship (`strength=1.0`) — but an out-of-population
   `hostile_gain=12.5000` DOES, against the SAME relationship. Who wins
   is decided by relative magnitude, never architecturally pre-decided.
7. **Settling order** — `PASS`. First-ever and second `decide_speech`
   calls on a fresh resident read the identical settled bias
   (`0.5000 == 0.5000`) — the unarmed-settle-then-arm fix works.
8. **Fail-quiet gain caught** — `PASS`, exactly `0.0000` when
   `hostile_ref` is zeroed — `Div`'s fail-quiet-to-`0.0` behavior
   (`term.rs:7711`) confirmed live and now has an explicit regression
   test guarding it, not just a documented risk.
9. **`PASS` as originally worded, but RETRACTED — see §0.** Originally:
   "gain cap clamps," raw ratio `1.0/0.4=2.5` clamped to an invented
   `gain_cap=2.0000`. **Corrected**: no cap exists. `hostile_weight=1.0`
   (the population's own natural max) now correctly yields the
   UNCLAMPED `hostile_gain=2.5000`; an out-of-population
   `hostile_weight=5.0` correctly yields `12.5000` — genuinely
   unbounded, as it should be.

## 3. A real, pre-existing gap found and fixed en route

Writing the isolation tests (predictions 4/6/7) surfaced two real
findings, neither hypothetical:

- **`AffectiveState.arousal` is continuously RECOMPUTED by `core_emotions.
  json`'s own rules from Appraisal/ModulatorState** — a direct
  `set_attr` on it gets silently clobbered back to a formula-derived
  value on the next `run_rules()` once `core_emotions` is loaded. This is
  a real, pre-existing fact about the ALREADY-BUILT emotion system, not
  something this phase changed. Isolation tests that need a KNOWN,
  externally-controlled arousal value must build residents with
  `emotional_core_enabled=0.0` (the boot-seeded `AffectiveState` — always
  present via `affective_state_core` in `boot_core.CORE_SEEDS` — stays
  externally settable only when `core_emotions`'s own recompute rules are
  never loaded). Documented directly in `tests/test_affect_coupling.py`'s
  own `_resident`/`_set_arousal` helpers rather than worked around
  silently.
- **`_ensure_speech_graph` could not run standalone** (without
  `_ensure_emotional_core` having run first) — it called
  `_prepare_bigville_imports()` assuming `BIGVILLE_ROOT` was already on
  `sys.path`, but that insertion only happened inside
  `_ensure_emotional_core`. Every PRIOR test happened to call
  `seed_character(personality={"emotional_core_enabled": 1.0, ...})`
  first, papering over this. Fixed by adding the same `sys.path`
  bridge directly to `_ensure_speech_graph`, matching
  `_ensure_emotional_core`'s own pattern — a real, small, pre-existing
  gap this phase's own bare-mode test coverage was the first to expose.

## 4. Honesty notes

**Does establish**: a working, generic, graph-shape-matched coupling
mechanism — confirmed to fire identically across two different node
types, confirmed off by default, confirmed additive, confirmed to
correctly fail quiet rather than silently succeed wrong on missing
configuration. Zero new Rust, per the plan's own bar. Fixed two real,
independently-discovered, pre-existing gaps (the arousal-recompute fact,
the standalone-import gap) as a direct byproduct of writing genuinely
isolating tests, not hypothesized in advance. **Additionally establishes,
via the §0 correction**: relative magnitude — not an architectural cap —
correctly decides whether disposition or real relationship history wins,
matching the design doc's own tails evidence instead of contradicting it.

**Does NOT establish**: any change to `sp_choose_utterance`'s existing
hand-patched arousal term (Phase 3 — both channels coexist additively
this phase). Does NOT extend coupling to any target-scoped Concept
(Phase 4). Does NOT run against a live 100-cast population (Phase 5).
Does NOT claim the reference means are empirically calibrated —
registered normalizations against the generator's own drawn means, a
weaker claim than a fit. No longer claims a `gain_cap` at all — REMOVED,
not tuned, per §0.

## 5. Files

- `docs/research/psychology_affect/AFFECT_COUPLING_SHAPE_PREREG.md`
- `docs/research/psychology_affect/AFFECT_COUPLING_SHAPE_RESULTS.md` (this file)
- `scripts/_build_affect_coupling_seed.py` (new)
- `seeds/affect_coupling.json` (new, generated, 2 rules)
- `worlds/bigville_ocelot_adapter.py` (edited: channel rows, seed
  loading, `_ensure_speech_graph` tagging + standalone-import fix,
  `decide_speech` settling-order fix)
- `bigville/seeds/bigville_speech_decide.json` +
  `bigville/bigville/seeds/bigville_speech_decide.json` (bigville repo,
  v1.1.0, both copies)
- `tests/test_affect_coupling.py` (new, 11/11)
- `scripts/affect_coupling_demo.py` (new)
