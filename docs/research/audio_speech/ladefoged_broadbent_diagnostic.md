# Ladefoged–Broadbent (1957) diagnostic — does the model perceive vowels RELATIVE to a carrier-talker?

**Script:** `scripts/ladefoged_broadbent_diagnostic.py`
**Log (with end marker):** `/tmp/lb_diag.log` → `LB_DIAGNOSTIC_COMPLETED`, `EXIT=0`

## The question

Ladefoged & Broadbent (1957) / Chodroff & Stilp (2022) replication: a human listener
perceives an *ambiguous* test vowel **relative** to the formant range of a preceding
carrier phrase (the "sliding template" / extrinsic normalization). A carrier whose
formants are shifted **up** (small vocal tract) makes a fixed test sound like a
**lower** vowel, and vice versa — vowel identity depends on the *relationship* between
the test's formants and the carrier-talker's range, not on absolute Hz.

This diagnoses whether our model has the **relative / speaker-normalised** perception
that the session's cross-speaker KILLs suggested we are missing.

## Build (donkey-clean)

- **Stimuli = the world/synth.** espeak-ng voicebox; a VTL formant warp (`vtl_warp`)
  scales all formants by α via an STFT frequency-axis warp (f → α·f), holding duration
  fixed. (An earlier resample-then-resample-back warp was a **no-op** on the spectrum;
  caught by the formant audit and replaced — see note below.)
- **Perception = the model, unchanged.** The model's three seed front-end channels
  (gammatone-flat + FFT-ear + all-pole-ear) and its per-utterance-CMVN residual
  trajectory (`learned_voice_shape.residual_track(.,.,[])`). The category readout is the
  model's own 1-NN cognition+hat: `score = d(test, bid) − d(test, bed)` over two banked
  endpoint exemplars (the model's nearest-exemplar Argmin on a 2-word lexicon).
- **The carrier+test is one clip.** Per-utterance CMVN (subtract the mean over the whole
  clip) is the model's **only** candidate extrinsic-context mechanism — a prepended
  carrier enters that mean. We read the category of the **test portion** of the clip.

## Donkey audit — the stimuli are real

| | F1 (Hz) | F2 (Hz) |
|---|---|---|
| endpoint `bid` | 390 | 1730 |
| endpoint `bed` | 628 | 1698 |
| **carrier-UP** (α=1.18) | 476 | **1569** |
| **carrier-DOWN** (α=0.85) | 380 | **1188** |
| fixed test (α=1.125) | 445 | 1936 |

The carrier's formant range genuinely shifts between conditions — UP vs DOWN differ by
~96 Hz in F1 and **~381 Hz (≈24%) in F2**. The fixed test bytes are identical in every
condition.

## Result — perceived category of the FIXED test vs carrier

`score = d(test,bid) − d(test,bed)`  (>0 → bed; <0 → bid)

| condition | score | perceived |
|---|---|---|
| (1) TEST ALONE | +0.0277 | bed |
| (2) CARRIER-UP + TEST | +0.0671 | bed |
| (3) CARRIER-DOWN + TEST | +0.0690 | bed |

**Carrier effect (score_up − score_down) = −0.0019** = **−0.6%** of the endpoint score
separation (0.3209). **No category flip.**

The shift from test-alone to carrier-present (+0.039) is **identical for UP and DOWN**
(d_up=+0.039, d_down=+0.041): the per-utterance CMVN reacts to *having any carrier at
all* (the mean is biased by extra frames), but is **completely blind to the carrier's
formant range** — which is exactly the Ladefoged–Broadbent variable. The model does not
slide its template with the talker.

## Verdict

**The model perceives the test ABSOLUTELY — by its own formants, regardless of the
carrier's formant range. The relative / speaker-normalised ("sliding template")
perception is MISSING.** The prediction is confirmed (the embarrassing-in-hindsight
one). This is the cross-speaker mechanism the session's cross-speaker KILLs were
probing: there is no extrinsic-normalization machinery that re-references a test against
an established talker range.

## Optional — minimal sliding-template fix

Re-expressing the test relative to the carrier's geometric-mean formant (warp the test
by `neutral_ref / carrier_ref`) did **not** produce the LB shift either (effect +0.0006,
no flip). Honest read: a single-scalar formant-ratio renormalization against a *crude*
LPC carrier reference is too coarse to move this exemplar/DTW category boundary at this
resolution — the fix is not as trivial as one rescale. The diagnostic (the absent
mechanism), not the fix, is the deliverable; a real sliding template would need the
carrier range as a perceptual frame the recognizer reads, not a one-shot waveform warp.

## Note on the caught measurement bug

The first run reported carrier-UP and carrier-DOWN with **identical** formants (F2~1396
both) — the VTL warp was a no-op (resample then resample back restores the original
spectrum). Caught by the donkey formant audit, the warp was replaced with a true STFT
frequency-axis warp and the run repeated. The verdict is unchanged across both the
broken and fixed warp (no carrier effect either way), but only the fixed-warp run is a
valid LB test, because only it actually shifts the carrier's formant range.
