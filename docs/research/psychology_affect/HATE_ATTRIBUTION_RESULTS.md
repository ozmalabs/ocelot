# Hate attribution — RESULTS

Registered design: `HATE_ATTRIBUTION_PREREG.md`. **All 7 predictions
confirmed.** One design correction made and reported honestly (Sec 3
below), matching this arc's own standing discipline.

## 1. Live run (`scripts/hate_attribution_demo.py`)

```
=== Predictions 1/3/5/6: repeated negative incidents toward Alex ===
incident 0: locus=first_encounter streak=0 crystallized=False (this_call=False) regard_ef=-0.30 removal_ef=+0.00
incident 1: locus=global_other   streak=1 crystallized=False (this_call=False) regard_ef=-0.60 removal_ef=+0.00
incident 2: locus=global_other   streak=2 crystallized=False (this_call=False) regard_ef=-0.90 removal_ef=+0.00
incident 3: locus=global_other   streak=3 crystallized=True  (this_call=True ) regard_ef=-1.20 removal_ef=+0.30
incident 4: locus=global_other   streak=4 crystallized=True  (this_call=False) regard_ef=-1.50 removal_ef=+0.30

=== Prediction 4: a positive exception resets confirm_streak ===
incident 0 (negative): locus=first_encounter streak=0 crystallized=False (this_call=False) regard_ef=-0.30 removal_ef=+0.00
incident 1 (negative, confirms): locus=global_other   streak=1 crystallized=False (this_call=False) regard_ef=-0.60 removal_ef=+0.00
incident 2 (positive, exception): locus=specific_act   streak=0 crystallized=False (this_call=False) regard_ef=-0.30 removal_ef=+0.00
incident 3 (negative, streak restarts): locus=global_other   streak=1 crystallized=False (this_call=False) regard_ef=-0.60 removal_ef=+0.00

=== Prediction 7: per-target isolation, ONE substrate ===
Jo crystallized: True
Kim's first incident (unaffected by Jo's crystallized hate): locus=first_encounter streak=0 crystallized=False (this_call=False) regard_ef=-0.30 removal_ef=+0.00
Kim crystallized: False
```

## 2. Predictions

1. **A confirming incident → `global_other`** — `PASS`. Incidents 1-4
   toward Alex, all negative after an established negative pattern, all
   classify `global_other`.
2. **A disconfirming incident → `specific_act`** — `PASS`. The positive
   exception toward Sam (incident 2) classifies `specific_act`.
3. **A first encounter → `first_encounter`, never `global_other`** —
   `PASS`. Every target's incident 0 classifies `first_encounter`
   regardless of sign.
4. **A `specific_act` resets `confirm_streak` to 0** — `PASS`. Sam's
   streak goes `0 → 1 → 0` (the exception) `→ 1` (restart), never
   accumulating across the exception.
5. **Crystallization requires the threshold, not the first confirmation**
   — `PASS`. Alex's streak reaches 1 and 2 with `crystallized=False`;
   only at streak `3` (`HATE_STABILITY_THRESHOLD`) does `crystallized`
   flip, on incident 3, not incident 1.
6. **`removal_desire` receives evidence ONLY on the crystallizing
   incident** — `PASS`. `removal_ef` is `0.00` through incident 2, jumps
   to `+0.30` exactly at incident 3 (`crystallized_this_call=True`), and
   stays flat at `+0.30` on incident 4 (`crystallized_this_call=False`) —
   the gate opens once, not on every subsequent `global_other` incident.
7. **Per-target isolation** — `PASS`, confirmed within ONE substrate (not
   just separate substrates): Jo's crystallized hate leaves Kim's very
   first incident reading `first_encounter`, `crystallized=False` —
   identical to a target with no history at all.

## 3. A design correction, found and fixed before finalizing

The PREREG (Sec1) proposed live-wiring `held_regard` to the tracked
`regard_for` Concept's own `state` (the discrete, relaxed 3-state CAN
value). **Measured before finalizing** (this arc's own standing
discipline): `state` stayed at `0.0` through six repeated `alpha=0.3`
incidents even as the underlying evidence accumulated — the SAME discrete
relaxation threshold (~0.366 at `temperature=1.5`) `SELF_COMPLEXITY_
COUPLING_RESULTS.md` already found and documented, here silently
misreading every post-first incident as "no held pattern" instead of
tracking the agent's actual accumulating impression, because `state` on
an isolated Concept with no `causal_influence` edges never crosses that
threshold at all in this scale of run.

**Fixed by reading `external_field` (the continuous evidence
accumulator) instead of `state`** — the same object `concept_apply_
evidence` itself writes to directly, so the residual now reads the exact
quantity the mechanism itself moves, with no relaxation-threshold
dependency. This is not the same failure class as the retracted
`belief_plasticity` 1/n anti-pattern (`EVIDENCE_AND_AUDIENCE_WEIGHTING_
RESULTS.md`) — it is a units mismatch (discrete relaxed state vs.
continuous accumulator), not a rate that needs its own rate — but it is
the SAME "measure before shipping" discipline catching a real defect
before it reached the registered predictions, and is recorded here rather
than silently corrected.

## 4. Honesty notes

**Does establish**: a working, regression-tested outward generalization
of `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`'s self-directed residual —
the SAME structural mechanism (residual between an incident's signal and
a held pattern) correctly produces `global_other`/`specific_act`/
`first_encounter` about ANOTHER agent, gated behind a genuine stability
requirement (Sternberg 2003's decision/commitment component) before
crystallizing, with a motivational consequence (Fischer et al. 2018's
elimination goal) correctly withheld from every appraisal below
threshold. `ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md`'s own deferred scope
note — live-wiring the held pattern to a real CAN Concept instead of
supplied data — is attempted and lands here.

**Does NOT establish**: Sternberg's passion component (this rung does not
couple to `SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`'s `TargetArousal`
— named as a real follow-on, not attempted). Does NOT independently
validate `HATE_STABILITY_THRESHOLD=3` against real longitudinal
intergroup-hostility data — a documented, un-fitted constant, same
honesty class as this arc's other constants. Does NOT model group-level
or in-group/out-group hate — scoped to a single (resident, target) pair.
Produces no narrative or depictive content anywhere — every artifact is a
scalar, a Concept name, or a Term formula; no violent action is modeled
or enabled (the still-unbuilt `BIGVILLE_ADMISSIBILITY_GRAMMAR.md` remains
the separate, named gate for anything actionable).

## 5. Files

- `docs/research/psychology_affect/HATE_ATTRIBUTION_PREREG.md`
- `docs/research/psychology_affect/HATE_ATTRIBUTION_RESULTS.md` (this file)
- `domains/hate_attribution.py` (new)
- `scripts/_build_hate_attribution_seed.py` (new)
- `seeds/hate_attribution.json` (new, generated)
- `scripts/hate_attribution_demo.py` (new)
- `tests/test_hate_attribution.py` (9/9, new)
