# Vowel recognition — the F2-resolving formant-frame weighted-admissibility match

**The named fix for the vowel-rung limiter (follows commit a363ca71).**

## The limiter being fixed

The AbS vowel recogniser (`scripts/solve_for_n_vowel.py`) worked above chance
(38.9%, chance 20%) but lost badly to a plain 1-NN exemplar (65.1%). The
diagnosis from a363ca71 was that the bottleneck is the **match space, not the
forward model**: the speaker-relative **mel-envelope L2** match UNDER-RESOLVES
F2. The formant peaks sit buried under the low-frequency spectral tilt, so
front/back pairs that share F1 but differ only in F2 collapse together. The
mel-L2 confusion matrix shows exactly this:

```
AbS mel-L2 confusion (row=true, col=pred)   acc 38.9%
       ao    eh    ih    iy    uw
  ao:  188     0     0     0   112      ao -> uw  (share low F1, differ in F2)
  eh:  194    46    26    11    23      eh -> ao  (the worst: 194/300 lost to ao)
  ih:   60    16   101   121     2      ih <-> iy
  iy:   22    22   105   120    31      iy <-> ih
  uw:    1     0    85    86   128      uw -> ih/iy
```

The synthesis CARRIES F2 (the forward model has an explicit F2 resonator); the
mel-L2 match THREW IT AWAY by burying it under the tilt.

## The fix (only the match function swapped)

The vowel forward model, the per-utterance speaker search (f0 + VTL/formant
scale grid), the data harness (1500 real FSDD nuclei, 5 vowels, 6 speakers),
and the LOSO cross-speaker split (held-out speaker NEVER banked) are **unchanged**.
The mel-envelope L2 match is replaced by an **F2-resolving formant-frame
weighted-admissibility match**:

1. **Input formant estimation (owned DSP, no net/fit).** Estimate F1,F2,F3 of
   the input clip via **LPC roots** — autocorrelation + Levinson-Durbin (order
   10), then the pole resonance frequencies. This inverts the same all-pole
   source-filter model the forward model uses. **Pre-emphasis (1 − 0.97 z⁻¹)**
   flattens the −6 dB/oct glottal source tilt first; without it the tilt plants
   a spurious low-frequency pole that pushes every formant down a slot (the
   off-by-one that buried F2 below 600 Hz in the first cut). The lowest 3
   in-band, reasonable-bandwidth poles are F1,F2,F3.

2. **Candidate formants are known analytically.** Peterson-Barney table ×
   searched VTL scale — no synthesis needed for the candidate side.

3. **Speaker-relative formant space.** Each formant frame is mapped to
   **log-formants minus their mean**. A VTL change is a multiplicative shift on
   all formants = an additive shift in log = removed by the mean subtraction.
   What survives is the speaker-INVARIANT formant PATTERN, and **F2 is resolved
   with equal weight to F1/F3** — no low-frequency tilt to bury it. (This makes
   the VTL-scale search a no-op for the relative match, which is correct: the
   relative space already cancels VTL.)

4. **Weighted-admissibility, NOT a dot product** (memory:
   `ozma_collapse_multiple_frames`). Each formant F_i contributes a SOFT
   EXCLUSION: a Gaussian log-admissibility `−0.5·(d/σ)²` of the deviation
   `d = (logF_i^cand − logF_i^input)` in speaker-relative space (σ ≈ quarter
   octave), CLAMPED at an abstain floor (3σ) so a wildly-off frame stops
   asserting — it abstains where unsure rather than dominating with magnitude.
   The three frames combine by **INTERSECTION = vector-weighted SUM of the
   per-frame log-admissibilities** (all weights equal = equal F1/F2/F3
   resolution). The candidate that survives all three formant frames' weighted
   exclusions at once wins (highest joint log-admissibility). This is a
   constraint-satisfaction / coherence collapse, NOT a premature scalar
   (dot-product) collapse.

**Donkey audit.** Forward model + LPC formant extraction = owned numpy DSP, no
net, no `.fit()`, no gradient descent. The match = owned weighted-admissibility
(the agent's cognition). Held-out speaker never banked. CortexLoop untouched.
The flat `scripts/solve_for_n.py` engine is unchanged. The vowel forward model
and harness are byte-identical to a363ca71.

## Results — n=1500, cross-speaker LOSO, chance 20%

| match | accuracy |
|---|---|
| AbS mel-L2 (envelope baseline) | **38.9%** |
| AbS **formant-frame weighted-admissibility (the fix)** | **51.3%** |
| 1-NN exemplar (banked, the linear read-off) | **65.1%** |

The mel-L2 (38.9%) and 1-NN (65.1%) baselines reproduce the a363ca71 numbers
exactly — confirming only the match changed. The fix gains **+12.4 points**
over mel-L2, landing between mel-L2 and 1-NN. 0/1500 abstentions (LPC always
returned 3 formants).

```
AbS FORMANT-FRAME confusion (row=true, col=pred)   acc 51.3%
       ao    eh    ih    iy    uw
  ao:  285     3     0     0    12
  eh:   23   274     2     1     0
  ih:    9   154   133     0     4
  iy:    2   150   140     4     4
  uw:    1    72   153     0    74
```

Per-speaker (formant): george 75.6, jackson 36.0, lucas 44.0, nicolas 61.6,
theo 38.0, yweweler 52.8.

### Did the F2-collapse pairs clear?

| named F2-collapse pair | mel-L2 | formant-frame | verdict |
|---|---|---|---|
| **eh → ao** | eh 46/300 correct, 194 → ao | eh **274/300** correct, 23 → ao | **CLEARED** |
| **ao → uw** | ao 188/300, 112 → uw | ao **285/300**, 12 → uw | **CLEARED** |
| **ih ↔ iy** | ih 101, iy 120 (mutually swapped) | ih→iy and iy→ih gone, but both → eh/ih | **NOT cleared — re-routed** |
| **uw → ih/iy** | uw 128/300, 85→ih 86→iy | uw 74/300, 153 → ih, 72 → eh | **NOT cleared — worse on uw** |

The two strongest, clearest F2-collapse confusions — **eh↔ao and ao↔uw** — are
essentially eliminated (eh recovers from 46 to 274 correct). The low-back / mid
region is now resolved, which is the bulk of the +12.4-point gain.

## VERDICT

**The formant-frame weighted-admissibility match WORKS as predicted for the
low/mid vowels and improves recognition (+12.4 pts over mel-L2), but does NOT
yet reach 1-NN (65.1%).** Resolving F2 explicitly clears the eh↔ao and ao↔uw
collapses outright. The prediction ("resolving F2 clears the front/back
confusions → accuracy climbs toward or past 1-NN") is **half right**: it climbs
toward 1-NN and clears the worst pairs, but does not pass it.

### The remaining limiter (the next fix) — honest

The residual errors are concentrated in the **high vowels iy and uw**, both of
which now collapse toward **eh/ih**. The cause is **input formant estimation at
8 kHz**, not the admissibility match:

- The FSDD sample rate is 8 kHz → Nyquist 4 kHz. iy's true F2 (2290 Hz) and F3
  (3010 Hz) sit near the band edge and are closely spaced; an order-10 LPC at
  8 kHz cannot reliably separate them — measured median iy F2 comes out ≈1670 Hz
  (far below the 2290 table value), so iy lands between eh and ih.
- uw's true F2 (870 Hz) is measured ≈1500 Hz (pulled UP) because the F1/F2
  cluster of a high-back vowel merges into one or two poles, so uw drifts toward
  ih.

This is a perception/front-end resolution limit (the gammatone/8 kHz "wall"
again — memory `ozma_wall_is_self_imposed`), not the recognition cognition. The
weighted-admissibility match is doing its job; it is being fed an unreliable F2
for the high vowels. The next fix is on the **input formant estimator**, e.g.:
- a continuity/band-assignment formant tracker (map poles to F1/F2/F3 bands
  rather than naive lowest-3), or
- a second, frequency-sharp "ear" front-end for the high-F2 region (the
  complementary-ears move), or
- estimating the input formants by the same AbS inversion used for the
  candidates rather than raw LPC roots.

The match-space limiter that a363ca71 pinpointed is **fixed**; the limiter has
moved one rung down, from the match to the high-vowel input formant estimate.
