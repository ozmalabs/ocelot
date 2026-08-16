# Shape-fit preference — RESULTS

Registered design: `SHAPE_FIT_PREFERENCE_PREREG.md`. **All 5 predictions
confirmed.**

## 1. Live run (`scripts/shape_fit_preference_demo.py`)

```
=== Predictions 1/2/3: the inverted-U over fluency ===
exact match (fluency=1.0)        fluency=1.0000 preference=0.0000 arousal=0.0000
partial match (fluency=2/3)      fluency=0.6667 preference=0.8889 arousal=0.3333
total novelty (fluency=0.0)      fluency=0.0000 preference=0.0000 arousal=1.0000

=== Prediction 4: symmetry around the midpoint ===
fluency=0.3: preference=0.840000
fluency=0.7: preference=0.840000
match: True

=== Prediction 5: novelty feeds the shared arousal pool ===
familiar stimulus arousal_level: 0.0000
novel stimulus arousal_level:    1.0000
```

## 2. Predictions

1. **Exact match (`fluency=1.0`) scores `preference=0.0`** — `PASS`. The
   over-familiar/boring extreme, confirming this is NOT a monotonic
   "more fit = more liked" formula — the theoretically important
   negative result Berlyne's model predicts and simple fluency-only
   accounts (Reber/Winkielman/Schwarz taken in isolation) would not.
2. **Total novelty (`fluency=0.0`) ALSO scores `preference=0.0`** —
   `PASS`. The overwhelming/incoherent extreme.
3. **Partial match scores strictly higher than both extremes** — `PASS`.
   `fluency=0.667` scores `preference=0.889`, well above either `0.0`.
4. **Symmetry** — `PASS`. `fluency=0.3` and `fluency=0.7` score
   IDENTICALLY (`0.840000` both), confirming the registered parabola
   shape precisely rather than an ad hoc asymmetric curve.
5. **Novelty feeds arousal** — `PASS`. A totally novel stimulus raises
   `TargetArousal.level` to `1.0000`; a perfectly familiar one leaves it
   at `0.0000` (zero novelty, zero contribution) — the documented side
   observable, tracked but not folded into `preference` itself.

## 3. Honesty notes

**Does establish**: a preference primitive that is qualitatively
different from every other valence Concept in this arc — a direct
read-off of the sd loop's own already-existing decode fluency
(`ShapeDecode`'s `covered_count`/`goal_relations`, confirmed pre-surfaced
before this rung began, zero new plumbing), composed into Berlyne's
inverted-U rather than a Concept accumulating evidence via
`concept_apply_evidence`. This is the "an agent likes things by shape"
mechanism the user named directly, working exactly as the theory
predicts: familiarity alone does not maximize liking; moderate mismatch
against what is already known does.

**Does NOT establish**: any specific interaction between fluency and
arousal beyond tracking both as separate observables (Sec2 of the
PREREG explicitly declines to fabricate a combined formula without a
citable functional form). Does NOT validate the `4x(1-x)` parabola
against real preference-rating data — a documented, un-fitted functional
choice, same honesty class as every other design decision in this arc.
Does NOT wire this signal into `regard_for`'s own accumulated-evidence
valence as a cold-start prior — a real, named, deferred integration
point, not built here.

## 4. Files

- `docs/research/psychology_affect/SHAPE_FIT_PREFERENCE_PREREG.md`
- `docs/research/psychology_affect/SHAPE_FIT_PREFERENCE_RESULTS.md` (this file)
- `domains/shape_fit_preference.py` (new)
- `scripts/shape_fit_preference_demo.py` (new)
- `tests/test_shape_fit_preference.py` (7/7, new)
