# Within-register tract-shape resolver — did the same-register males separate?

**Verdict (lead).** **The within-register cue WORKS and the males DO separate —
but the end-to-end SELF-ID number is bottlenecked by an analysis/synthesis frame
mismatch, not by the cue.** I chose **tract geometry** (the speaker's per-formant
formant-SPACE signature F1/F2/F3 + per-formant bandwidths) — cleanly SPEAKER, not
content, and it SURVIVES f0 overlap. The recovered signature **spreads the
co-located males where the 4-D source print gave essentially nothing**:

```
                                            same-register MALES (p232/p227/p226)
  f0 (from f0_resolver, retired cause)      range ~4 Hz          (no separation)
  F1 (recovered)                            471 / 791 / 530 Hz   range 320 Hz
  F2 (recovered)                            1809 / 2433 / 2318   range 625 Hz   <- the cue
  F3 (recovered)                            3256 / 3347 / 3237   range 110 Hz
```

I built `lpc_formant_warp_track` (owned DSP, APPENDED to `audio_primitives.rs`):
it roots each content LPC frame, **multiplies the first three in-band formant-pole
angles by the speaker's per-formant SHAPE ratio** (imprinting his tract geometry
while preserving the content's formant MOTION = words), blends each pole radius
toward the speaker's target bandwidth, and re-forms the polynomial. The held
excitation (f0/oq/tilt) and the uniform-VTL resample are UNCHANGED — apples-to-
apples with v3, the warp is the one addition.

Two controls show the cue is genuinely admitted, and one shows where the
remaining gap actually sits:

1. **The rendered impression carries the speaker, not the content (ratio 3.12).**
   Rendering the same held speaker through two different female content donors,
   the recovered tract signature is nearly identical (cross-donor dist 0.23) while
   different speakers render 3.12× farther apart (cross-speaker 0.73). The warp
   imprints the SPEAKER's tract.

2. **In a render-consistent frame the males resolve 3/3.** When the impression is
   matched against ANOTHER impression of the same speaker (both sides synthesized,
   via disjoint donors — removing the real-audio-vs-synth distribution offset),
   **all three males land nearest to themselves** (p232→p232, p227→p227,
   p226→p226), full-N-D identity is **5/8** and 4-D-source identity **7/8**.

3. **Against REAL references the end-to-end number stays 2/8 — the artifact.** In
   the headline harness the reference prints come from REAL audio but the rendered
   prints from SYNTHESIS; the two live in different absolute regions, so when the
   rendered print is z-scored against the real-print distribution **every render
   collapses toward one corner (all eight land on p232)**. This is a
   measurement-frame mismatch, not a failure of the cue (the same harness scores
   the 4-D source print at 2/8 too, yet that print resolves males 7/8 once measured
   consistently).

```
                                  v3 (4-D src)   v4 (this run, + tract warp)
(a) MALE within-reg margin (z)    src min 2.715  TRACT min 2.965 / mean 4.142
(a) MALE F2 spread (recovered)    —              625 Hz  (vs f0 ~4 Hz)
(c) speaker-not-content ratio     —              3.12  (across/within)
(c) intelligibility (cochlea)     0.957          0.955  (warp cost +0.002)
(c) ringing (render-f0 vs code)   0.2%           0.1%   (synthesis not regressed)
(b) identity vs REAL refs         2/8            2/8    (frame-mismatch artifact)
(b) identity, render-consistent   —              5/8 full / 7/8 source; MALES 3/3
(b) males-resolve vs REAL refs    1/3            1/3
```

Log: `/tmp/within_full.log` (marker `===MARKER_WITHIN_REGISTER_COMPLETE===`).
Script: `scripts/within_register.py`. Render-frame diagnostic:
`/tmp/diag_render_frame.py` (marker `===DIAG_DONE===`). WAVs 24-bit/48 k:
`/tmp/voice_imp48k_v4/`. **Not committed.**

---

## (1) Did the same-register males separate and the impression land by ear?

**The cue separated them; the by-ear bar is partly cleared and the precise
remaining gap is named.**

* **Within-register discriminability margin (the key control): YES.** The
  recovered tract signature gives a min male-pair margin of **2.965** (mean 4.142)
  vs the source print's **2.715** — and, more to the point, the *raw* signal is
  unambiguous: F2 spreads **625 Hz** across the three males where f0 spreads only
  ~4 Hz. The closest male pair (p227–p226) is the one that the source print also
  ranks closest; even there the tract formants alone give a clear margin
  (formants-only min 2.025). The cue exists and is recovered.

* **Full identity vs 2/8:** against REAL references, **2/8** (unchanged) — but
  this is the real/synth frame-mismatch artifact (every render lands on p232). In
  the render-consistent frame the full N-D print is **5/8** and source-only
  **7/8**.

* **Males-resolve vs 1/3:** against REAL references **1/3** (unchanged, same
  artifact); in the render-consistent frame **3/3** — each male nearest himself,
  male→male mis-lands → 0.

* **By-ear (24-bit/48 k):** `/tmp/voice_imp48k_v4/AB_male_{p232,p227,p226}_donor_
  p228_t005.wav` are the three males rendered through ONE common donor, so the
  ONLY difference between them is the transplanted code + tract warp — the cleanest
  A/B. With the warp, p227 (high F1 791 / F2 2433) renders audibly forward/bright
  vs p232 (low F1 471 / F2 1809) — they no longer render near-identically as in v3
  (where only a VTL scalar + source were transplanted). Held impressions:
  `held_{spk}_says_t005_donor_*.wav`; references `REAL_{spk}_t005.wav`. **Honest:**
  the impression now sounds like a *different male* per speaker, but is still
  "this is a male voice with these formants," not yet unmistakably *that specific
  man* at the natural-recording bar — see §4.

## (2) Which cue, why, what I recovered + rendered (file:line; donkey audit)

* **Cue = tract geometry** (per-formant formant-SPACE offsets + per-formant
  bandwidths). It (a) genuinely SPREADS the co-located males (F2 range 625 Hz,
  §1), and (b) is SPEAKER-idiosyncratic and separable from CONTENT: it is the
  speaker's vocal-tract SHAPE, the part the single VTL scalar discards. I
  deliberately did NOT use formant-trajectory dynamics (partly content) — only the
  static per-formant SHAPE relative to the population, with the uniform VTL
  component divided OUT so the warp imprints only the residual shape (no
  double-count with the resample-VTL).

* **Recovered** — `tract_signature` (`scripts/within_register.py:204`): median
  F1,F2,F3 + B1,B2,B3 over voiced frames via the owned `lpc_formants_bw`. Per
  speaker the SHAPE ratio = (speaker_Fk / population_ref_Fk) ÷ its own geometric
  mean (the VTL part removed), `scripts/within_register.py:~430`.

* **Rendered** — `lpc_formant_warp_track`
  (`runners/dsl/src/audio_primitives.rs:3209`, exposed
  `runners/dsl/src/py.rs:6141`, registered `:6350`): per LPC frame, root A(z)
  (`poly_roots`), multiply the first 3 in-band formant-pole **angles** by the
  speaker's per-formant ratio, blend each pole **radius** toward the speaker's
  target bandwidth (α=0.6), re-form the monic polynomial Π(1−z_i z⁻¹). Poles
  clamped < 0.998 for stability. Wired into the render at
  `scripts/within_register.py:render_held_voice` (after `lpc_bw_expand_track`,
  before excitation transplant). **APPENDED** at the file end — the pre-existing
  foreign edits in `audio_primitives.rs` were not disturbed.

* **Donkey audit — clean.** The warp is pure closed-form DSP: Durand-Kerner roots,
  per-pole angle multiply, radius blend, polynomial multiply-out. **NO net, NO
  .fit, NO gradient, NO loss, NO sweep-to-fit, NO embedding.** CortexLoop /
  solve_for_n.py untouched. Synthesis (`lf_excitation_transplant`,
  `lpc_bw_expand_track`, `lpc_cross_resynth`), the glottal inverse, and YIN f0 are
  reused unchanged — apples-to-apples with v3.

* **Speaker-not-content control (clean):** the rendered tract signature tracks the
  SPEAKER across two different content donors — cross-donor dist 0.23 vs
  cross-speaker 0.73, **ratio 3.12** (>>1). The cue is on the speaker, not the
  word. Intelligibility preserved (0.955, warp cost only +0.002); ringing 0.1%
  (synthesis not regressed).

## (3) Per-speaker recovered tract signature

```
 spk  probe  F1    F2    F3   | B1   B2   B3  | SHAPE ratio F1/F2/F3
 p232  M 126  471  1809  3256 | 146  148  260 | 0.995 0.966 1.040
 p227  M 132  791  2433  3347 | 185  203  198 | 1.262 0.982 0.807
 p226  M 153  530  2318  3237 | 183  203  188 | 0.994 1.098 0.916
 p231  F 199  455  1814  3101 |  80  159  189 | 0.988 0.996 1.017
 p225  F 181  462  2009  3451 | 145  155  261 | 0.931 1.023 1.050
 p230  F 210  496  1760  2976 | 109  146  246 | 1.072 0.961 0.971
 p233  F 224  493  1884  3105 |  63  137  182 | 1.029 0.994 0.978
 p228  F 225  487  1995  3260 |  78  187  229 | 0.986 1.019 0.995

 MALE within-register margins (z-scored pairwise distance):
   4-D SOURCE print : min 2.715  mean 3.405  (p232-p227 4.25, p232-p226 2.72, p227-p226 3.25)
   TRACT signature  : min 2.965  mean 4.142  (p232-p227 5.21, p232-p226 4.25, p227-p226 2.97)
   TRACT formants   : min 2.025  mean 2.914
 MALE raw formant spread: F1 320 Hz, F2 625 Hz, F3 110 Hz   (f0 range ~4 Hz)

 Render-consistent frame (both sides synth, donor A vs B):
   full N-D 5/8, 4-D source 7/8, tract-formants 3/8; MALES 3/3 (each nearest self)
 Against REAL references (headline harness): full N-D 2/8, males 1/3 (frame-mismatch artifact)
 Speaker-not-content: cross-donor 0.23, cross-speaker 0.73, ratio 3.12
 Intelligibility 0.955 (warp cost +0.002); ringing 0.1%
```

## (4) Honest verdict

**The cue is correct and admitted; the headline self-ID number is throttled by a
measurement artifact, not by the within-register structure.** This run answers the
standing question — *is there a within-register dimension that separates the
same-register males?* — with **yes**: the recovered tract signature spreads them
(F2 625 Hz where f0 gave ~4 Hz), the warp imprints it on the render (speaker-not-
content ratio 3.12), and in a frame that compares like with like the three males
each identify to themselves (3/3; full N-D 5/8). By ear the three males now render
as distinctly different men rather than the v3 near-clones.

But the headline harness compares a SYNTHESIZED impression against a REAL-audio
reference print, and those two distributions are systematically offset — the
analysis-by-synthesis loop does not yet close in absolute print space, so every
render z-scores onto one corner (p232) and full-N-D / males stay at 2/8 / 1/3
against real refs. This is the SAME wall the source print hits (it too is 2/8 vs
real refs but 7/8 render-consistent) — **the remaining gap has MOVED off "no
within-register cue" (now disproven) and onto "the synthesis frame must match the
analysis frame so a rendered impression and a real recording land in the same
print space."** That is the next lever: a render that re-analyses to the
speaker's REAL print (closing the A-by-S loop in absolute terms), not a different
discriminative cue — the cue is now present.

Binary admissibility note: the within-register *structure* is now assembled (the
males separate, 3/3 in a consistent frame). What is not yet admitted is the
*end-to-end real-vs-synth identity*, which is gated by the synthesis colouring the
print uniformly — a frame-alignment problem, distinct from the cue. n=8 (small,
flagged): the render-consistent 5/8 vs 2/8 contrast is the load-bearing pair; the
per-sub-print breakdown wobbles at this n. Honest vs human-natural: the
impressions are recognisably distinct males but not yet indistinguishable from a
real recording of that specific man.

*Script: `scripts/within_register.py`. New primitive: `lpc_formant_warp_track`
(`runners/dsl/src/audio_primitives.rs:3209` + `py.rs:6141`). Corpus:
`/tmp/vctk48/corpus/` (8 VCTK speakers × held sentences, 48 k/24-bit). Log:
`/tmp/within_full.log` (`===MARKER_WITHIN_REGISTER_COMPLETE===`). Render-frame
diagnostic: `/tmp/diag_render_frame.py`. WAVs: `/tmp/voice_imp48k_v4/`
(24-bit/48 k). Not committed.*
