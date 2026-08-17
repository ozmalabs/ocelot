# Disposition transport (affect-coupling Phase 1) — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`, designed
by an Opus Plan agent that read the actual DSL/Rust sources before
proposing anything — see the plan's own investigation notes — reviewed
and spot-checked against `runners/dsl/src/{term,rewrite}.rs` before
approval). Phase 1 of 5 resolving
`EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §5.

## Goal

Every `_PARAM_SPEC` disposition trait (13 keys,
`bigville/worlds/bigville_town100_world.py`) reaches a
`BigvilleOcelotResident`, with **zero new rules** — pure transport. The
traits with an ALREADY-EXISTING consumer (`mood_bias` → `em_happiness`)
should start moving behavior; everything else should land inertly, a
deliberate, falsifiable null confirming transport is separable from
consumption.

## Design

- `_can_params` (`worlds/bigville_ocelot_adapter.py`) extended with
  `cred_on`/`valence` — the 2 of 13 keys it was missing.
- New `_disposition_traits(profile)` — same resolution as `_can_params`,
  exposed under its own name (disposition-transport and CAN-builder
  callers are legitimately separate consumers of the same drawn data).
- New `_ensure_affect_coupler(profile)` — idempotent `AffectCoupler` node
  per resident, `has_affect_coupler` edge from the agent, `reads_affect`
  edge to the boot-seeded `AffectiveState` every resident already has
  (`affective_state_core` is in `boot_core.CORE_SEEDS` — confirmed, not
  assumed). Carries the additive channels used directly (`mood_bias`,
  `trait_valence`) and the raw inputs to a NOT-YET-BUILT normalization
  rule (`trait_arousal`, `trait_hostile_weight`, `trait_charm_weight`,
  `trait_w_spite`, `trait_cred_on`), plus neutral gain defaults
  (`reactivity_gain`/`hostile_gain`/`warmth_gain` = 1.0) and registered
  reference means (`arousal_ref=0.40`, `hostile_ref=0.40`,
  `charm_ref=0.50`, `gain_cap=2.0`).
- New `_apply_generated_dispositions()` — when `personality["self_priors"]`
  is present: (a) copies `ingroup_affinity`/`outgroup_suspicion` directly
  onto `personality` so `_speech_bond`'s EXISTING fallback read
  (`personality.get("ingroup_affinity", 0.4)`) sees the real generated
  value instead of always defaulting; (b) calls the EXISTING
  `domains/bigville_disposition_apply.apply_resident_dispositions`
  (reused, not reimplemented) to mint real target-scoped Concepts for
  people/groups/self, defaulting any missing identity bucket
  (`class`/`group`/`role`/`workplace_kind`) to `"unspecified"` rather
  than raising.
- `seeds/affect_coupling.json` deliberately NOT created this phase — the
  `AffectCoupler` node is minted directly in Python, matching the
  EXISTING precedent in this exact file (`HeldEmotionParams`/
  `Appraisal`/`ModulatorState`/`AffectiveState` are all minted the same
  way, not from a seed's `nodes` section). The seed file's real content
  starts in Phase 2 (the two rules) — an empty placeholder file with no
  rules would be dead weight.

## Predictions

1. Two residents differing ONLY in `mood_bias`, given the identical
   `record_action_outcome(action="help", applied=True)` input, diverge in
   `appraisal.happiness` AND `appraisal.total_value` — via the
   ALREADY-EXISTING `em_happiness`/`em_fulfilment_value` rules, zero new
   rule code.
2. All 13 `_PARAM_SPEC` keys present as `personality_<key>` on the agent
   AND on the `AffectCoupler`'s own attrs — enumerated by name.
3. `w_spite`/`cred_on`/`valence` transport (confirmed present, differing
   between residents) but change NOTHING in the appraisal outcome — a
   deliberate null.
4. A real generated `ingroup_affinity` (from `self_priors`) differs from
   the hardcoded `0.4` fallback in `_speech_bond`'s output, at a
   magnitude below `FAMILIARITY_CAP` so the comparison isn't masked by
   the cap.
5. A real seeded `social_dispositions` entry still wins outright over
   bucket familiarity — the existing mutually-exclusive branch structure
   in `_speech_bond` is untouched.
6. A generated backstory (self_priors + bonds) applies via the EXISTING
   `apply_resident_dispositions`, producing the expected count of real
   `TargetPattern` nodes (person + 4 own buckets + 1 out-group bucket).

## What this explicitly does NOT establish

No new rule exists yet — `coupling_on` stays `0.0`, `reactivity_gain`/
`hostile_gain`/`warmth_gain` stay at their neutral `1.0` default forever
in this phase. Does NOT touch `decide_speech`'s existing arousal
max-blend (Phase 3). Does NOT tag any `SpeechOption`/Concept with
`affinity_*` (Phase 2/4). Does NOT run on a live `populate_town100` cast
(Phase 5).

## Files

- `worlds/bigville_ocelot_adapter.py` (edited)
- `tests/test_disposition_transport.py` (new)
- `docs/research/psychology_affect/DISPOSITION_TRANSPORT_PREREG.md` (this file)
- `docs/research/psychology_affect/DISPOSITION_TRANSPORT_RESULTS.md` (paired)
