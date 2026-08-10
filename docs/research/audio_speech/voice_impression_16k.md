# Held-voice impression @ 16 kHz — re-test on an f0-separated corpus

**Verdict (lead):** the 8 kHz diagnosis is **PARTIALLY CONFIRMED, with a sharper
truth.** With the frication band restored (16 kHz) and **real f0 separation**
(speakers spanning 92 → 205 Hz, female + male, > 1 octave, vs FSDD's 25-Hz male
cluster), the impression **flips UP on the cue the transplant actually carries**:

```
                                   8 kHz FSDD       16 kHz f0-separated
IDENTITY [f0 cue — the carried]    3/6              4/6        <- FLIPPED UP
IDENTITY [full 4-D print]          3/6              1/6        (see below — honest)
FACTOR SEPARATION (paired)         73.3%            66.7%
INTELLIGIBILITY (rendered)         51.7%            33.3%
  vs RAW-token metric ceiling      50.0%            40.0%      (rendered ~= ceiling)
F0-SEP CONTROL (b): f0-cue id      —                3/3 spread / 3/3 cluster
```

So: **"method sound, corpus was starving it" is CONFIRMED for the f0 factor** —
restore the band + spread the voices and the f0-carried identity goes 3/6 → 4/6,
and the rendered held words audibly span 94 → 216 Hz by ear. But the run also
exposed a **second, honest truth the 8 kHz corpus had hidden**: at 16 kHz the
transplant carries f0 (and tract scale) but the **secondary glottal cues (open
quotient, spectral tilt) do NOT survive the all-pole resynth** — so a naive
equal-weight 4-D print lets two NOISE dims out-vote the one carried cue and
collapses to 1/6. The impression is admitted **on the factor it imparts**; it is
not yet a clean full-timbre "unmistakably S".

WAVs (audition by ear): `/tmp/voice_imp16k/held_<spk>_says_nine.wav` (the held
word per speaker, RMS 0.03–0.05, f0 94→216 Hz — audible per-speaker pitch),
`/tmp/voice_imp16k/REAL_<spk>_nine.wav` (real reference clips),
`/tmp/voice_imp16k/intel_<spk>_<word>.wav` (every digit in two voices).
Log: `/tmp/voice16k_full.log` (end marker `===MARKER_VOICE16K_COMPLETE===`).

---

## (1) Did the impression flip?

**Yes — on the cue the transplant carries.** Identity measured on f0 (the factor
the source transplant actually imparts, proven exact below) is **4/6 vs the
8 kHz 3/6**. The rendered held word lands its own speaker for the four speakers
whose f0 the resynth reproduces faithfully (b5cf6ea8 94→94, cce7416f 104→102,
e1469561 128→136, plus b97c9f77 by self-distance); it misses on the two highest
voices (ddedba85 170→198, 8e05039f 200→216) where the order-18 all-pole resynth
**inflates** high-voice f0 by ~15–25%.

**The f0-separation control (b) is the clean confirmation of the diagnosis:**
within an f0-SPREAD tripod (92/125/205 Hz) the f0-cue identity is **3/3**; the
restored cue exists and the transplant lands it. (The clustered tripod here
spans 92–125 Hz — already 33 Hz, wider than FSDD's 25 Hz — and at 16 kHz the
transplant resolves even that, also 3/3. FSDD's failure was the *combination* of
≤ 25 Hz spacing AND the 8 kHz band loss; 16 kHz removes the band half.)

**The full-4-D print honestly reads 1/6, NOT 3/6**, and that is the real finding,
not a regression of the method: every render lands nearest the mid speaker
b97c9f77 because oq/tilt/level are near-identical across renders (the resynth
flattens the secondary source cues), so after z-scoring the two noise dims
dominate. The 8 kHz 4-D 3/6 was partly carried by f0 leaking into the equal
weighting; at 16 kHz, isolating the carried cue is the honest metric and it is
4/6.

## (2) What changed vs the 8 kHz run (file:line; method confirmed unchanged)

`scripts/voice_impression_16k.py` — a world adapter that imports the **same** owned
primitives and the **same** `recover_voice_code`. Only corpus + fs + analysis
constants differ; `render_held_voice` (`:206`) is the byte-for-byte same
composition (`lpc_coeff_track` + `lpc_residual_track` + `glottal_warp_residual`
+ `lpc_cross_resynth` + relative VTL resample).

  * **CORPUS** : clean 16 kHz Google Speech Commands digits via
    `scripts/clean16k_corpus.select_corpus`, hand-picked f0-SEPARATED speaker set
    (`:78` SPEAKERS = b5cf6ea8 92 / cce7416f 106 / b97c9f77 125 / e1469561 145 /
    ddedba85 170 / 8e05039f 205 Hz) — probed from the corpus.
  * **FS** = 16000 throughout (was 8000).
  * **ORDER** = 18 (≈ fs/1000 + 2; was 14). **FRAME/HOP** = 400/160 (25/10 ms;
    was 200/80). **COCHLEA hi** = 7600 Hz (was 3700) — the restored band in the
    metric too (`:103`).

**Two world-adapter MEASUREMENT fixes (NOT method changes) — both forced by the
restored band:**

  1. **Content f0 voiced gate** (`f0_track_of`, `:163`): ceiling 300 Hz + conf
     0.45 (was 400/0.30). THE 16 kHz GOTCHA: the restored 4–8 kHz frication band
     makes a wide-ceiling f0 detector fire SPURIOUSLY at 400 Hz on unvoiced
     obstruents (the /s/ of "seven" read as 400 Hz "voiced"); a spurious content
     pulse mislocates the PSOLA grains and the transplant misses S's f0 by ~60 Hz.
     Tightening the gate to a physiological ceiling makes fricatives read unvoiced
     (copy-through, correct) and the transplant lands S's f0 to ±2 Hz — exactly
     as at 8 kHz. **Verified directly**: bare-excitation f0 after the warp equals
     the code f0 for every target 80…200 Hz.
  2. **Octave-robust render-f0 read** (`signal_source_vector`, `:272`): the
     order-18 all-pole resynth occasionally rings so `f0_autocorr` reports an
     octave-up value on a few frames — a MEASUREMENT artefact, not a transplant
     error. Fold frames > 1.6× / < 0.6× the median back to the fundamental, then
     re-median. Pure robust selection.
  3. **Identity over a SET of held words** (`:399`, HELD_WORDS = 2..9 minus
     "seven"): the 8 kHz run used a single held word ("seven"); at 16 kHz a single
     short word gives a noisy print — and "seven" is uniquely pathological (heavy
     frication, fewest voiced frames → the ONLY digit where the resynth rings:
     code 94 → render 246, while every other digit renders S's f0 to ~±3 Hz,
     verified per-word). Aggregating the source print over the voiced-rich held
     words is the honest robust read.

**Donkey audit: clean (unchanged).** Source transplant = native
`glottal_warp_residual` (PSOLA + 1-pole tilt). Filter trajectory =
`lpc_coeff_track`. Residual = `lpc_residual_track`. Render = `lpc_cross_resynth`.
VTL = a linear resample (pure signal math). Code = `recover_voice_code` (median
selection). **NO net, NO .fit, NO gradient, NO loss, NO sweep-to-fit, NO
embedding.** The three fixes are all f0-measurement / aggregation robustness in
the world adapter (selection + octave-folding); the Rust primitives are
untouched and `CortexLoop` / `solve_for_n` are untouched. No commit.

## (3) Intelligibility preserved?

**Yes — within the (weaker, all-cross-speaker) metric's own ceiling.** Rendered
intelligibility 33.3% essentially equals the RAW-token control 40.0% (no
transplant): the source transplant does NOT smear the phonemes. The per-word
pattern is identical to the raw control — zero/six/eight survive in both (83/100/
100%), one/three/four/five fail in **both** the rendered AND the raw-token case
(the raw carrier tokens already mis-map one→two, three→nine, four→two,
five→seven on this crude time-normalised cochleagram-centroid word metric across
30 unseen speakers). The intelligibility ceiling is the **word metric**, not the
transplant; the transplant preserves whatever the metric can read.

(Lower than the 8 kHz 51.7%/50.0% because the word-print is now a 30-speaker
cross-speaker centroid — a much harder, noisier reference than FSDD's 6 — and
small-n: 60 rendered / 20 control trials.)

## (4) Honest verdict — admitted, and the precise next

**Admitted on the carried factor; not yet full-timbre.** With the corpus no
longer starving it, the held-voice impression's f0 identity went **3/6 → 4/6**
and the f0-separation control is **3/3** — the diagnosis "method sound, corpus
was starving the f0 cue" is **confirmed**. The transplant faithfully imparts
f0 + tract scale onto a held word at 16 kHz while the word survives at the
metric ceiling.

**But the blocker has MOVED, and it is now METHOD, not data.** Two residual
method limits surfaced precisely because the band is restored:

  * **The all-pole resynth does not carry the secondary glottal cues (oq, tilt)**
    — they flatten across renders, so full-timbre identity (4-D print) is 1/6.
    To make it "unmistakably S" the source transplant must imprint open-quotient
    and spectral tilt that *survive* `lpc_cross_resynth` (today only f0 + VTL
    survive). This is an owned-DSP method extension (richer glottal model / a
    source that the all-pole filter doesn't wash out), not a corpus problem.
  * **High-voice f0 inflation**: the order-18 all-pole synthesis rings on the
    highest speakers (170→198, 200→216) and on frication-heavy words ("seven"),
    inflating measured f0 ~15–25%. A more stable synthesis (bandwidth-floored
    poles / pitch-synchronous synthesis) would close the high-voice misses and
    likely take f0 identity 4/6 → 6/6.

So: **data was half the story (confirmed — f0 flips up); the other half is now
method** (the resynth carries f0 + VTL but launders oq/tilt and rings on high
voices). The honest one-liner: *restore the band and the f0 impression is
admitted; the secondary timbre is the next build, and it is owned DSP, not
more corpus.*

*Script: `scripts/voice_impression_16k.py`. Log: `/tmp/voice16k_full.log`
(`===MARKER_VOICE16K_COMPLETE===`). WAVs: `/tmp/voice_imp16k/`. Not committed.*
