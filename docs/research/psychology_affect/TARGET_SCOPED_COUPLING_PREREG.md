# Target-scoped coupling (Phase 4) — PRE-REGISTRATION

**Committed BEFORE measurement** (fixed in the approved build plan,
`/home/matt/.claude/plans/distributed-frolicking-waterfall.md`). Phase 4
of 5 resolving `EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §5. Builds on
Phases 1-3 (all confirmed; Phase 2's `gain_cap` was retracted and
corrected mid-Phase-3 — `AFFECT_COUPLING_SHAPE_RESULTS.md` §0).

## Goal

Extend the generic coupling (Phase 2) to the target-scoped
social-disposition family (`domains/hate_attribution.py`) — mood-congruent
processing (Bower 1981) shades HOW STRONGLY a target-scoped belief lands,
WITHOUT merging distinct Concepts into one scalar. The amygdala
dissociation evidence (`EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §3b:
Adolphs/Feinstein patient SM — fear knocked out specifically, other
emotions intact) is the concrete constraint this phase turns into tests,
not just design prose.

## Design

- `domains/shared_arousal.py::mint_target_concept` — new optional
  `affinity` dict param, tags the Concept at creation only. Byte-identical
  for every existing no-arg caller.
- `domains/hate_attribution.py::mint_target_pattern` — tags `regard_for`/
  `admiration_for` `affinity_warm=1.0`, `removal_desire_for`/
  `devaluation_for` `affinity_hostile=1.0`. `pity_for`/`controllability_for`
  get NEITHER tag — pity is the OUTCOME of low controllability (not an
  affect the coupler should shade) and controllability is a ToM belief
  about the target (not the resident's own affect).
- `domains/hate_attribution.py::record_hate_incident` — new optional
  `spite_gain: float = 1.0` param, a THIRD multiplicative factor on
  `effective_removal_alpha` alongside the existing (unmodified)
  `(1+arousal)(1+resentment_debt)` term. Default `1.0` — byte-identical
  to every pre-existing caller.
- `worlds/bigville_ocelot_adapter.py::_couple_target_pattern` (new) —
  adds `couples_affect_to` edges from the resident's `AffectCoupler` to
  the 4 tagged Concepts on a `TargetPattern` (idempotent — checks for an
  existing edge first, so calling it more than once, from the two
  existing call sites that can each mint the same pattern
  — the `social_dispositions` loop and `_apply_generated_dispositions` —
  never double-counts a channel in the coupling `Sum`). `pity_for`/
  `controllability_for` never get a `couples_affect_to` edge at all —
  genuinely excluded, not "tagged but zero."
- `AffectCoupler` gains `spite_gain`/`spite_ref=0.15` (the `_PARAM_SPEC`
  population mean); `psi_resolve_disposition_gains` (Phase 2's rule)
  gains a fourth gain row, uncapped (per Phase 3's correction).

## Predictions

1. Affinity tags land exactly on the registered pathway per Concept
   (`regard_for`/`admiration_for` warm, `removal_desire_for`/
   `devaluation_for` hostile), nothing else.
2. `pity_for`/`controllability_for` never receive a `couples_affect_to`
   edge — genuinely uncoupled, confirmed by absence of `affect_bias`
   entirely, not by a zero value.
3. After a mixed real-incident history (2 negative incidents), `regard_for`
   and `removal_desire_for` move to distinct, real nonzero values while
   `admiration_for`/`devaluation_for` (untouched by any positive
   incident) stay exactly `0.0` — the coupling does not leak activity
   between the warm and hostile pathways.
4. High- vs low-`w_spite` residents, identical incident sequence,
   diverge in `removal_desire_for` while `regard_for` stays identical —
   isolates `spite_gain` from the regard/arousal channels.
5. Crystallization threshold (incident count to first crystallize) is
   unaffected by `spite_gain` — disposition shades magnitude, never the
   gate.
6. `spite_gain=1.0` (default) reproduces
   `HATE_RESENTMENT_PASSION_COUPLING_PREREG.md`'s own exact regression
   number (`effective_removal_alpha=1.2` at `base_alpha=0.3,
   arousal=1.0, resentment_debt=1.0`) byte-for-byte.

## What this explicitly does NOT establish

Does NOT wire `cred_on`/`w_supergraph`-as-channel (still deferred, no
consumer exists). Does NOT run against a live 100-cast population
(Phase 5). Does NOT claim the coupling IMPROVES any outcome — only that
it is present, correctly selective, and additive alongside (never
replacing) real incident-driven evidence.

## Files

- `domains/shared_arousal.py` (edited)
- `domains/hate_attribution.py` (edited: `mint_target_pattern` tagging,
  `record_hate_incident` `spite_gain` param)
- `worlds/bigville_ocelot_adapter.py` (edited: `_couple_target_pattern`,
  wired into both call sites, `spite_gain`/`spite_ref` on `AffectCoupler`)
- `scripts/_build_affect_coupling_seed.py` (edited: 4th gain row)
- `seeds/affect_coupling.json` (regenerated)
- `tests/test_target_scoped_coupling.py` (new)
- `scripts/target_scoped_coupling_demo.py` (new)
- `docs/research/psychology_affect/TARGET_SCOPED_COUPLING_PREREG.md` (this file)
- `docs/research/psychology_affect/TARGET_SCOPED_COUPLING_RESULTS.md` (paired)
