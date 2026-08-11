# Speech forward model — the VOWEL (analysis-by-synthesis recognition)

**Script:** `scripts/solve_for_n_vowel.py`
**Run:** `python -m scripts.solve_for_n_vowel` (full) / `--quick` (smoke)
**Status:** built, run to completion, real numbers below. `SOLVE_FOR_N_VOWEL_COMPLETED`,
exit 0, pgrep-verified (no lingering process). Captured: `/tmp/solve_for_n_vowel_full.log`.

## The rung

The general solve-for-N machine (`scripts/solve_for_n.py`) is proven on the clean
synthetic domain (damped sinusoids = clocks) and composed hierarchically
(`scripts/solve_for_n_recursive.py`, melody = sum of notes). This is the **last hard
plug-in**: the SPEECH forward model. By the diagnostic-ladder discipline, build the
SIMPLEST unit first — the **VOWEL** (a steady source-filter sound) — and measure where it
breaks via analysis-by-synthesis vowel recognition. Later units (consonants, syllables)
are higher rungs; the recursive solve composes them.

The vowel is the **clock machine in GENERATE mode**
(memory `ozma_clock_is_enough_cochlea_is_a_bank_of_clocks`): a glottal SOURCE clock (pulse
train at f0) driving a bank of vocal-tract RESONATOR clocks (formant resonances F1,F2,F3).
Production = the same oscillators run as a source. Recognition = analysis-by-synthesis:
hypothesise vowel + speaker params → synthesise → match → pick the lowest error.

## (1) The forward model wired (donkey audit)

**FORWARD MODEL = owned source-filter DSP** (`VowelSourceFilterModel`):
- **SOURCE**: glottal pulse train at f0 (impulse oscillator), optional 1-pole source tilt.
  Speaker-adjustable f0 (read off the input by autocorrelation pitch — the source clock's
  rate).
- **FILTER**: a cascade of three 2nd-order formant RESONATORS at F1,F2,F3 (the standard
  all-pole vocal-tract model), with fixed bandwidths (80/100/120 Hz). Speaker-adjustable by
  a **formant-scale** (vocal-tract-length factor) searched per candidate.
- **CONTROL / formant table**: **Peterson & Barney (1952)** canonical American-English
  vowel formants (Hz), STATED in the script (`VOWEL_FORMANTS`). e.g. iy=(270,2290,3010),
  ao=(570,840,2410).
- **SYNTHESIS**: source × resonator-cascade → vowel waveform. Pure numpy generative
  function `f(params) → waveform`. **NO trained TTS net, NO `.fit()`, NO gradient descent.**

**RECOGNITION = the agent's analysis-by-synthesis** (`abs_recognise`): for each candidate
vowel, synthesise it while **adjusting the speaker params** (f0 read off input,
formant-scale searched over a 12-point grid) to best match the input; match in a
**speaker-RELATIVE spectral space** (mean-subtracted, range-normalised log-mel envelope —
the formant SHAPE that survives speaker-tilt removal); lowest-error candidate = the
recognition. **NO classifier weights, NO training** — a bounded coordinate search against
the EXACT forward model, exactly the AbS calculus `solve_for_n.py` runs for a sinusoid.

**DATA = REAL human vowels**: steady monophthong nuclei extracted (highest-energy,
low-zero-crossing voiced window) from FSDD digit recordings. Digit→nucleus map (clear
monophthongs only; diphthongs five/nine/eight skipped): 2→/uw/, 3→/iy/, 4→/ao/, 6→/ih/,
7→/eh/. 5 vowels, 6 speakers, 1500 nuclei (300/vowel). **Cross-speaker (LOSO); held-out
speaker NEVER banked.** CortexLoop untouched. Research harness, owned numpy only.

## (2) Synthesis quality

Match-error of the best speaker-adjusted source-filter synthesis to REAL vowels of the
SAME identity vs CROSS identity (relative-envelope space). Same-id < cross-id ⇒ the
synthesis approximates the real vowel's formant structure and the match discriminates.

| vowel | same-id err | cross-id err | margin (cross−same) |
|---|---|---|---|
| ao | 3.281 | 5.298 | **+2.017** |
| eh | 4.956 | 5.589 | +0.633 |
| ih | 4.331 | 5.268 | +0.937 |
| iy | 4.268 | 5.686 | **+1.418** |
| uw | 4.695 | 4.765 | +0.069 (thin) |
| **overall** | **4.306** | **5.321** | **+1.015** |

The synthesis **does** approximate the real vowel's formant structure — every vowel has a
positive same-vs-cross margin (overall +1.015). `ao` and `iy` (the formant-space corners)
separate cleanly; `uw` (high back) has almost no margin.

## (3) AbS vowel recognition — cross-speaker (LOSO)

| recogniser | accuracy | n | chance |
|---|---|---|---|
| **AbS** (forward model, NO exemplars) | **38.9 %** | 1500 | 20.0 % |
| 1-NN (exemplar baseline, banked) | 65.1 % | 1500 | 20.0 % |

Per-speaker AbS: george 47.6 %, jackson 34.0 %, lucas 37.2 %, nicolas 48.4 %,
theo 18.8 %, yweweler 47.2 %.

**AbS confusion (row=true, col=pred):**

| | ao | eh | ih | iy | uw |
|---|---|---|---|---|---|
| **ao** | **188** | 0 | 0 | 0 | 112 |
| **eh** | 194 | 46 | 26 | 11 | 23 |
| **ih** | 60 | 16 | **101** | 121 | 2 |
| **iy** | 22 | 22 | 105 | **120** | 31 |
| **uw** | 1 | 0 | 85 | 86 | **128** |

## (4) VERDICT — good enough for AbS? and the limiter

**AbS recognises vowels cross-speaker WELL ABOVE chance (38.9 % vs 20 %), held-out
speaker never banked — the source-filter forward model is good enough to discriminate
vowels by synthesis.** The prediction held: source-filter approximates the formant
structure → speaker-adjusted match discriminates → AbS above chance. But it is **NOT yet
competitive with the plain 1-NN exemplar baseline (38.9 % vs 65.1 %)**. Honest: the
forward model is real but coarse.

**The limiter is the MATCH SPACE, not the synthesis** (pinpointed by diagnostic, not
guessed):
- The real F1 estimates of the nuclei TRACK the table (eh real-F1 ≈ 523 Hz vs table 530;
  ao ≈ 506 vs 570; iy ≈ 373 vs 270) — **F1 synthesis is correct**.
- The confusions are an **F2-axis collapse**: `eh→ao` (194/300) and `ih↔iy` (105/121) and
  `uw→ih/iy` (171) are exactly the pairs that share F1 but differ in **F2**. The mean
  relative envelopes all peak in the same low bins (~300–600 Hz); the 24-bin mel-envelope
  L2 is **dominated by the F1/spectral-tilt region and under-resolves F2**, the axis that
  separates front (eh,ih,iy) from back (ao,uw). So front-vs-back collapses.

**The next rung's fix** (in priority order):
1. **An F2-resolving / formant-targeted match space** — match on the F1–F2 (and F2–F3)
   formant pattern, not raw mel-envelope L2 that the low-frequency ramp dominates. This is
   the single biggest lever: the synthesis already carries F2, the match throws it away.
2. **Source spectral tilt** — the flat impulse source over-weights high bins inconsistently
   with real glottal −12 dB/oct roll-off; a calibrated source tilt would stabilise the
   relative-envelope shape (currently `src_tilt=0`).
3. **Bandwidths as free (small) AbS params** — fixed 80/100/120 Hz is crude; real vowel
   bandwidths vary and affect peak sharpness in the match.

The 1-NN gap is the honest measure of how much the forward model leaves on the table: a
pure-exemplar memory already does the F2 comparison the AbS match space currently blurs.
Fixing the match space (lever 1) is the vowel rung's remaining work before climbing to
consonants/syllables on the recursive solve.

## Donkey audit (recap)

Forward model = owned source-filter DSP (pulse-train source + 2nd-order resonator cascade
+ Peterson–Barney table). Recognition = the agent's AbS (owned search over speaker params +
L2 match against the exact forward model). NO neural net, NO `.fit()`, NO gradient-descent
training. Real human vowels (FSDD), cross-speaker, held-out never banked. CortexLoop
untouched. The proven `solve_for_n.py` forward-model boundary (synthesise/propose/refine)
is mirrored so the vowel plug-in slots into the same engine.
