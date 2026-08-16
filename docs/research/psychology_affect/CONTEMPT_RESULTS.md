# Contempt — RESULTS

Registered design: `CONTEMPT_PREREG.md`. **All 5 predictions confirmed.**
This closes Phase G, the final phase of the expanded emotional+
preference system build plan.

## 1. Live run (`scripts/contempt_demo.py`)

```
=== Prediction 1: default violation_type still routes removal (backward compat) ===
route=removal removal_ef=0.5400 devaluation_ef=0.0000

=== Prediction 2: a controllable norm violation routes to devaluation ===
route=devaluation removal_ef=0.0000 devaluation_ef=0.3000

=== Prediction 3: controllability still gates independently of violation type ===
uncontrollable norm violation -> route=pity

=== Prediction 4: devaluation_for's alpha is unamplified, unlike removal_desire_for's ===
removal (amplified): effective_removal_alpha=1.2000
devaluation (flat):  devaluation_external_field=0.3000 (== base_alpha=0.3000)

=== Prediction 5: per-target isolation ===
Jo crystallized=True, Kim's own violation_type=harm (unaffected by Jo's)
```

## 2. Predictions

1. **Backward compatibility** — `PASS`. Every existing caller (no
   `violation_type` argument) still routes to `"removal"`, matching
   `v1.7.0`'s exact figures (`0.5400`, unchanged from `ADMIRATION_
   GRATITUDE_RESULTS.md`'s own no-understanding demo).
2. **A controllable norm violation routes to devaluation** — `PASS`.
   `removal_desire_for` receives ZERO evidence; `devaluation_for`
   receives it instead.
3. **Controllability still gates independently of violation type** —
   `PASS`. An UNCONTROLLABLE norm violation still routes to `"pity"`,
   confirming the two axes (Weiner's controllability, the CAD triad's
   violation type) compose rather than one overriding the other.
4. **`devaluation_for`'s alpha is unamplified** — `PASS`, and starkly
   so: matched arousal (`1.0`) and resentment_debt (`1.0`) produce
   `effective_removal_alpha=1.2000` for the `"removal"` route but only
   the flat `base_alpha=0.3000` for `"devaluation"` — confirming
   contempt's documented "colder" character is a real, measured design
   choice, not just an assertion in the PREREG's prose.
5. **Per-target isolation** — `PASS`. Kim's own `violation_type` reads
   the call-supplied `"harm"` default, completely unaffected by Jo's
   prior `"norm"`-routed crystallization on the same substrate.

## 3. Honesty notes

**Does establish**: the second leg of Rozin, Lowery & Haidt (1999)'s CAD
triad (Contempt, for Community violations) alongside the already-built
Anger/Hate leg (Autonomy violations, Fischer et al. 2018's elimination
motive), sharing ONE crystallization ladder, ONE controllability gate,
and adding exactly one new caller-supplied datum (`violation_type`) with
zero new decisions — the routing itself is entirely a Rule-computed Term,
matching the same rules-decide/Python-dispatches division of labor
`consequence_route` has used since `HATE_PITY_TOM_UNDERSTANDING_PREREG.
md`. Confirms, not just asserts, that contempt is measurably "colder"
than hate in this substrate: the SAME crystallizing conditions produce a
4x weaker motivational signal via the unamplified `devaluation_for` path.

**Does NOT establish**: the CAD triad's third leg, Disgust (Divinity
violations) — two of three built, one explicitly out of scope. Does NOT
aggregate `violation_type` across the whole confirming pattern — reads
only the crystallizing incident's own value, the same snapshot
convention `consequence_route`'s controllability read already uses.
Does NOT model any behavioral enactment of devaluation.

## 4. Files

- `docs/research/psychology_affect/CONTEMPT_PREREG.md`
- `docs/research/psychology_affect/CONTEMPT_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: `violation_type` param, `devaluation_for` Concept, three-way dispatch)
- `scripts/_build_hate_attribution_seed.py` (edited: `violation_type` passthrough, `_consequence_route_term`'s second branch, `tracks_devaluation` production, v1.8.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/contempt_demo.py` (new)
- `tests/test_contempt.py` (6/6, new)
