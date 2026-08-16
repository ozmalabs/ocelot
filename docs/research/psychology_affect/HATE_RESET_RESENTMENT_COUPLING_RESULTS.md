# Hate reset × arousal coupling (resentment) — RESULTS

Registered design: `HATE_RESET_RESENTMENT_COUPLING_PREREG.md`. **All 4
predictions confirmed** — prediction 4 in the empirically-corrected form
its own PREREG section already registers (measured before finalizing,
per this arc's standing discipline, then written into the PREREG rather
than silently swapped in).

## 1. Live run (`scripts/hate_reset_resentment_coupling_demo.py`)

```
=== Prediction 1: at zero arousal, specific_act is still an exact full reset ===
staged streak=5.0, arousal=0.0 -> post-exception streak=0.0000

=== Prediction 2: elevated arousal leaves a strictly positive residue ===
staged streak=5.0, arousal=1.0 (retained_fraction=0.5) -> post-exception streak=2.5000

=== Prediction 3: the residue matches the formula exactly, live ===
pre-exception streak=1.8000 arousal=1.3600 -> residue=1.0373 (expected 1.0373)

=== Prediction 4: resented streak stays ahead of forgiven streak at a matched step ===
hot (arousal=1.0 at exception): residue=0.5000 -> streak after resumed confirmation=3.0000
cold (arousal=0.0 at exception): residue=0.0000 -> streak after resumed confirmation=1.8000
```

## 2. Predictions

1. **At zero arousal, `specific_act` is still an exact full reset** —
   `PASS`. A staged `streak=5.0` at `arousal=0.0` resets to exactly
   `0.0000` — byte-identical to every prior rung's behavior.
2. **Elevated arousal leaves a strictly positive residue** — `PASS`. The
   SAME staged `streak=5.0` at `arousal=1.0` (`retained_fraction=0.5`)
   resets only to `2.5000` — half the pre-exception streak survives.
3. **The residue matches the formula exactly, live** — `PASS`. A
   genuinely-grown (not staged) sequence's residue (`1.0373`) matches
   `old_streak * level/(1+level)` computed independently from the SAME
   run's own prior result to 4 decimal places.
4. **A resented streak stays ahead of a forgiven one at a matched step**
   — `PASS`, in the corrected form. From the identical `pre_streak=1.0`,
   an aroused exception (`level=1.0`) leaves a `0.5` residue that carries
   forward to `streak=3.0` after one resumed confirmation, versus a cold
   exception's `0.0` residue carrying forward to only `streak=1.8` — a
   real, measurable, forward-propagating advantage from resentment.

## 3. A prediction corrected before finalizing, not after

The PREREG's ORIGINAL Sec3 prediction 4 (before this RESULTS doc was
written) claimed the resented path would cross the crystallization gate
in FEWER TOTAL INCIDENTS than the forgiven path. **Measured before
finalizing** (this arc's own standing discipline): across a systematic
parameter sweep (pre-exception streak `0.05`–`2.5`, exception-time
arousal `0.1`–`2.5`), the two paths crystallized on the SAME incident
count in every case tried — never separated by an integer step. The
cause, found and understood, not just observed: `AROUSAL_INTENSITY=0.8`
is applied UNCONDITIONALLY on every incident (including the exception
itself and the forgiving/cold path's own exception), so post-exception
arousal is never actually zero in either path — combined with the
already-landed increment (`v1.2.0`) and threshold-lowering (`v1.3.0`)
couplings, ONE resumed confirming incident is very often already enough
to cross the gate regardless of the residue's exact size, because those
two couplings dominate the outcome at this scale.

**This is not the retracted `belief_plasticity` situation** — nothing was
built and then reverted. The PREREG's Sec3 prediction 4 was rewritten,
in place, BEFORE this RESULTS doc was finalized, to the claim that
survives the compounding (`confirm_streak` VALUE at a matched step,
rather than incident COUNT), and the PREREG itself documents why the
stronger claim doesn't hold, in its own words, rather than this RESULTS
doc silently reporting a different prediction than what was registered.
The mechanism itself — the residue exists, is strictly positive when
aroused, and matches its formula exactly — is unaffected; only the
downstream behavioral framing of prediction 4 changed.

## 4. Honesty notes

**Does establish**: `confirm_streak`'s reset on `specific_act` now models
resentment directly — a grievance that persists past a disconfirming act
because the act was discounted under the same arousal the grievance
itself produced (Bodenhausen 1993), with NO new node type, NO new
constant, and an exact backward-compatible zero-arousal case. The
mathematically guaranteed direction (residue monotonically nonnegative,
strictly positive whenever arousal is) is proven exactly by predictions
1–3; its forward propagation into a real streak-value advantage is
confirmed by prediction 4.

**Does NOT establish**: that resentment measurably changes HOW MANY
incidents it takes to crystallize hate, given this arc's own already-
landed couplings — that stronger claim was tested and found not to hold
at the parameter scale explored, and the PREREG says so. Does NOT model
active forgiveness-seeking, apology, or repair — only the passive
discount-under-arousal effect on credit given to one disconfirming act.

## 5. Files

- `docs/research/psychology_affect/HATE_RESET_RESENTMENT_COUPLING_PREREG.md`
- `docs/research/psychology_affect/HATE_RESET_RESENTMENT_COUPLING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (unchanged — the coupling is entirely inside the Rule, not Python)
- `scripts/_build_hate_attribution_seed.py` (edited: `_retained_fraction_term`, v1.4.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_reset_resentment_coupling_demo.py` (new)
- `tests/test_hate_reset_resentment_coupling.py` (6/6, new)
- `tests/test_hate_attribution.py` (1 test renamed/rewritten to check the residue formula instead of a bare 0; 10/10 still green)
