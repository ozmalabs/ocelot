# Center-surround salience front end vs the cross-speaker feature wall

**Question.** The combine is closed and the cue / source-normalization levers are
exhausted; the residual lever is the FEATURE / cross-speaker RELIABILITY. Does a
CENTER-SURROUND SALIENCE front end on the cochleagram break (or move) that wall?

**Hypothesis** (user, `ozma_analogical_transfer` — vision retina/LGN center-surround
-> auditory spectro-temporal contrast). A center-surround filter on the (frames x
bands) cochleagram attacks cross-speaker invariance on two axes at once:
(a) **local contrast normalizer** — each time-freq point relative to its local
surround cancels the speaker-common slowly-varying offsets (global tilt, level, the
slow envelope the VTL shift rides on), which live in the wide surround blur; (b)
**salience filter** — amplifies what stands out (formant peaks, spectral edges,
onsets, where the phonetic info lives) and discards the flat speaker-specific
background (blurred away by both Gaussians). Prediction: CS lifts cross-speaker LOSO
and/or tightens the seen-vs-cross gap.

## Build (donkey-clean)

`domains/agent_frontend.center_surround(M, sigma_t_c, sigma_f_c, sigma_t_s, sigma_f_s)`
— difference-of-Gaussians on the cochleagram: `center` = M blurred at the small center
sigmas, `surround` = M blurred at the wider surround sigmas, output = **signed**
`center - surround` salience map. Separable Gaussian convolution (`np.convolve` per
line, reflect-padded) + a subtraction — the SAME center-surround DoG the vision front
end uses (`domains/vision.py`: `_blur_keep_dims(base,2) - _blur_keep_dims(base,16)`).
No fit, no net, no searched param beyond the small reported {axis, width} ablation set.

Wired as two front-end cues the agent owns:
- `cs_ear` (registered in `CUE_EXTRACTORS`, added to `REPERTOIRE_CUES`) — the CS
  contrast cochleagram read out through the SAME A1 patch bank as the gammatone ear,
  so it drops into the recognizer with the identical descriptor shape.
- `cs_track` — the CS contrast cochleagram as an ordered per-frame trajectory (the
  analogue of `cmvn_track`) for the agent's graph-resident DTW recognizer.

## Test (robust SC 40-speaker LOSO, ungameable)

`scripts/center_surround_loso.py`. Real Google Speech Commands digits, 120 train /
40 held-out speakers (disjoint; held-out clips NEVER banked), 20 clips per word.
Split: **200 bank, 200 seen-speaker probes, 400 cross-speaker LOSO probes**. Chance
0.100. Two recognizers, both the experiment's own:
- **BANK** — the agent's 1-NN cosine bank recognizer (`channel_likelihood`) over a
  SINGLE front-end ear through the same A1 patch bank. RAW = the seed gammatone_flat
  readout (absolute cochleagram, per-band mean removed); CS = the cs_ear contrast. The
  ONLY difference is the contrast transform — apples to apples.
- **DTW** — the agent's graph-resident Argmin-MinOver-DtwTo Term over the ordered
  per-frame trajectory. RAW = raw cochleagram track; CS = the cs_track contrast track.

Ablation: frequency-only surround at widths sigma_f_s ∈ {3, 4, 6}, plus one
spectro-temporal variant (sigma_f_s=4, sigma_t_s=2). A small FIXED reported set — not
a sweep-and-keep-best.

## Results (captured `/tmp/cs_loso_full.out`, marker `CENTER_SURROUND_LOSO_COMPLETE`)

```
[BANK 1-NN recognizer — single front-end ear, same A1 patch readout]
  RAW cochleagram          seen 0.350  LOSO 0.325  gap +0.025
  CS freq-only sf=4        seen 0.360  LOSO 0.315  gap +0.045
  CS freq-only sf=6        seen 0.335  LOSO 0.318  gap +0.018
  CS freq-only sf=3        seen 0.355  LOSO 0.295  gap +0.060
  CS spectro-temp 4/2      seen 0.395  LOSO 0.345  gap +0.050

[DTW-trajectory recognizer — agent's graph-resident Argmin MinOver DtwTo]
  RAW cochleagram track    seen 0.305  LOSO 0.305  gap +0.000
  CS freq-only sf=4 track  seen 0.350  LOSO 0.292  gap +0.057
  CS spectro-temp 4/2 track seen 0.345  LOSO 0.345  gap +0.000

chance 0.100
BANK  RAW: seen 0.350  LOSO 0.325  gap +0.025
BANK  best CS (spectro-temp 4/2): seen 0.395  LOSO 0.345  gap +0.050  | LOSO lift +0.020
DTW   RAW: seen 0.305  LOSO 0.305  gap +0.000
DTW   best CS (spectro-temp 4/2): seen 0.345  LOSO 0.345  gap +0.000  | LOSO lift +0.040
```

## Verdict

**WEAK / PARTIAL, not a wall-break. The frequency-only contrast does NOT help; the
SPECTRO-TEMPORAL surround gives a small lift, biggest on the DTW recognizer.**

1. **Cross-speaker LOSO lift.** Best CS = the **spectro-temporal** surround
   (sigma_f_s=4, sigma_t_s=2). BANK +0.020 (0.325 -> 0.345), DTW **+0.040**
   (0.305 -> 0.345). Both small and inside the ~±0.02-0.04 LOSO noise band of this
   split (the 12/4-speaker smoke run gave a *negative* bank lift -0.051 and a +0.026
   DTW lift — the sign of the bank effect is not stable across splits). Real but not
   decisive; this is not the binary admissibility jump that a missing structure would
   produce — LOSO stays ~0.31-0.35, far from solved.

2. **Frequency-only contrast does not help.** Every frequency-only CS variant (sf=3/4/6)
   is at or BELOW raw LOSO (0.295-0.318 vs raw 0.325) on the bank. The per-frame
   spectral-edge contrast alone is NOT more speaker-invariant. The small benefit needs
   the TEMPORAL surround (normalising onsets/offsets across time), not the spectral one.

3. **The gap does NOT tighten — it WIDENS.** Under the best (spectro-temporal) CS the
   seen-vs-cross gap goes from +0.025 to +0.050 on the bank (seen rises 0.350 -> 0.395
   while LOSO rises only 0.325 -> 0.345). The contrast adds *seen-speaker discriminative
   detail* faster than it adds cross-speaker invariance — the opposite of the "more
   invariant" prediction. The salience/contrast is informative but it is NOT cancelling
   the speaker-specific term; it is sharpening the representation for everyone.

4. **KILL on the strong hypothesis.** Center-surround is NOT the missing cross-speaker
   invariance. The local contrast does not cancel the speaker term (the gap widens), and
   the frequency-only contrast — the part that should normalise the spectral tilt/VTL
   envelope — does nothing. The honest read: CS is a mild, mostly seen-speaker-side
   *feature enrichment* (best via the temporal axis), not an invariance lever.

**Residual.** Cross-speaker LOSO best 0.345 (chance 0.100); ~0.655 from solved. The
feature/cross-speaker reliability wall holds. The +0.040 DTW lift from the
spectro-temporal contrast is worth keeping as a cheap orthogonal feature (it is owned,
composable, effect-gated), but it does not move the wall and it does not tighten the
seen-vs-cross gap. The missing invariance is deeper than a local-contrast salience map.

Required suites green: `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance`, `test_frontend_effect_gate`
(36 passed). Not committed.
