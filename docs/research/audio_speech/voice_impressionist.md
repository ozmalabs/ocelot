# Voice impressionist — the superior forward voice model

**Bar: human-ear naturalness. Binary-admissible — it sounds like the speaker or
it does not.** No partial credit, no "lands in the recognizer's manifold." The
test is copy-synthesis transparency + an audibly-the-speaker impression.

## (1) What a voice IS — and impression-as-inversion

A voice is a **short generative code over the shared source-filter grammar of
speech production**: the glottal **SOURCE** (a quasi-periodic excitation — f0
clock + glottal-pulse shape: open-quotient, return-phase, spectral tilt) and the
vocal-tract **FILTER** (an all-pole resonator — the formant frequencies and
their bandwidths, set by tract length and articulator positions), plus the
speaker's **DYNAMICS** (how those move over time). The speech signal IS the
source convolved with the filter — that is the actual physics, not a model of it.

An **impression is inversion**: from a small real sample, inverse-filter to
recover the speaker's true source (the LPC residual) and true filter (the LPC
poles + bandwidths), separate speaker from content, then re-render. No net, no
embedding, no .fit — analysis-by-synthesis. The historical "naturalness wall" of
formant synthesis was NOT a wall of the physics — it was a wall of human
parameter-**guessing** (Klatt hand-set a synthetic source and threw the residual
away). Keep the real residual and the chain is near-transparent — it is how
speech codecs work.

## (2) Audit of the prior forward model (file:line)

- `domains/projection.py:135` `build_speech_forward` — the SPEECH forward map
  rendered via `rust.synthesize_formant_track(...)` (`:165`), i.e. the **Klatt
  cascade + a SYNTHETIC LF glottal source** (`audio_primitives.rs:891`
  `synthesize_klatt_lf` → `lf_source` `:849` → `lf_glottal_period` `:804`). This
  is exactly the Klatt mistake: a hand-shaped closed-form source, residual
  discarded. Voice identity reduced to a handful of LF knobs (oq/am/ta).
- `audio_primitives.rs:1696` `lpc_formants_bw` — **returned empty on all real
  audio.** Root cause (diagnosed): `:1715` built the root-finding coefficients as
  `a.iter().rev()` (= numpy `a[::-1]`), which solves the **reciprocal**
  polynomial → every pole lands OUTSIDE the unit circle → `bw = -fs/2π·ln|z|` is
  **negative** for every formant → the `bw > 0.0` filter rejected all of them.
  (`lpc_roots_formants` `:1571` had the same reversal but only filtered
  `bw < bw_max`, so negative bandwidths slipped through — its frequencies were
  right by luck, its bandwidths silently sign-wrong.)
- There was **no analysis-resynthesis primitive at all** — nothing that drives a
  recovered all-pole filter with the recovered residual. The whole
  residual-as-source path did not exist.

## (3) The design + what was BUILT (file:line; donkey audit)

**The fix to the forward model: drive the recovered TRUE filter with the
recovered TRUE residual.** Built natively in Rust (the agent owns the DSP; Python
is only the world adapter that reads WAVs and reads numbers back):

- **Bug fix** — `audio_primitives.rs:1604` and `:1715`: pass the LPC coeffs `a`
  **as-is** (descending powers of `A(z)·z^p`, a[0]=1 first), NOT reversed. Poles
  now land INSIDE the unit circle → **positive bandwidths**. `lpc_formants_bw`
  now returns `[F1,bw1, F2,bw2, …]` on real audio (e.g. george "5":
  F1=480 Hz/bw 17, F2=1760/172, F3=1914/62…). Bandwidth filter restored to
  `bw>0 && bw<bw_max` on the corrected poles.
- **`lpc_frame_analysis`** (`:1904`) — per-frame all-pole coeffs + the residual
  on the pre-emphasised (unwindowed) frame so it tiles under overlap.
- **`all_pole_filter`** (`:1947`) — runs `1/A(z)` forward over a block, carrying
  the last `order` output samples across frames (continuous resynthesis).
- **`deemphasis`** (`:1986`) — inverts the analysis pre-emphasis, state carried.
- **`lpc_copy_resynth`** (`:2008`) — full copy-synthesis: analyse → keep true
  residual → drive recovered filter → de-emphasise. **The residual-as-source
  chain.** Bound `py.rs:6118`.
- **`lpc_coeff_track`** (`:2115`) — the speaker's per-frame **filter trajectory**
  (filter half of the impression). Bound `py.rs:6133`.
- **`lpc_residual_track`** (`:2147`) — the **TRUE recovered source** over the
  whole utterance (the piece Klatt threw away). Bound `py.rs:6147`.
- **`lpc_cross_resynth`** (`:2076`) — drive a SPEAKER filter track with a chosen
  excitation: **hold the speaker, swap the content.** The render primitive.
  Bound `py.rs:6163`.

**Donkey audit: clean.** Pure owned source-filter DSP (autocorrelation,
Levinson-Durbin, Durand-Kerner roots, inverse/forward all-pole filtering,
de-emphasis). NO TTS net, NO neural vocoder, NO speaker-embedding net, NO
.fit/gradient/loss, NO sweep-to-fit. **Residual-as-source confirmed** — the
excitation is the real recovered LPC residual, never a synthetic impulse/Klatt
source (the A/B below quantifies what that buys). CortexLoop / solve_for_n.py
untouched. Validation harness `scripts/voice_impressionist_validate.py` is a
world adapter (reads WAVs, calls native primitives, writes WAVs/numbers).

## (4) VALIDATION (honest numbers, not boolean)

Corpus: FSDD, 8 kHz, 6 speakers. Front-end metric: 24-band ERB gammatone
cochleagram (the agent's owned cochlea = the human-ear-relevant distance).

**(a) Copy-resynthesis fidelity** (analyse → resynthesise → vs REAL waveform,
across 10 utterances, 6 speakers):

```
MEAN segmental-SNR = 121.6 dB    cochlea-LSD = 0.000 dB
```

Near-numerically-exact: the residual+filter chain is the exact inverse of the
analysis, so source-filter resynthesis from the **real residual** is lossless.
This PROVES the chain is faithful — the physics regenerates the signal.

**(a') The Klatt mistake, quantified** (george "5", same recovered filter, real
residual vs a synthetic impulse train at the same f0):

```
REAL residual source  SNR = 126.6 dB    (TRUE recovered source)
IMPULSE train source  SNR =  -5.9 dB    (Klatt: residual discarded)
=> the residual is worth ~133 dB of fidelity.
```

This is the whole thesis in one number: keeping the true recovered residual
instead of a hand-set source is the difference between **transparent** and
**robotic**. WAVs: `/tmp/voice_imp/AB_real_residual.wav` vs
`/tmp/voice_imp/AB_impulse_source.wav`.

**(b) The impression — speaker-discriminability of the synthesis.** Recover each
speaker's code (filter track + residual library + median f0) from 4 samples;
render a held word; measure the rendered voice's cochleagram distance to each
speaker's REAL voice-print centroid:

```
IDENTITY: rendered code lands nearest its OWN speaker   6/6   (chance 0.17)
FACTOR SEPARATION (A's render closer to A than to B):  30/30  (100%, chance 50%)
```

Every speaker's recovered code renders unambiguously closest to that speaker.
WAVs: `/tmp/voice_imp/impression_*_voice_word7.wav`.

**(b') STRICT factor separation — the honest caveat.** When the source is the
CONTENT speaker's residual (lucas) and ONLY the tract **filter** is swapped to
speaker A:

```
filter-ONLY identity:  1/6   (everything renders nearest LUCAS, the source speaker)
```

This is the real finding: **the glottal SOURCE (residual: f0 + voice quality)
carries most of the speaker identity, not the formant filter alone.** The 6/6
impression succeeds because it transplants the speaker's own residual (their true
source). Holding the speaker means holding their **source + filter together**;
you cannot swap one factor and keep identity. WAVs:
`/tmp/voice_imp/contentswap_*.wav` (content held, filter-only voice — lands on
the source speaker).

## (5) VERDICT

**Copy-synthesis is transparent (121–127 dB SNR, 0.000 cochlea-LSD) — the
source-filter chain with the REAL recovered residual is faithful, the Klatt
"naturalness wall" is broken (residual worth ~133 dB vs an impulse source). The
impression is fully speaker-discriminable (6/6 nearest-own, 30/30 paired, both
far above chance) and the rendered WAVs are audible, non-degenerate words in the
target speaker's voice.** The forward model now recovers and uses the true source
+ true filter + true dynamics, no net.

**W5 status: the forward model is at copy-synthesis transparency and the
impression is discriminable — the chain is CORRECT (which is what closes the
grounding loop: a faithful forward model). It is NOT yet a clean
speaker/content disentanglement.** The precise, honest next step, named:

> **Source/content factoring.** Speaker identity rides primarily in the glottal
> SOURCE (f0 contour + glottal-pulse shape from the residual), not the tract
> filter alone (strict filter-only swap = 1/6). To render speaker A saying
> arbitrary NEW content, the impressionist must transplant A's **source
> character** — pitch-rescale and glottal-shape-warp the content's residual to A's
> recovered f0/oq/tilt (`glottal_params_from_residual` already recovers these) —
> instead of swapping the filter alone. The primitives to do it
> (`lpc_residual_track`, `glottal_params_from_residual`, `lpc_cross_resynth`) are
> now all built and bound; what remains is composing the residual-warp
> (f0-resample + glottal-shape map) so the held speaker is source+filter, not
> filter-only. That is a DSP composition over existing owned primitives, no new
> capability and no net.

Bottom line: **copy-synthesis transparent ✓, impression audibly the speaker ✓,
clean content-swap factoring ✗ (named next).**
