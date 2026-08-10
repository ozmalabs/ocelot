# Iteration 38 — add the phoneme-class LANDMARK node (the transient phonetic-event axis)

> The fourth and last of the four acoustic axes. The agent's cues read the vocal-tract
> FILTER (gammatone/FFT/LPC/manner — spectral envelope + derivatives); iter-37 added the
> SOURCE (F0) and TEMPORAL-RATE (modspec) axes. The one remaining axis is the TRANSIENT
> PHONETIC EVENT — the stop burst, the VOT interval, the fricative noise, the nasal
> murmur — the cue that separates the within-manner confusions (b/d/g, p/t/k, s/f) that
> survive every speaker-invariant FILTER cue (docs/research_dismissed_ideas_as_specialists.md §4).
>
> THE TEST (iter-37's diagnosis): F0 was orthogonal-but-NOISY — highest error-overlap, but
> its rescues were offset by mis-points on bottom-up-correct queries, netting ~0. The
> landmark fires on a DEFINITE acoustic event, so it should be SHARP and RELIABLE
> (rescues > mis-points) — the test of whether reliability was the missing ingredient.
>
> NO commit. Results + this doc left in the working tree. Written INCREMENTALLY; runs
> captured to /tmp FILES; PYTHONUNBUFFERED=1.

## NO-DONKEY — "the detector is the donkey, the cue is the harvest"

The published landmark/VOT detectors are TRAINED (SVM/RNN) — they are NOT ported. The
landmark CUE is RE-DERIVED as composable DSP from the agent's OWNED operators, ZERO-FIT:

- **burst** = onset spike — order-1-over-time positive jump in HIGH-band energy
  (`np.diff` over the cochleagram high-band partition `_HIGH`).
- **VOT** = lag from the burst onset to the VOICING onset — the periodicity the manner
  channel already computes (`stacked_representation._frame_periodicity`, autocorrelation).
- **fricative** = sustained HIGH-frequency APERIODIC energy = high-band energy × (1 −
  periodicity) — the time-resolved sibilant-band cue.
- **nasal** = low-frequency murmur × spectral-FLATNESS = low-band energy × the LPC
  residual ratio (the Levinson gain `e / r[0]` from the agent's OWN `_autocorr` +
  `_levinson`; a flat anti-formant region leaves large residual = high flatness).

Assembled per-segment into a fixed-length landmark SIGNATURE: 24-frame resampled contour
of `[burst, voicing, fricative, nasal_flatness, hi, lo]` (6 channels) ++ 3 per-utterance
timing scalars `[burst_time, voicing_onset_time, burst-to-voicing LAG (=VOT)]` = a 147-d
L2-normalised vector. Same node shape as `fft_ear`: the SAME cosine 1-NN exemplar
evidence → softmax by its OWN median candidate distance → ONE more `Times` factor in the
variadic Argmax-of-product. NO select, NO weight, NO fit, NO tuning.

### Audit (combine-all, not select)

`predict_many_settings_term(27)` for the full graph (20 gammatone + 6 ortho + 1 AxS) is
`Argmax(NodesWhere) of Times[p_ch0..p_ch26]` — node types
`{Argmax, Attr, Lit, NodesWhere, Times, Var}`, EXACTLY 27 Times factors, NO
`Max/Sort/Pick/If/Div/Weight/Mul` anywhere (verified programmatically by
`iter36_continuous_graph.audit_combine_all_term`). The landmark node enters the product
symmetrically as the 27th factor.

## Build status

- (1) LANDMARK node WIRED — composable DSP from owned operators (onset/diff, voicing
  periodicity, sibilant high-band, LPC residual flatness), zero-fit, combine-all,
  audited. ✓ `scripts/enriched_hvpt_accept.landmark_readout` (+ `_lpc_residual_flatness`),
  added to `ORTHO_NAMES` and `build_fold`; `score_fold` reconstructs the `iter36`
  (no f0/modspec/landmark) AND `iter37` (no landmark) baselines in the same fold, so
  `graph+landmark − iter37` is the clean landmark delta.
- COMBINE-ALL AUDIT (n=27): PASS — Argmax-of-Times, 27 factors, no forbidden ops. ✓
- Required suites green (32): `test_stt_pipeline`, `test_perception_self_assessment`,
  `test_process_meta_assessor`, `test_gap_guidance`. ✓
- Smoke: landmark → 147-d unit vector; graceful on tiny/short input; flatness separates
  a noise burst (0.98) from a periodic tone (0.01) as designed. ✓

## Run (live — captured to /tmp, incremental)

```
# CONTINUOUS (gold-span LibriSpeech, 8 held-out speakers, ~12-word vocab, chance ~0.083)
PYTHONUNBUFFERED=1 python -m scripts.iter36_continuous_graph 8 40 8 12 > /tmp/iter38_continuous_n8.txt
# DIGIT-ISOLATED (FSDD, LOSO over 6 speakers, 10 digits, chance 0.100)
PYTHONUNBUFFERED=1 python -m scripts.enriched_hvpt_accept 8 2          > /tmp/iter38_digit_n8.txt
```

Both report GRAPH+landmark vs iter-37 (F0+modspec) vs iter-36 vs iter-34/33 vs
single-flat, with shuffle, the landmark drop-it, the saturation-free error-overlap, AND
(continuous) the WITHIN-MANNER confusion breakout (b/d/g, p/t/k, s/f).

## Results

Setup reproduces iter-36/37 byte-for-byte: same 12-word function vocab
(`and but for had have his not out that the was with`), 501 clips, 8 held-out speakers,
chance 0.083; cross-speaker DTW-NN consistency reproduces exactly (0.165, shuffle 0.100,
margin +0.065). COMBINE-ALL AUDIT (n=27): PASS.

### CONTINUOUS (gold-span LibriSpeech, LOSO over 8 speakers, chance 0.083)

| metric (mean over 8 LOSO folds) | value |
|---|---|
| **GRAPH + landmark (+F0 +modspec +AxS)** | **0.239** |
| **iter37 (F0+modspec, no landmark)** | **0.236** |
| iter36 (3-ortho + AxS, no new) | 0.234 |
| iter34 (no AxS) | 0.237 |
| iter33 (gammatone only) | 0.222 |
| single-flat | 0.183 |

- **GRAPH+landmark vs iter37: Δ +0.002 → does NOT meaningfully widen.** Per-fold landmark
  drop-it (+0.000, +0.043, +0.000, −0.033, −0.019, +0.015, +0.000, +0.014) is symmetric
  around zero = noise.
- **SHUFFLE clean:** GRAPH+landmark real 0.239 vs shuffle 0.214, margin +0.025 (CLEAN);
  iter37 +0.020; single-flat −0.002.
- **ERROR-OVERLAP (decisive, saturation-free)** — on the 389 held queries where the
  bottom-up is WRONG, what each cue ALONE catches (chance 0.083):

  | cue alone | catches | rate | vs chance |
  |---|---|---|---|
  | manner_voicing | 68/389 | 0.175 | 2.1× |
  | AxS | 59/389 | 0.152 | 1.8× |
  | f0_contour | 56/389 | 0.144 | 1.7× |
  | fft_ear | 52/389 | 0.134 | 1.6× |
  | **landmark** | **51/389** | **0.131** | **1.6×** |
  | formant_relation | 47/389 | 0.121 | 1.5× |
  | modspec | 44/389 | 0.113 | 1.4× |

  The landmark IS orthogonal in information (1.6× chance), but it sits in the MIDDLE of the
  pack — BELOW f0_contour (1.7×) and well below manner_voicing (2.1×). Same
  orthogonal-but-noisy pattern as F0: rescues on bottom-up-wrong queries offset by
  mis-points on bottom-up-correct queries, netting ~0 in the product.

### WITHIN-MANNER CONFUSION ANALYSIS (the landmark's SPECIFIC target)

Only **10 within-manner confusions (b/d/g, p/t/k, s/f) occurred across all 8 folds** — the
function-word vocab has almost no such minimal pairs, so the landmark's target population is
nearly ABSENT in this venue. On that tiny slice (chance 0.083):

| cue | catches within-manner |
|---|---|
| manner_voicing | 3/10 (0.300) |
| f0_contour | 2/10 (0.200) |
| fft_ear / formant_relation / modspec / AxS | 1/10 (0.100) |
| **landmark** | **0/10 (0.000)** |

The landmark caught the FEWEST of its own named target. On n=10 this is not interpretable
(one clip = 0.1), but the claim "the landmark resolves the within-manner confusions the
filter cues can't" is NOT supported here — and the venue cannot test it (population absent).

### DIGIT-ISOLATED (FSDD, LOSO over 6 speakers, chance 0.100)

| metric (mean over 6 FSDD LOSO speakers, n=8) | value |
|---|---|
| **GRAPH + landmark + AxS** | **0.592** |
| iter34 (no AxS) | 0.585 |
| iter33 (gammatone only) | 0.567 |
| single-flat | 0.496 |

- **GRAPH+landmark vs iter37 (= the landmark drop-it): Δ +0.004 → does NOT widen.** Per-fold
  landmark drop-it (+0.000, −0.012, −0.012, +0.013, +0.012, +0.025) is symmetric around
  zero = noise, exactly like F0/modspec on digits. (Aggregate over folds, the printed
  landmark drop-it mean is +0.004.)
- landmark ALONE on digits ~0.215 mean, below formant_relation (0.421) / fft_ear (0.400) /
  modspec (0.315). The PERSONA fold's landmark-alone 1.000 is a saturation artifact of the
  synthetic identical-source stimulus (all cues saturate there), not real signal.
- SHUFFLE clean (graph+landmark+AxS real 0.592 vs shuffle 0.554, margin +0.037).

## VERDICT

**(1) Landmark cue wired (composable DSP from owned operators — the cue NOT the detector;
zero-fit, combine-all, audited).** ✓ burst = order-1-over-time positive jump in high
cochleagram bands; VOT = burst-to-voicing lag (the periodicity `_frame_periodicity`
computes); fricative = high-band × (1−periodicity); nasal = low-band × LPC-residual
flatness (the Levinson gain `e/r[0]` from the agent's own `_autocorr`+`_levinson`). 147-d
L2 vector → cosine 1-NN → softmax by own median → one more Times factor. AUDIT (n=27):
Argmax-of-Times, exactly 27 factors, no Max/Sort/Pick/If/Div/weight. NO trained detector,
NO weight, NO fit.

**(2) Multi-metric on BOTH venues** with shuffle, the landmark drop-it, the saturation-free
error-overlap, AND the within-manner breakout. ✓

**(3) Does the SHARP RELIABLE landmark WIDEN where the diffuse noisy F0 didn't? NO.**
The landmark is **orthogonal-but-NOISY, exactly like F0** — and on this venue WEAKER, not
sharper:
- CONTINUOUS Δ vs iter-37 = +0.002 (within-noise; drop-it symmetric around zero).
- DIGIT Δ vs iter-37 = +0.004 (within-noise; drop-it symmetric around zero).
- ERROR-OVERLAP: landmark = 1.6× chance — real orthogonal information, but BELOW f0_contour
  (1.7×) and far below manner_voicing (2.1×). The "reliability was the missing ingredient"
  hypothesis is NOT supported: the landmark's rescues are offset by mis-points just as F0's
  were, netting ~0 in the product.
- WITHIN-MANNER (its named target): population nearly absent (10 confusions / 8 folds); on
  that tiny slice the landmark caught 0/10 (the fewest) — claim not confirmed, venue can't
  test it.

**Which branch of the spec this lands on:** the **orthogonal-but-noisy** branch (NOT a real
lift, NOT redundant). **The noise problem is GENERAL, not F0-specific** — a SHARP-event cue
does not automatically convert. The landmark CUE re-derived as a raw 1-NN exemplar node is
itself noisy: a coarse 24-frame contour over a coarse 8 kHz / ~25 ms-frame cochleagram, so
the burst/VOT geometry is blurry at this time-frequency resolution. "Sharp event" did not
translate to "reliable node."

**The four-axis direct-route map is now COMPLETE:**

| axis | iter | error-overlap | combined lift | status |
|---|---|---|---|---|
| FILTER (gammatone/FFT/LPC/manner) | 34 | — (the base) | YES (the only lift) | reliable |
| SOURCE (F0) | 37 | 1.7× | no | orthogonal-but-noisy |
| TEMPORAL-RATE (modspec) | 37 | 1.4× | no | weakly orthogonal |
| TRANSIENT (landmark) | 38 | 1.6× | no | orthogonal-but-noisy |

Three of the four orthogonal axes are orthogonal-in-information yet sub-threshold as raw
1-NN nodes in the saturating product. **General finding: a cue must be orthogonal AND
reliable to widen; the direct zero-fit route delivers orthogonality but not reliability for
the source/rate/transient axes.** Per the spec's own contingency, this is where the SMALL
SPECIFIC NETS become necessary — a gap-filler that extracts the landmark's (and F0's) signal
more reliably than a raw 1-NN node. The direct routes are now exhausted.

### Honest limits
- Absolute continuous accuracy is low (≈0.24, chance 0.083) on a 12-word function-word
  vocab; deltas (±0.002–0.005) are a few clips per fold.
- The within-manner target population is nearly absent in the function-word venue (10
  confusions / 8 folds) — the landmark's specific claim is effectively UNTESTED here. A
  venue with stop/fricative minimal pairs (FSDD digits have few; a CVC or TIMIT-consonant
  venue would have many) is needed to test it properly. This is the single biggest caveat:
  we did NOT give the landmark its target population.
- The 20-gammatone product saturates, so an orthogonal-in-information node can fail to widen
  the combined number — error-overlap is the cleaner signal than drop-it.
- No fit, no select, no weight anywhere; combine-all throughout; the landmark node is pure
  I/O-boundary DSP (world adapter), the graph product is unchanged.

## Reproduce
```
python -m scripts.iter36_continuous_graph 8 40 8 12   # CONTINUOUS (/tmp/iter38_continuous_n8.txt)
python -m scripts.enriched_hvpt_accept   8 2          # DIGIT      (/tmp/iter38_digit_n8.txt)
```
Wiring: `scripts/enriched_hvpt_accept.py` — `landmark_readout` (+ `_lpc_residual_flatness`)
added to `ORTHO_NAMES` and `build_fold`; `score_fold` reconstructs the iter36 (no
f0/modspec/landmark) and iter37 (no landmark) baselines in the same fold.
`scripts/iter36_continuous_graph.py` — `audit_combine_all_term` + the within-manner
breakout in `error_overlap` + the within-manner aggregation in `main`. Required suites green
(32): test_stt_pipeline, test_perception_self_assessment, test_process_meta_assessor,
test_gap_guidance.
