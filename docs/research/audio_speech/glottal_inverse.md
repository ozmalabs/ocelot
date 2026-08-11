# Genuine glottal inverse — did the ANALYSIS fix resolve voice identity?

**Verdict (lead).** The named analysis fix **landed and is provable at the
instrument**: a genuine glottal inverse (IAIF + closed-phase covariance LPC +
GCI) **replaces the saturating estimator** and now **recovers the injected
open-quotient across the full range** — inject oq 0.40→0.90 reads back
**0.404→0.904 (Pearson r = +0.973)**, where the old `glottal_params_from_residual`
returned a **flat 0.300** for every injected value. On real VCTK the recovered
codes **SPREAD** for the first time (oq range **0.178** vs the v1 collapse of
**0.021**; f0 range **84 Hz**), and the **spread-preserving cepstral f0** kills
the octave doubles (autocorr read p227 as 379 Hz; cepstral reads 121 Hz).
End-to-end held-voice identity **rose to 2/8** (chance 1/8; v1 was 1/8) and
**f0-identity to 5/8** (v1 3/8), with the **solved synthesis untouched** (ringing
0.4 %, intelligibility 0.957). **But the held-voice impression is NOT YET
admitted at the human-ear bar** — and the run pinpoints the precise remaining
gap: the **three male speakers' recovered f0 still clusters** (~120–122 Hz for
probe 126/132/153), so even though the *estimator itself* now resolves identity
(injection control + recovered-code spread both pass), the male f0 compression on
real speech leaves the 4-D print partly degenerate. Small-n (8 speakers); audition
WAVs are 24-bit/48 k in `/tmp/voice_imp48k_v2/`.

```
                                   48k v1 (saturated)   48k v2 (glottal inverse)
(a) OQ injection read-back         FLAT 0.300           0.404..0.904  r=+0.973  <- FIXED
(a) f0 injection (cepstral)        —                    exact (110..260 to ±0.5%)
(b) real oq spread (8 spk)         0.021 (0.729-0.750)  0.178 (0.611-0.789)      <- SPREAD
(b) real f0 spread                 clustered            84 Hz (121..204)
(c) IDENTITY [full 4-D]            1/8                  2/8
(c) IDENTITY [f0-only]             3/8                  5/8
(c) FACTOR SEPARATION              51.8%                60.7%
(c) RINGING (render-f0 vs code)    0.4%                 0.4%   (synthesis untouched)
(d) INTELLIGIBILITY (cochlea corr) 0.968                0.957
```

Log: `/tmp/glottal_full.log` (marker `===MARKER_GLOTTAL_INVERSE_COMPLETE===`,
EXIT=0). Script: `scripts/glottal_inverse.py`. WAVs: `/tmp/voice_imp48k_v2/`
(24-bit/48 k). **Not committed.**

---

## (1) Did the analysis fix resolve identity?

**The estimator is fixed — proven by the two corpus-independent controls — but the
end-to-end impression is not yet "unmistakably this speaker."** Three things are
now true that were not before:

* **The injection control PASSES (the estimator resolves identity).** Synthesizing
  voices with KNOWN oq/ta/f0 (the owned LF source through a fixed 3-formant tract)
  and running the new estimator: the recovered oq **tracks the injected oq
  monotonically across the whole 0.4→0.9 range** (0.404, 0.616, 0.641, 0.759,
  0.879, 0.904; r = +0.973), where the saturating estimator returned **0.300 for
  all of them**. The cepstral f0 is **exact** (110→110.1, 140→139.9, 180→179.8,
  220→220.2, 260→259.5). This isolates the estimator from the corpus: it CAN read
  the source cue that is provably in the spectrum.

* **The recovered codes SPREAD on real VCTK.** oq now spans **0.611–0.789** (range
  0.178) across the 8 speakers — an **8.5× wider** spread than v1's 0.729–0.750
  (range 0.021), and it orders sensibly (the breathier females p230/p228 read
  highest oq 0.776/0.789; the males lower). The spread-preserving cepstral f0
  removes the octave doubles that collapsed v1's pitch (autocorr reads p227 at
  379 Hz; cepstral reads 121 Hz).

* **End-to-end identity rose, but only to 2/8.** With the SOLVED synthesis
  unchanged, full 4-D identity went 1/8 → **2/8** and f0-identity 3/8 → **5/8**;
  factor separation 51.8 % → **60.7 %**. The render f0 still lands the code f0 to
  **0.4 %** (no ringing — synthesis untouched) and intelligibility holds at 0.957.

**The precise remaining gap.** The diagnostic sub-prints localise it exactly:
`IDENTITY[f0-only] = 5/8` but `IDENTITY[oq+tilt] = 1/8` and `IDENTITY[f0+level]
= 1/8` *in the render*. The estimator resolves oq off real speech (the recovered
CODES spread, 0.611–0.789), but when the rendered audio is re-analysed the
source print partly re-clusters, and — the dominant residual — **the three male
speakers' f0 still compresses**: p232/p227/p226 (probe 126/132/153 Hz) all recover
**~120–122 Hz**. The cepstral estimator is stable (no octave error) but locks the
three low males onto a nearly common quefrency, so the male f0 dimension carries
little speaker information and three of the eight renders land on a male
neighbour. This is the next wall, and it is **f0 RESOLUTION among same-register
speakers**, not the source saturation that v1 blamed (that is now closed).

## (2) What was designed / built (file:line; donkey audit)

A genuine glottal inverse + spread-preserving pitch, both NEW owned-DSP native
primitives, and a v2 recovery that swaps ONLY the analysis:

* **`glottal_inverse_iaif`** — `audio_primitives.rs:2141`, exposed `py.rs:6112`.
  The drop-in replacement for the saturating `glottal_params_from_residual`.
  Operates on the **RAW (radiated) speech frame**, not the over-whitened residual.
  Pipeline (all closed-form, classical):
  - **IAIF** (`iaif_glottal_flow`, `:2055`, Alku 1992): a low-order LPC removes the
    gross glottal+lip tilt → a `tract_order` LPC estimates the vocal tract →
    inverse-filter the original → first glottal estimate → integrate
    (`leaky_integrate`, `:2036`) → re-estimate the glottal contribution → cancel it
    → **re-estimate the tract on the glottis-free signal** → inverse-filter the
    original → glottal-flow DERIVATIVE → integrate → glottal FLOW.
  - **GCI detection** (`detect_gci`, `:2087`): the closures are the large negative
    excursions of the flow derivative; a threshold-on-global-min + refractory
    greedy peak picker yields one GCI per pitch period (verified period-spaced).
  - **CLOSED-PHASE covariance LPC** (`covariance_lpc`, `:1929`, Cholesky on the
    covariance normal equations): per period, the genuinely-closed stretch is found
    data-adaptively as the lowest-energy ~0.15·period window (source ≈ 0 there →
    the tract estimate is source-free) and used as a per-period fallback inverse
    filter where IAIF leaves a period without a clean closure.
  - **oq / ta / tilt fit** (`fit_one_period_deriv`, `:2244`): oq is read in the
    **amplitude domain** off the recovered FLOW (the period-fraction where the flow
    exceeds 50 % of its peak-to-trough range) — robust to the formant ripple the
    imperfect tract leaves in the flow, where single-sample derivative
    landmark-picking was phase-fragile and non-monotone. An affine stretch maps the
    (compressed) amplitude reading onto the LF open-quotient range. ta = the
    return-phase 1/e-decay of the closure; tilt = the flow's low/high energy split.

* **`f0_cepstral`** — `audio_primitives.rs:2335`, exposed `py.rs:6112`. Octave-robust
  pitch: the real cepstrum (log-magnitude DFT → IDFT) peak in the pitch quefrency
  range, cross-checked against the autocorrelation estimate — when the two disagree
  by ~2× (an octave error always reads HIGH) it takes the LOWER (the fundamental).
  Kills the low-male octave doubles (autocorr 379 Hz → cepstral 121 Hz).

* **`recover_voice_code_v2`** — `domains/voice_impressionist.py` (world-adapter
  measurement, median selection — no decisions). Byte-identical to
  `recover_voice_code` EXCEPT the two named swaps: source via `glottal_inverse_iaif`
  (not the residual reader) and f0 via `f0_cepstral` (not plain autocorr).

**Donkey audit — clean.** Every primitive is closed-form classical DSP:
autocorrelation + Levinson, covariance normal equations by Cholesky, FIR inverse
filtering, leaky integration, real-cepstrum DFT/IDFT, amplitude-threshold and
peak-pick landmarking. **NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit,
NO embedding** (grep-verified across the new functions). The SOLVED 48 kHz
synthesis (`lf_excitation_transplant`, `lpc_bw_expand_track`, `lpc_cross_resynth`)
is **reused UNCHANGED** — only the recovery swapped, apples-to-apples. **CortexLoop
/ solve_for_n.py untouched** (not in the diff).

## (3) Recovered-param spread table + identity numbers

```
speaker  probe-f0  v2-f0   f0-err   oq      ta       tilt     level
 p232  M   126     120.6    4%     0.651   0.0769   +30.57   7.20
 p227  M   132     121.2    8%     0.611   0.0837   +28.88   7.54
 p226  M   153     121.8   20%     0.657   0.0938   +29.62   7.38
 p231  F   199     172.7   13%     0.686   0.1151   +28.83   7.23
 p225  F   181     170.2    6%     0.661   0.1074   +28.82   7.25
 p230  F   210     200.0    5%     0.776   0.1240   +28.24   7.23
 p233  F   224     204.3    9%     0.714   0.1189   +27.39   7.30
 p228  F   225     200.8   11%     0.789   0.1352   +28.60   7.30
 ----  spread     121-204         0.611-0.789       27.4-30.6
 v1    spread     clustered       0.729-0.750 (0.021 range)
```

Identity: full-4D **2/8** (v1 1/8), f0-only **5/8** (v1 3/8), oq+tilt 1/8,
f0+level 1/8, factor-sep **60.7 %** (v1 51.8 %). Ringing **0.4 %**,
intelligibility **0.957**. By-ear 24-bit/48 k:
`/tmp/voice_imp48k_v2/held_<spk>_says_t005_donor_<donor>.wav`,
`REAL_<spk>_t005.wav`, `CONTENT_donor_<donor>_t005.wav`.

## (4) Honest verdict

**The analysis fix is real and proven at the estimator, but the held-voice
impression is not yet admitted.** This is a clean *fix-the-fixer* step, not a
regression: the v1 doc named the wall as "the read-back estimator saturates at
0.30 and f0 loses its spread" — **both are now closed in owned DSP** (injection
r=+0.973, recovered-code spread 8.5×, octave doubles gone), and the residual is a
*different, narrower* gap: **f0 resolution among same-register (male) speakers**.
The three males collapse to ~121 Hz, so a third of the 4-D prints land on a male
neighbour and full identity reads 2/8 — above v1's 1/8 (chance) but below the
human-ear "unmistakably this speaker" bar. Binary admissibility: the 4-D identity
structure is now fed by an instrument that DEMONSTRABLY resolves oq and f0 in
isolation, so the cue is no longer flat — but one dimension (male f0) is still too
compressed on real speech for the conjunction to assemble.

**Next build (owned-DSP, not corpus).** A higher-resolution per-speaker f0 that
separates same-register voices (the cepstral peak quefrency is integer-binned at
48 kHz — a parabolic-interpolated / longer-window cepstral or a YIN-style
difference-function f0 would sharpen the male 120–155 Hz band), plus carrying the
now-spread oq/ta/tilt code through to the render print without the re-analysis
re-clustering (the oq+tilt render sub-print is 1/8 despite the CODES spreading
0.611–0.789 — the render→re-analysis round-trip loses some of the recovered
spread). With sharper male f0 the carried-and-now-readable source cues should let
the 4-D conjunction assemble toward the human-ear bar — the synthesis and the
estimator are both already there.

*Script: `scripts/glottal_inverse.py`. Corpus: `/tmp/vctk48/corpus/` (8 VCTK
speakers × 8 sentences, 48 k/24-bit). Log: `/tmp/glottal_full.log`
(`===MARKER_GLOTTAL_INVERSE_COMPLETE===`). WAVs: `/tmp/voice_imp48k_v2/`
(24-bit/48 k). New primitives: `runners/dsl/src/audio_primitives.rs` +
`py.rs`; recovery: `domains/voice_impressionist.py:recover_voice_code_v2`.
Not committed.*
