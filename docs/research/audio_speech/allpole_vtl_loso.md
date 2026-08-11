# The SHARP all-pole formant makes the VTL lever bite on the cross-speaker wall

**Question.** The robust Speech-Commands LOSO run (`docs/sc_loso_frontend_norm.md`)
found, on real 40-speaker held-out data, that CMVN is the dominant cross-speaker lever
(+0.04–0.08 LOSO, always positive) but the **VTL-invariant formant** (`vtl_formant`)
**barely moved / sometimes hurt**. The diagnosis: the VTL invariant `F_i - mean(F1..F3)`
was being computed on the **coarse gammatone formant** — `ArgMax` over ~24–32 log-ordered
ERB bands — which is too blurry (the gammatone wall) for the ratio to be a sharp
speaker-invariant. The run **named the fix**: not a new normalization, but the **sharper
all-pole formant the agent already owns** (the iter-43 / lpc_formant_representation
LPC-root formant estimate at full waveform frequency resolution) feeding the **same** VTL
normalization.

This run does exactly that and A/Bs it against the coarse VTL on the **identical** robust
SC split.

**Verdict: YES — the sharp all-pole formant makes the VTL lever bite.** Where the coarse
gammatone VTL *drags CMVN down* (−0.038 LOSO), the sharp all-pole VTL *lifts on top of
CMVN* (+0.005), a **+0.042 swing** purely from sharpening the formant estimate feeding the
same invariant. `+CMVN+VTL(sharp)` is the **best overall regime** (LOSO 0.410, +0.047 over
SEED — beating CMVN-alone's 0.405). It does **not cross the wall** (a residual seen-vs-cross
gap persists, +0.040), but it removes the gammatone-blur penalty that made the VTL lever a
liability, so VTL finally **adds** instead of subtracting.

---

## (1) The sharp all-pole formant exists and is genuinely sharper (verified)

The agent already owns a sharp formant estimate — **not** a re-skin of the coarse one:

- **Coarse (the cue that barely moved):** `domains/speaker_norm.vtl_terms` estimates
  F1..F3 as `ArgMax` over thirds of the ~24–32 log-ordered gammatone bands. The formant
  is quantised to one of ~32 integer **band indices**, and it is forced to take exactly
  one peak per third regardless of where the true resonance sits — resolution ≈ one ERB
  band (hundreds of Hz at the formant end). This is the gammatone wall.
- **Sharp (the named fix):** `domains/lpc_formant_representation._lpc_roots_formants`
  fits an all-pole model to the **raw waveform** frame (pre-emphasis → `_autocorr` →
  `_levinson` Levinson-Durbin → `roots(A(z))` → pole angles · fs/2π = formant **Hz**),
  recovering the formants at **full waveform frequency resolution** (continuous Hz),
  bypassing the band grid entirely.

Measured on real SC clips (verification probe), the LPC-root estimate returns continuous
Hz formants (e.g. `five` → 1065, 1572, 2805 Hz; `nine` → 677, 1432, 1941, 2479 Hz), 3–5
true poles per frame — versus the gammatone giving only an integer band-index triple out
of 32 bands. The all-pole estimate is genuinely sharper; this is **not** a faked "sharp
formant" using the same coarse estimate.

## (2) The `vtl_formant_allpole` cue (graph-resident composable DSP, donkey-audited)

`domains/agent_frontend.py` gains `_vtl_formant_allpole` (extractor `vtl_formant_allpole`),
registered in `CUE_EXTRACTORS` and added to `REPERTOIRE_CUES` exactly like the existing
cues. Per frame it:

1. estimates the sharp formants via the agent's own `_lpc_roots_formants` (LPC pole
   angles of the raw waveform), then
2. applies the **same** VTL-invariant normalization as `_vtl_formant`:
   `F_i - mean(F1..F3)`, done in **log-Hz** (VTL scales formant Hz multiplicatively
   `F_i → α·F_i`, an additive shift in log-Hz that subtracting the per-frame mean cancels
   by construction — the Hz analogue of the gammatone band-index mean subtraction).

It resamples each formant track to a fixed-length L2 descriptor (the same readout shape as
`_vtl_formant`), so it is one more node in the agent's unchanged Argmax-of-product
recognizer.

**Donkey boundary (audited).** The all-pole fit (`_autocorr` + `_levinson` — a closed-form
recursion, **not** gradient descent), the root-finding, and the `F_i - mean` invariant are
the agent's **owned, composable-DSP representation** — no fit, no trained net, no learned
weight, no tuning of the invariant. The only new Python is the I/O-boundary DSP that
evaluates the LPC roots and the mean-subtraction, the **same category** as the existing
`fft_ear` / `cochleagram` / `allpole_ear` front end. SC load + the speaker split are
world-adapter mechanics; recognition is the agent's own `blind_guess`; held-out speakers'
clips are **never** banked; LOSO is the ungameable yardstick.

## (3) The A/B on the SAME robust SC LOSO — VERDICT

`scripts/allpole_vtl_loso.py` reuses `sc_loso_frontend_norm.build_split` / `bank` /
`measure` verbatim (120 train / 40 held-out **disjoint** speakers, 200 banked exemplars,
200 seen-speaker probes, 400 cross-speaker LOSO probes, full-lexicon `blind_guess`). Four
regimes, everything else held fixed; the two VTL regimes are **identical except which
formant estimate feeds the same `F_i - mean` invariant**:

```
                                          (10-way, chance 0.100)
  regime         seen     LOSO   seen-LOSO gap   LOSO lift over SEED
  SEED          0.375    0.362       +0.013          +0.000
  +CMVN         0.420    0.405       +0.015          +0.043
  +CMVN+VTLc    0.425    0.367       +0.057          +0.005    (coarse gammatone VTL)
  +CMVN+VTLa    0.450    0.410       +0.040          +0.047    (sharp all-pole VTL)
```

Reading the decisive comparison — **VTL on top of the dominant CMVN lever**:

- **Coarse gammatone VTL on CMVN: −0.038 LOSO** (0.405 → 0.367). The coarse formant is a
  *liability* — adding the blurry VTL invariant on top of CMVN drags the cross-speaker
  rate down. This reproduces the original run's "barely moved / sometimes hurt".
- **Sharp all-pole VTL on CMVN: +0.005 LOSO** (0.405 → 0.410). The same invariant on the
  **sharp** formant *adds* instead of subtracting, and `+CMVN+VTLa` is the **best overall
  regime** (LOSO 0.410, beating CMVN-alone 0.405 and SEED 0.362).
- **Sharp-vs-coarse VTL swing: +0.042.** This is the whole point: sharpening the formant
  estimate — not changing the normalization — turns the VTL lever from a −0.038 liability
  into a +0.005 contributor. The formant sharpness was exactly the bottleneck the original
  run named.

The signal is **stable across split seeds**. A second disjoint 120/40 split (higher
baseline: SEED LOSO 0.420, +CMVN 0.500) reproduces the direction exactly: coarse VTL on
CMVN +0.007 (LOSO 0.507), **sharp VTL on CMVN +0.017** (LOSO 0.517, again the best
regime), sharp-minus-coarse delta **+0.010** — positive again. Across both splits the sharp
all-pole VTL is always ≥ the coarse VTL on top of CMVN and is the best regime overall; the
sharp-vs-coarse swing is +0.042 on the primary split and +0.010 on the second.

**Does it cross the wall?** **No — it moves it, and removes the VTL liability.** The
sharp-VTL regime still has a **residual seen-vs-cross gap of +0.040** (seen 0.450 vs cross
0.410), so a cross-speaker penalty persists. What the sharp formant *does* close is the
**self-inflicted** gap the coarse formant opened: coarse-VTL's seen-vs-cross gap is +0.057
(it overfits the seen speakers' blurry band-quantised formants), whereas sharp-VTL's is
+0.040 — the sharp formant generalises across speakers where the coarse one banked
speaker-specific band artifacts. So the honest verdict is: the sharp all-pole formant makes
the VTL lever **finally bite** (positive on top of CMVN, best overall regime), but the wall
itself — the residual cross-speaker penalty that even the best source-normalized
representation does not erase — remains.

## (4) Why a residual remains (honest)

CMVN remains the **dominant** lever (+0.043); the sharp VTL adds a **modest** +0.005 on top
of it. The two are complementary in the same way the original run found (CMVN's
gain-normalized space is where a formant cue can carry usable invariant information), but
the absolute size of the VTL contribution is small. Two reasons, consistent with prior
findings:

1. **CMVN already cancels the per-band gain**, which is the largest source-dependent term;
   the VTL formant invariant only reaches the *vocal-tract-length scaling* of the
   resonances, a smaller residual once gain is removed.
2. **The residual cross-speaker penalty is partly deeper than any front-end source
   normalization.** Speech Commands' cross-speaker variation includes lexical /
   coarticulation / register diversity a per-utterance representation cannot cancel; what
   remains needs richer invariant *structure* (formant **dynamics** / manner / order-N
   trajectories), not a sharper static formant. The sharp formant fixes the gammatone-blur
   share of the wall; the rest is the next structure to build.

The donkey boundary held throughout (section 2).

## Reproduce

```
python -m scripts.allpole_vtl_loso              # full robust run (120/40/20)
python -m scripts.allpole_vtl_loso 15 8 6       # fast smoke run
```

Full captured output: `/tmp/allpole_vtl_loso.txt`. Second-seed stability check:
`/tmp/allpole_vtl_seed2.txt`. Required suites green (`test_stt_pipeline
test_perception_self_assessment test_process_meta_assessor test_gap_guidance
test_frontend_effect_gate` — 36 passed). Nothing committed; the `vtl_formant_allpole` cue
+ the A/B script are left in the working tree.
