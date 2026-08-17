# Target-scoped beliefs reach decide_speech (Phase D) — PREREG

## Context

The first opus design-review pass named Phase D narrowly: *"target-scoped
`affect_bias`/`spite_gain` have no real production consumer either."*
Investigating both threads found the deeper gap the user then asked to
close fully:

- `spite_gain` (a resident's own computed AffectCoupler gain,
  `psi_resolve_disposition_gains`) has a real, correct consumer signature
  — `domains/hate_attribution.py::record_hate_incident`'s `spite_gain`
  parameter is genuinely multiplied into `effective_removal_alpha`. But
  grepping every caller across the whole tree (every test file, every demo
  script, `bigville_social_experiment.py`) found **zero** real callers
  threading a resident's own coupler value in — every one either omits it
  (default `1.0`, no effect) or hand-sets a synthetic test value. And
  `worlds/bigville_ocelot_adapter.py` never calls `record_hate_incident` at
  all — there is no live entry point analogous to `record_action_outcome`.
- `affect_bias` on target-scoped Concepts (`regard_for`/`admiration_for`/
  `devaluation_for`/`removal_desire_for`) is genuinely dead too —
  `seeds/affect_coupling.json` is the only seed in the tree that even
  mentions `affect_bias`.
- **The deeper finding**: even the underlying BELIEF (`external_field` —
  the crystallized regard/admiration/devaluation state itself, not just its
  disposition-coupled bias) is never read by `decide_speech`. Tracing
  `_speech_bond`'s `elif profile:` branch found it reads
  `self.personality["social_dispositions"][target]` — a STATIC dict,
  author-set at `seed_character` time. `seed_character`'s own loop
  ALREADY calls `mint_target_pattern` + `_apply_social_aspects` for every
  `social_dispositions` entry, which seeds the SAME `regard`/`admiration`/
  `devaluation` values onto the LIVE target-scoped Concepts as their
  INITIAL evidence — so both representations start identical. But only
  the live Concepts can evolve afterward (via a real recorded incident);
  `_speech_bond` keeps reading the frozen `t=0` snapshot forever,
  regardless of what actually happens to the relationship.

## Design

1. **`record_social_incident(target, *, negative, violation_type, base_alpha)`**
   (new method, `BigvilleOcelotResident`) — the missing connective tissue.
   Mints (idempotent) the target's `TargetPattern`, reads THIS resident's
   own `AffectCoupler.spite_gain` (1.0/neutral if coupling is off or
   unset), and calls `record_hate_incident` with it. Mirrors
   `record_action_outcome`'s own pattern exactly.
2. **`_live_target_regard(target)`** (new method) — reads
   `regard_for:<target>`/`admiration_for:<target>`/`devaluation_for:<target>`'s
   CURRENT `external_field` from this resident's own Microtheory, plus
   live trust via the same `competence_for:<target>`/`willingness_for:<target>`
   beliefs `resident_trust.read_trust` already uses. Returns `None` (not
   `{}`) when this resident holds no target-scoped belief about `target`
   at all — so `_speech_bond` falls through to the static snapshot / bucket
   familiarity exactly as before for a genuinely unknown target.
3. **`_speech_bond`'s `profile` lookup** becomes
   `self._live_target_regard(target) or self._speech_personality(target)`
   — live wins whenever it exists, matching the "relative magnitude
   decides, not an architectural override" principle already established
   in Phase 2/3. Byte-identical at `t=0` (both start from the same seeded
   evidence); genuinely diverges the moment a real incident is recorded.

## Predictions

1. `tests/test_affect_coupling.py`, `test_target_scoped_coupling.py`,
   `test_disposition_transport.py`, `test_bigville_ocelot_adapter.py` all
   pass unmodified (30/30) — the wiring is additive, not a formula change,
   so every existing scenario (none of which calls
   `record_social_incident`) is byte-identical.
2. A resident seeded with `social_dispositions={target: {"regard": 0.3}}`
   produces an IDENTICAL `decide_speech` outcome at `t=0` whether read from
   the static snapshot or the live Concept (they hold the same value by
   construction).
3. After several real `record_social_incident(target, negative=True)`
   calls that crystallize hate, the SAME resident's `decide_speech(target)`
   outcome CHANGES — while `self.personality["social_dispositions"][target]`
   remains completely unchanged (proving the read is genuinely live, not a
   second copy of the same static data).
4. Broader hate/social regression (`test_hate_attribution.py`,
   `test_admiration_gratitude.py`, `test_contempt.py`,
   `test_resident_trust.py`, `test_envy.py`, `test_self_efficacy.py`,
   `test_shared_arousal_excitation_transfer.py`,
   `test_bigville_disposition_apply.py`) stays green — `hate_attribution.py`
   itself is untouched; only a NEW caller was added in the adapter.
5. bigville's own 211-test suite is unaffected (this phase is entirely
   ocelot-adapter-side; no bigville file touched).

## Does NOT claim

Does not claim any REAL bigville gameplay path currently calls
`record_social_incident` — this phase builds the connective tissue and
proves it works end-to-end when called, matching the pattern
`record_action_outcome`/`supergraph_contribution` established in Phase A
(the adapter method existed before bigville's own `held_board_games.py`
was wired to call it). Wiring a real bigville event (a dispute, a broken
promise, a witnessed harm) to actually CALL `record_social_incident` is a
further, separate rung — named, not built here. Does not change
`hate_attribution.py`'s own mechanics at all.
