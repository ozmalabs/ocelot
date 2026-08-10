# Stage 5 — FRICATION / HIGH-BAND DETAIL (the harder manner contrasts), CLEAN 16 kHz

The agent executes STAGE 5 of its OWN self-designed curriculum
(`docs/toolbox_and_curriculum.md`, the Stage-5 definition ~line 386): *resolve
/s/–/sh/–/f/ and other turbulent-noise contrasts — the high-band spectral-tilt +
aperiodic-noise detail.* Acting on its own ordering principle 5 (frication is the
LAST manner detail because it needs the high-band + temporal periodic/aperiodic
machinery the earlier stages build).

Driver: `scripts/stage5_frication_gate.py`. Full log: `/tmp/stage5_full.log`
(ends `===MARKER_STAGE5_FRICATION_GATE_COMPLETE===`, exit 0, pgrep-verified done).
Corpus: CLEAN 16 kHz Speech Commands digits, 1752 tokens, 30 speakers, NOT
downsampled — the intact 4–8 kHz frication band (gone at 8 kHz, the K10 wall).

---

## (1) VERDICT — the gate FIRES

**STAGE-5 FRICATION STRUCTURE ADMITTED (confusions shrink AND anchor safe): True.**

- **Fricative confusions SHRINK with W7:** overall fricative-pair confusions
  **275/938 → 259/938** (+16 separated), **4/6** named pairs shrank, **5/6** pairs'
  mean cross-speaker margin improved.
- **Anchor safety (T9) holds:** the vowel/sonority recogniser is NOT dragged — its
  cross-speaker cluster gap **d' = 0.331** is untouched (fusion only ADDS the W7
  prong, never modifies the anchor representation), and the fused decision does not
  harm sonorant digits (0.106 → 0.117, +1.1 pts).

The systematic fricative confusions shrink WITHOUT dragging the vowel recogniser —
exactly the Stage-5 readiness signal. Structure-admitted, NOT a held-out accuracy.

---

## (2) What was built — W7, the frication/turbulent-noise cue

`scripts/stage5_frication_gate.py:w7_frication_cue` (def at `:165`), the agent's
owned 4-dim descriptor over the intact 4–8 kHz band:

- **[0] high-band energy fraction** (E_>3kHz / E_total) — frication PRESENCE.
- **[1] high-band APERIODICITY** = `1 − periodicity-strength`, from the NATIVE T4
  TFS chain (`gammatone_band → band_autocorr → summary_autocorrelogram →
  periodicity_track`) run on HIGH-band 4/5.5/7 kHz gammatone channels
  (`_hi_band_aperiodicity`, `:104`). Tall ACF peak = periodic (voiced high
  harmonic); flat ACF = aperiodic (turbulent frication noise). This is the **T4
  periodic-vs-aperiodic axis gated to the frication band** — the cue's core.
- **[2] high-band spectral TILT** — least-squares slope across the 4/5.5/7 kHz
  channel energies (place cue: /s/ high & flat-to-rising vs /f/ diffuse/low).
- **[3] high-band turbulence ONSET** position (energy-weighted temporal centroid of
  the >3 kHz energy).

**Gated in (T13):** `gate_in_w7` (`:214`) registers W7 as a graph `Cue` node on the
agent's `FrontEnd` and sets `active=1.0`; the extractor is registered in
`AF.CUE_EXTRACTORS`. Front end after gating:
`['gammatone_flat', 'fft_ear', 'allpole_envelope', 'w7_frication']`.

**Fused (T8):** the per-word frication admissibility is a soft excluder
`a_w7(w)=exp(−d_w7(w)/τ_w7)` fused with the anchor by weighted-admissibility
`argmax_w a_anchor(w)·a_w7(w)^weight` (log-space soft-AND). W7 reliability
**weight = 0.234** = above-chance (W7-alone train acc 0.310, chance 0.100)
normalised to [0,1] — a MEASUREMENT, not a swept knob. τ scales = measured
per-channel across-digit spread (τ_anchor 0.220, τ_w7 2.020).

**Architecture audit (donkey):** W7 is owned DSP built FROM the native T4 chain +
owned numpy spectral statistics; NO new Python cognition/decision — the cue
extractor is mechanical I/O-boundary DSP, the recognition decision is the native
graph DtwTo (anchor) + the native T8 weighted-admissibility fusion. NO net, NO
.fit, NO gradient, NO loss, NO sweep-to-fit. The anchor = Stage-3 native
VTL-invariant DtwTo, imported UNCHANGED. CortexLoop / solve_for_n / runners
untouched. 16 kHz NOT downsampled.

W7 sanity (mean per digit, raw): the /s/-onset digits stand out on hi_frac —
**six 0.304, seven 0.103** vs the vowel/sonorant digits (one 0.004, nine 0.009);
the /f/ digits four/five (0.009) and /th/-/z/ three/zero (0.023/0.055) are lower
(most /f/ /th/ energy is broadband-weak, the harder contrast), but aperiodicity and
tilt carry the residual separation.

---

## (3) Per-confusion-pair numbers + anchor safety

Cross-speaker LOSO-style (3 proto speakers held for templates, 27 scored). Margin =
log-admissibility(own digit) − log-admissibility(confusable partner); >0 = correctly
separated. Confusion count = tokens with margin ≤ 0.

| pair        |   n | margin anchor | margin +W7 | conf anchor | conf +W7 |          |
|-------------|----:|--------------:|-----------:|------------:|---------:|----------|
| six/seven   | 154 |        −0.105 |     −0.087 |      90/154 |   91/154 | (worse by 1) |
| four/five   | 158 |         0.402 |      0.426 |      19/158 |   15/158 | SHRUNK   |
| three/zero  | 156 |         0.304 |      0.341 |      35/156 |   29/156 | SHRUNK   |
| six/three   | 154 |        −0.091 |     −0.062 |      90/154 |   89/154 | SHRUNK   |
| seven/zero  | 158 |         0.324 |      0.308 |      33/158 |   33/158 | flat     |
| four/six    | 158 |         0.575 |      0.670 |       8/158 |    2/158 | SHRUNK   |

- **Overall: 275/938 → 259/938** confusions (+16 tokens separated).
- **4/6** pairs shrank; **5/6** improved mean margin; 1 pair (six/seven) got 1 token
  worse — the hardest contrast (both pure /s/-onset; the place/aperiodicity cue is
  weakest where the two words share the SAME fricative).
- The largest wins are **four/six** (8 → 2: /f/ vs /s/, the cleanest place split)
  and **four/five** (19 → 15) — exactly where W7's high-band tilt/aperiodicity bites.

**Anchor safety (T9):**

- Anchor cross-speaker cluster gap **d' = 0.331** (within 0.6165 ± 0.118, between
  0.6511 ± 0.090, separation 0.672 of tokens) — the Stage-3 invariant, untouched.
- Sonorant/vowel digits (one, two, eight, nine) under the FUSED decision:
  **0.106 → 0.117** (+1.1 pts) — W7 does not drag them.

---

## (4) Honest verdict — Stage 5 COMPLETE, with one caveat named

**Stage 5 is COMPLETE / structure-admitted.** W7 (high-band spectral-tilt +
aperiodic-noise, built from the native T4 periodic-vs-aperiodic chain) gated in and
fused by T8 makes the systematic fricative confusions shrink (275 → 259, 4/6 pairs)
while the anchor's cross-speaker separation (d' = 0.331) holds — the readiness gate
fires.

**Caveat (the honest limit):** the absolute sonorant-digit recognition under this
cross-speaker template scheme is near chance (anchor 0.106), so "not dragged"
(0.106 → 0.117) is a WEAK accuracy-based safety signal in isolation — the LOAD-
BEARING anchor-safety evidence is the **structural** d' = 0.331 being untouched
(the fusion only adds the W7 prong, never modifies the anchor trajectory, so it
CANNOT drag the anchor representation). The residual hard contrast is **six/seven**
(both pure /s/-onset, 1 token worse): W7's place/tilt cue separates /s/ from /f/
cleanly (four/six 8 → 2) but cannot split two SAME-fricative words — that needs the
finer /s/-vs-/sh/ spectral-peak-frequency detail, a sharper-frequency W7 ear
(the named next refinement, not a Stage-5 blocker).

The gate's signal is the confusion-shrink + anchor-safety STRUCTURE, not a held-out
LOSO accuracy ([[ozma_no_premature_testing_mid_curriculum]]).
