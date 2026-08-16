# Hate × passion coupling — RESULTS

Registered design: `HATE_PASSION_COUPLING_PREREG.md`. **All 4
predictions confirmed.**

## 1. Live run (`scripts/hate_passion_coupling_demo.py`)

```
=== Predictions 1/2: coupled removal alpha vs formula, back-to-back incidents ===
incident 0: arousal_level=0.8000 effective_removal_alpha=n/a crystallized_this_call=False
incident 1: arousal_level=1.3600 effective_removal_alpha=n/a crystallized_this_call=False
incident 2: arousal_level=1.7520 effective_removal_alpha=n/a crystallized_this_call=False
incident 3: arousal_level=2.0264 effective_removal_alpha=0.8256 crystallized_this_call=True
hand-computed pre-incident arousal level = 1.7520 -> expected alpha = 0.8256

=== Prediction 3: hot vs cold crystallization, same structural event ===
hot crystallization effective_removal_alpha = 0.8256
cold crystallization effective_removal_alpha = 0.3002 (arousal decayed to near-zero between incidents)

=== Prediction 4: per-target isolation with arousal coupling ===
Jo's built-up arousal: 1.7520
Kim's first incident arousal_level (unaffected by Jo's): 0.8000 (expect 0.8000)
```

## 2. Predictions

1. **Coupled removal-desire evidence at crystallization exceeds
   `base_alpha`** — `PASS`. Three back-to-back negative incidents build
   arousal to `1.7520` before the crystallizing 4th incident; its
   `effective_removal_alpha=0.8256`, nearly 3× `base_alpha=0.3`.
2. **The amplification matches the formula exactly** — `PASS`. Hand-
   computing `level` from the SAME `level*0.7 + 0.8` recurrence
   independently of the live run gives `1.7520`, and
   `0.3*(1+1.7520)=0.8256` matches the live `effective_removal_alpha` to
   4 decimal places.
3. **"Hot" vs "cold" crystallization** — `PASS`. The IDENTICAL structural
   event (confirm_streak crossing `3`) produces `0.8256` when incidents
   fire back-to-back versus `0.3002` (effectively `base_alpha`,
   unamplified) when arousal is decayed toward zero between each
   incident — same crystallization, markedly different motivational
   strength, purely from timing.
4. **Per-target isolation holds** — `PASS`. Jo's arousal builds to
   `1.7520` from 3 prior incidents; Kim's first incident (same
   substrate) reads `arousal_level=0.8000` — exactly the single-incident
   baseline (`0*0.7+0.8`), unaffected by Jo's build-up.

## 3. Honesty notes

**Does establish**: `removal_desire_for`'s evidence at hate
crystallization is now genuinely coupled to Sternberg's passion
component via the SAME shared `TargetArousal` pool `shared_arousal.json`
already built for cross-belief excitation transfer — the identical
structural crystallization event produces a markedly stronger
motivational consequence when reached amid high arousal than when
reached cold, matching the theory's own claim that passion intensifies
the commitment, not just the appraisal. Non-crystallizing incidents still
contribute to the shared pool (so a genuine run-up of passion is possible
before the stability gate opens) without themselves applying any removal
evidence — the coupling is scoped exactly where the user asked
(`removal_desire`'s `alpha`), not spread into `regard_for`'s own
evidence application or into the crystallization threshold itself.

**Does NOT establish**: coupling `HATE_STABILITY_THRESHOLD` to arousal
(a separately named, still-deferred follow-on — an aroused incident
could plausibly count more toward the streak itself, not attempted
here). Does NOT independently validate `AROUSAL_INTENSITY=0.8`/
`AROUSAL_DECAY=0.7` beyond what `SHARED_AROUSAL_EXCITATION_TRANSFER_
RESULTS.md` already confirmed for those same constants in a different
context — reused verbatim, not re-derived.

## 4. Files

- `docs/research/psychology_affect/HATE_PASSION_COUPLING_PREREG.md`
- `docs/research/psychology_affect/HATE_PASSION_COUPLING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: tracks shared TargetArousal, couples crystallizing removal_desire alpha)
- `scripts/_build_hate_attribution_seed.py` (edited: `tracks_arousal` production, `depends_on: ["shared_arousal"]`, v1.1.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_attribution_demo.py` (edited: `_fresh` now also loads `shared_arousal.json`)
- `scripts/hate_passion_coupling_demo.py` (new)
- `tests/test_hate_attribution.py` (edited: `_fresh` now also loads `shared_arousal.json`; 9/9 still green)
- `tests/test_hate_passion_coupling.py` (5/5, new)
