# Target-scoped coupling (Phase 4) — RESULTS

Registered design: `TARGET_SCOPED_COUPLING_PREREG.md`. **All 6 predictions
confirmed.**

## 1. Live run (`scripts/target_scoped_coupling_demo.py`)

```
=== Predictions 1/2: affinity tags are selective, pity/controllability uncoupled ===
regard_for           affinity_warm=1.0 affinity_hostile=None affect_bias=25.0
removal_desire_for   affinity_warm=None affinity_hostile=1.0 affect_bias=31.25
pity_for             affinity_warm=None affinity_hostile=None affect_bias=<no couples_affect_to edge>
admiration_for       affinity_warm=1.0 affinity_hostile=None affect_bias=25.0
devaluation_for      affinity_warm=None affinity_hostile=1.0 affect_bias=31.25
controllability_for  affinity_warm=None affinity_hostile=None affect_bias=<no couples_affect_to edge>

=== Prediction 3: independent update paths, mixed history ===
regard_for           external_field=-0.6000
removal_desire_for   external_field=0.5400
admiration_for       external_field=0.0000
devaluation_for      external_field=0.0000

=== Prediction 4: spite_gain isolates removal_desire_for from regard_for ===
spite_gain: low=0.3333 high=4.0000
removal_desire_for: low=0.1800 high=2.1600
regard_for (should match): low=-0.6000 high=-0.6000

=== Prediction 5: crystallization threshold unaffected by spite_gain ===
incidents to crystallize: spite_gain=1.0 -> 2, spite_gain=4.0 -> 2
```

## 2. Predictions

1. **Affinity tags land exactly on the registered pathway** — `PASS`.
   `regard_for`/`admiration_for` carry `affinity_warm=1.0` and no
   `affinity_hostile`; `removal_desire_for`/`devaluation_for` the
   reverse. Note `regard_for`/`admiration_for` both landed
   `affect_bias=25.0` and `removal_desire_for`/`devaluation_for` both
   `31.25` — expected: they share the SAME affinity tag, so with
   identical coupler state they get identical bias, which is exactly
   what "the tag, not the Concept identity, drives the coupling" means.
2. **`pity_for`/`controllability_for` genuinely uncoupled** — `PASS`.
   Neither carries an `affect_bias` attr at all (no `couples_affect_to`
   edge was ever added) — not "tagged but zero," structurally absent
   from the coupling graph.
3. **Independent update paths, no cross-pathway leak** — `PASS`. After 2
   real negative incidents: `regard_for=-0.6000`, `removal_desire_for=
   0.5400` — distinct, real, nonzero, each driven by its own update rule
   (`regard_for` accumulates every incident's signal; `removal_desire_for`
   only the crystallizing one). `admiration_for`/`devaluation_for`
   (untouched by any positive incident) stayed EXACTLY `0.0000` — the
   coupling did not leak activity between pathways.
4. **`spite_gain` isolates `removal_desire_for` from `regard_for`** —
   `PASS`. `spite_gain` (`0.3333` vs `4.0000`) diverged
   `removal_desire_for` (`0.1800` vs `2.1600`, a real 12× swing) while
   `regard_for` stayed IDENTICAL (`-0.6000` both) — clean isolation,
   confirming `spite_gain` only touches the ONE formula it was added to.
5. **Crystallization threshold unaffected** — `PASS`. Both
   `spite_gain=1.0` and `spite_gain=4.0` crystallized on incident 2 —
   disposition shades the MAGNITUDE of the removal motive once
   crystallized, never whether/when crystallization itself happens.
6. **Default `spite_gain=1.0` reproduces the exact pre-Phase-4 regression
   number** — `PASS` (verified in
   `test_default_spite_gain_matches_pre_phase4_behavior`):
   `effective_removal_alpha == 1.2000` exactly
   (`0.3 × (1+1) × (1+1) × 1.0`), byte-identical to
   `HATE_RESENTMENT_PASSION_COUPLING_PREREG.md`'s own registered number.

## 3. Honesty notes

**Does establish**: the generic coupling mechanism (Phase 2) composes
cleanly with a REAL, previously-built, independently-tested Concept
family without merging or leaking between them — the amygdala-
dissociation constraint (`EMOTIONAL_SYSTEMS_UNIFICATION_DESIGN.md` §3b)
held up as an actual, passing test, not just a design intention.
`spite_gain` demonstrates the pattern for adding a NEW selective
pathway-gain: one new optional parameter, one new `AffectChannel`-style
row in `psi_resolve_disposition_gains`, zero changes to any existing
caller's behavior at the default.

**Does NOT establish**: any wiring for `cred_on`/`w_supergraph`-as-channel
(both still explicitly deferred — no consumer exists for either yet).
Does NOT run against a live 100-cast population (Phase 5 — everything
here used hand-constructed residents). Does NOT claim disposition-shaded
target beliefs are more "correct" in any evaluative sense than
unshaded ones — only that the shading is present, selective, and
additive.

## 4. Files

- `docs/research/psychology_affect/TARGET_SCOPED_COUPLING_PREREG.md`
- `docs/research/psychology_affect/TARGET_SCOPED_COUPLING_RESULTS.md` (this file)
- `domains/shared_arousal.py` (edited)
- `domains/hate_attribution.py` (edited)
- `worlds/bigville_ocelot_adapter.py` (edited)
- `scripts/_build_affect_coupling_seed.py` (edited)
- `seeds/affect_coupling.json` (regenerated, 4th gain row)
- `tests/test_target_scoped_coupling.py` (new, 6/6)
- `scripts/target_scoped_coupling_demo.py` (new)
