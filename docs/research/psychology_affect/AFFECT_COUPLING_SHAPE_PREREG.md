# Affect-coupling shape (Phase 2) — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`, designed
by an Opus Plan agent that read `runners/dsl/src/{term,rewrite}.rs`
before proposing anything; two of its most load-bearing claims —
`MatchEdge`'s type-agnostic endpoints and `numeric_variadic`'s
`Times`-identity-on-absence behavior — were independently spot-checked
against source before this plan was approved). Phase 2 of 5 resolving
`EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §5. Builds on Phase 1
(`DISPOSITION_TRANSPORT_RESULTS.md`, all 6 predictions confirmed).

## Goal

One seeded Rule, matched by SHAPE (any node with a `couples_affect_to`
edge + `affinity_*` attrs), automatically produces `affect_bias` — no
coefficient hand-authored per decision type. Composes additively;
changes nothing at population-mean disposition. OFF by default
(`coupling_on` guard), and NOT added to `boot_core.CORE_SEEDS`/
`boot_all` — zero blast radius on any other agent in the tree.

## Design

`AffectCoupler` (Phase 1) extended with 4 `AffectChannel` data rows
(`valence`, `trait_valence`, `arousal_hostile`, `arousal_warm`), each
naming which `state_key`/`bias_key`/`gain_key`/`pathway_gain_key` attr to
read via `AttrByName` — a NEW channel is a new row, not a rule edit.
Two rules in `seeds/affect_coupling.json`
(`scripts/_build_affect_coupling_seed.py`):

- `psi_resolve_disposition_gains` — normalizes raw disposition traits
  into gains (`reactivity_gain = min(trait_arousal/arousal_ref,
  gain_cap)`, similarly for `hostile_gain`/`warmth_gain`), clamped.
- `psi_couple_affect_to_tagged` — `affect_bias = Sum(channels,
  Times[affinity, (state+bias), gain, pathway_gain])`. Every read is
  `P0`-wrapped (`Plus[Attr(...), Lit 0.0]`) — required because an
  unwrapped `Times` treats a missing factor as the multiplicative
  identity (1), confirmed in `term.rs::numeric_variadic`'s
  `Value::None => {}` arm, NOT zero.

`_ensure_speech_graph` mirrors `warm_aff`/`hostile_aff` (bigville's own
`SPEECH_MENU` names) onto the canonical `affinity_warm`/`affinity_hostile`
attrs and adds a `couples_affect_to` edge per `SpeechOption`.
`decide_speech` mints its `Encounter` UNARMED, settles the bias with one
`run_rules()`, then arms (`decide_armed=1.0`) and runs again — fixes a
real found hazard: install order loads `bigville_speech_decide` before
`_ensure_emotional_core`'s seeds, so an armed-on-mint Encounter could read
a stale bias on the very first encounter. `bigville_speech_decide.json`
(both copies, confirmed byte-identical before and after) gains exactly
ONE new `Plus` item — `P0(opt.affect_bias)` — inside the existing
non-silence value formula (v1.1.0).

## Predictions

1. The SAME unmodified rule writes `affect_bias` on a `SpeechOption` AND
   a throwaway tagged `Concept` in one fixpoint — proves genericity.
2. `coupling_on=0` → `affect_bias` stays `0.0` — byte-identical to Phase 1.
3. An untagged node (no `affinity_*` attrs) → `affect_bias == 0.0`
   exactly — the `Times`-identity-trap regression.
4. Disposition/arousal isolation: `hostile_weight` diverges bias at
   IDENTICAL arousal; arousal diverges bias at IDENTICAL `hostile_weight`
   — neither channel alone explains both.
5. Population-mean resident (`arousal=0.40, hostile_weight=0.40,
   charm_weight=0.50, valence=0, mood_bias=0`) → every gain exactly
   `1.0`/`0.0`.
6. Additive, never overriding: real crystallized-feud-strength relationship
   still routes hostile even with `hostile_gain` clamped to `0`; the
   reverse (`hostile_gain` maxed) does not flip a strongly-warm real
   relationship.
7. Settling order: first-ever and second `decide_speech` on a fresh
   resident read the same settled bias.
8. Fail-quiet gain caught: a missing/zeroed reference mean → `Div`-by-zero
   → gain silently `0`, asserted explicitly, not just risked.
9. `gain_cap` actually clamps an extreme-tailed disposition.

## What this explicitly does NOT establish

Does NOT remove the hand-patched `arousal_gain × speaker_arousal ×
hostile_aff` term from `sp_choose_utterance` (Phase 3 — both channels
coexist this phase, additively). Does NOT tag any target-scoped Concept
(`regard_for`/`hate_attribution` etc, Phase 4). Does NOT run on a live
`populate_town100` cast (Phase 5). Does NOT claim the gain constants
(`gain_cap=2.0`, the reference means) are empirically calibrated — they
are registered normalizations against the generator's own drawn means,
a weaker claim than a fit.

## Files

- `scripts/_build_affect_coupling_seed.py` (new)
- `seeds/affect_coupling.json` (new, generated)
- `worlds/bigville_ocelot_adapter.py` (edited)
- `bigville/seeds/bigville_speech_decide.json` +
  `bigville/bigville/seeds/bigville_speech_decide.json` (bigville repo,
  edited, v1.1.0, both copies kept identical)
- `tests/test_affect_coupling.py` (new)
- `scripts/affect_coupling_demo.py` (new)
- `docs/research/psychology_affect/AFFECT_COUPLING_SHAPE_PREREG.md` (this file)
- `docs/research/psychology_affect/AFFECT_COUPLING_SHAPE_RESULTS.md` (paired)
