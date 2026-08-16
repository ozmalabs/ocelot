# Resident trust — RESULTS

Registered design: `RESIDENT_TRUST_PREREG.md`. **All 4 predictions
confirmed.**

## 1. Live run (`scripts/resident_trust_demo.py`)

```
=== Prediction 1: competence alone does not raise trust ===
trust after competence-only: 0.0000

=== Prediction 2: trust rises once BOTH dimensions are positive ===
trust after both positive: 0.3000

=== Prediction 3: a betrayal caps trust regardless of competence ===
competence now: 1.8000, trust: 0.3000
after 2 betrayals: willingness=-0.3000, competence=1.8000 (unchanged), trust=-0.3000

=== Prediction 4: per-target isolation ===
Sam's trust (unaffected by Alex's history): 0.0000
```

## 2. Predictions

1. **Competence evidence alone does not raise trust** — `PASS`.
   `min(0.3, 0.0) == 0.0` — the weakest-link property confirmed exactly,
   not a partial-credit average that would have shown some positive
   trust from competence alone.
2. **Trust rises once BOTH dimensions are positively evidenced** —
   `PASS`. `0.3000` matches the shared positive value both dimensions
   reached.
3. **A single betrayal caps trust regardless of competence** — `PASS`,
   and starkly so: competence built up to `1.8000` (six positive
   incidents) has ZERO effect once willingness turns negative — trust
   tracks `willingness` exactly (`-0.3000`), not any blend with the much
   higher competence score.
4. **Per-target isolation** — `PASS`. Sam's trust reads exactly `0.0000`
   despite Alex's substantial accumulated history on the same substrate.

## 3. Honesty notes

**Does establish**: a working generalization of `trust_mayor`'s
already-proven evidence-driven CAN pattern to ANY target, decomposed per
Castelfranchi's competence/willingness model, reusing the SAME named ToM
entry point (`mint_resident_tom_belief`) `controllability_for` already
established rather than forking a parallel representation. The
weakest-link combination rule (`min`, not average) is confirmed to
produce the theoretically important asymmetry: trust cannot be bought
back with competence after a betrayal in willingness.

**Does NOT establish**: Castelfranchi's third dimension, dependence — not
built. Does NOT couple this signal to `shape_fit_preference`'s own
fluency read as a cold-start prior — a real, deferred integration point.
Does NOT touch or generalize `trust_mayor`'s own structural
`causal_influence` coupling into the resident's broader CAN network —
confirmed untouched (`worlds/bigville_can_beliefs.py`, git-status-gated).
`min()` as the combination rule is a documented, standard simplification,
not independently validated against a richer weighted model.

## 4. Files

- `docs/research/psychology_affect/RESIDENT_TRUST_PREREG.md`
- `docs/research/psychology_affect/RESIDENT_TRUST_RESULTS.md` (this file)
- `domains/resident_trust.py` (new)
- `scripts/resident_trust_demo.py` (new)
- `tests/test_resident_trust.py` (7/7, new)
