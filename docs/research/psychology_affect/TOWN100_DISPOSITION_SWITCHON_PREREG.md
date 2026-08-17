# Town-100 disposition switch-on (Phase 5) — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`). Phase 5
of 5, the last phase, resolving `EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md`
§5. Builds on Phases 1-4, all confirmed (Phase 2's `gain_cap` corrected
mid-Phase-3, `AFFECT_COUPLING_SHAPE_RESULTS.md` §0).

## Goal

Wire the live 100-cast population to actually use everything Phases 1-4
built. Confirmed gap (this session's own investigation, into a real
Explore agent's finding): `populate_town100` never populated
`_scenario_character_data` — only `from_scenario()` did — so a cast-100
resident's own drawn `_PARAM_SPEC` params (already flattened onto that
resident's bigville-side graph node via `traits=`) never reached an
Ocelot `cognition_factory`'s `seed_character` at all. Sequenced last
because of measured blast radius: 100 residents × a full
`_ensure_emotional_core` boot each.

## Design

- `bigville/worlds/bigville_world.py::populate_town100` — populates
  `_scenario_character_data[record["name"]]` (identity: role/class/
  group; personality: the full 13-key `record["params"]` +
  `emotional_core_enabled: 1.0` set EXPLICITLY, not left to
  `seed_character`'s own silent default) BEFORE calling `add_actor` —
  `add_actor` itself reads this dict internally to seed a
  `cognition_factory`'s mind.
- `bigville/game.py::_characters_from_world` — the personality attr
  filter gains `cred_on`/`valence`/`resolution_bins` (previously
  dropped) — matters for callers OTHER than `populate_town100` too
  (e.g. hand-authored scenarios), since the `_scenario_character_data`
  preset merge only backfills this for the cast-100 path specifically.
- `domains/resident_trust.py::mint_trust_beliefs` — new optional
  `prior_others_trust` param, applied ONCE as a cold-start prior only
  when the beliefs are genuinely fresh (checked before minting) —
  closes the gap `RESIDENT_TRUST_PREREG.md` itself named ("Optionally
  consumes ... a cold-start prior ... named, not required"). Byte-
  identical for every existing no-arg caller.

## Predictions

1. All 100 cast-100 residents boot with pairwise-distinct, non-default
   gain vectors when built with `cognition_factory=BigvilleOcelotResident`
   — spread reported (min/max/mean), not asserted as "worked."
2. Cost (wall-clock for `populate_town100`, total/mean graph node count
   across all 100 private substrates) measured and reported as a
   headline number — if prohibitive, that IS the result, shipped gated
   rather than silently degraded.
3. The two real cast-100 residents at the observed `hostile_weight` tails
   choose DIFFERENT speech acts toward the SAME neutral stranger at
   identical arousal (coupling armed).
4. `cred_on`/`w_supergraph`-as-coupling-channel remain explicitly named
   as still-deferred (no consumer for either), restated here, not
   quietly dropped from the record.

## What this explicitly does NOT establish

Does NOT claim `coupling_on` is armed by default for a live game session
— it still defaults to `0.0` (Phase 2's own registered default); this
phase only confirms the DATA reaches every resident correctly and that
the mechanism produces real divergence WHEN armed. Does NOT wire
`cred_on`/`w_supergraph` to any new consumer. Does NOT claim the
disposition-driven outcomes are "better" gameplay in any evaluative
sense.

## Files

- `bigville/worlds/bigville_world.py` (edited: `populate_town100`)
- `bigville/game.py` (edited: `_characters_from_world`'s personality filter)
- `domains/resident_trust.py` (edited: `mint_trust_beliefs`)
- `bigville/tests/test_bigville_game_api.py` (edited: new
  `test_populate_town100_seeds_scenario_character_data_per_resident`)
- `scripts/town100_disposition_switchon_demo.py` (new)
- `docs/research/psychology_affect/TOWN100_DISPOSITION_SWITCHON_PREREG.md` (this file)
- `docs/research/psychology_affect/TOWN100_DISPOSITION_SWITCHON_RESULTS.md` (paired)
