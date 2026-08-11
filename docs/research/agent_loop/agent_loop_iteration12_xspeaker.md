# Autopoietic loop — iteration 12 (close the CROSS-SPEAKER invariance gap)

iter-11 retired the descriptor as the lever and located the binding blocker
precisely: on REAL FSDD, full-resolution DTW word-matching is high WITHIN-speaker
but low CROSS-speaker — the same word from different speakers does not match. The
current `invariant_transform` (forward-VTLN + CMVN + predict-remove, all estimated
PER UTTERANCE) got the units past the predictiveness yardstick but left this
cross-speaker word-matching gap. This iteration forward-builds a DEEPER speaker
normalization from the agent's own science and tests it on the FAST within/cross
full-DTW probe, running full recognition only because the cross gap closed.

## Honest headline

**The cross-speaker invariance gap CLOSED, shuffle-controlled, and the last link
became admissible.** The lever is PER-SPEAKER (not per-utterance) CMVN —
estimating the speaker's spectral envelope from the test speaker's OWN audio at
test time and subtracting it. On real FSDD, full-resolution DTW cross-speaker
word-matching went from `current 0.59` to `deeper 0.80` (within 0.94), the gap
collapsing from ~0.29 to ~0.14, reproducible across seeds and corpus sizes, with
the shuffle control flat at chance. The cross gap cleared the >0.6 gate, so
LOSO recognition on held-out SPEAKERS ran: word-accuracy went from `current
0.571` to `deeper 0.785` (unigram 0.100), the deeper normalization beating the
current one on 5 of 6 held-out speakers. The structure switched on for real
speech. I did NOT tune — no component was swept-and-kept; the winning method is
the one the science predicts, and the loser (per-speaker VTLN) is reported.

## (1) The deeper speaker-normalization — which lever, and why (from the science)

Forward-built in `domains/xspeaker_norm.py`. The diagnosis of WHERE the residual
cross-speaker variance lives, reasoned from the agent's own speaker science:

- **Per-utterance VTLN is noisy.** The warp factor α is estimated from a SINGLE
  ~0.5s digit's spectral centre-of-mass. That conflates the speaker's
  vocal-tract length with the WORD's spectral content (a "two" and a "six" from
  the same speaker have different centroids), so per-utterance α leaves a
  speaker-correlated residual AND injects word-correlated error. A speaker's
  true vocal-tract length is constant across their utterances → estimate it ONCE
  per speaker, pooled over the speaker's own audio.
- **Per-utterance CMVN under-removes the speaker envelope.** CMVN subtracts each
  utterance's OWN mean, but the speaker's long-term spectral envelope (glottal
  source shape, spectral tilt, formant bandwidths, channel) is the part that is
  CONSTANT across the speaker's utterances and DIFFERENT between speakers. A
  single short digit's mean is a poor, content-contaminated estimate of it. The
  speaker ENVELOPE = the mean log-spectrum over the speaker's OWN audio.
  Subtracting it removes the full speaker term, not one utterance's slice. This
  is the agent's own `speaker_norm` move ("subtract the mean cancels the constant
  speaker shift") generalised from per-utterance to **PER-SPEAKER**, and from a
  scalar VTL log-shift to the whole **ENVELOPE SHAPE** — exactly the residual the
  VTL log-shift does not reach (the task's "envelope-shape normalization beyond
  the VTL log-shift" and "a speaker embedding removed" levers, unified: the
  per-speaker per-band mean IS the speaker embedding).

The per-speaker statistics (one log-centroid for VTLN, one per-band mean/std for
CMVN) are estimated AT TEST TIME from the test speaker's own UNLABELLED audio —
the "per-speaker normalization at test time" lever, with no labels, no search, no
tuning: the statistic IS the speaker mean. The per-band mean subtraction and the
variance division are the SAME operations the agent already composed
graph-resident in `domains/cmvn` (per-band `(x - mean)/std`) and
`domains/speaker_norm`; the only change is the pooling set — the SPEAKER's frames,
not one utterance's. The I/O boundary is the pool-and-average over the test
speaker's frames.

## (2) WITHIN / CROSS full-DTW word-matching — before → after, per-method ablation

FAST probe (`scripts/iter12_xspeaker.py`): per-voiced-frame log-mel band matrix
(`cross_speaker_clustering_probe.logmel_frames`), full-resolution banded DTW
(`continuous_speech_recognition.dtw`) over the NORMALIZED frames — the richest
trajectory metric, zero resampling loss. For each utterance, its nearest WITHIN-
and nearest CROSS-speaker neighbour by DTW; does the neighbour carry the same
word? Real FSDD, all 6 speakers, 10 digits, chance 0.100.

```
n_per_speaker = 8 (480 utts):
method                          WITHIN     CROSS     gap
raw                              0.935     0.571   0.364
current(VTLN+CMVN+PR)            0.875     0.588   0.287
ps_VTLN+uCMVN+PR                 0.762     0.521   0.242   (per-utt at n=4; VTLN-only hurts)
uVTLN+ps_CMVN+PR                 0.938     0.802   0.136   <-- the lever
ps_VTLN+ps_CMVN+PR               0.858     0.696   0.162   (adding ps-VTLN HURTS)
ps_CMVN_only+PR                  0.938     0.802   0.136   (== uVTLN+ps_CMVN: VTLN is subsumed)
```

**Per-speaker CMVN closes the cross gap; per-speaker VTLN does NOT (and hurts when
stacked).** `ps_CMVN_only+PR` (no VTLN at all) equals `uVTLN+ps_CMVN+PR` exactly —
the per-speaker envelope subtraction SUBSUMES the VTL log-shift, because the
envelope mean already contains it. Adding per-speaker VTLN on top
(`ps_VTLN+ps_CMVN`) over-warps and drops cross to 0.696. So the lever is precisely
the per-speaker speaker-embedding removal, not the per-speaker warp.

Reproducible across seeds (n=4, `current cross -> ps_CMVN cross (within); shuffle`):

```
seed 1: 0.512 -> 0.700 (0.850); shuffle cross 0.079
seed 2: 0.517 -> 0.717 (0.900); shuffle cross 0.075
seed 3: 0.579 -> 0.754 (0.887); shuffle cross 0.104
```

**SHUFFLE control** (word labels shuffled, on the best method): within 0.05–0.07,
cross 0.06–0.10 — flat at chance (0.100) every seed. The matching is REAL, not an
artifact. (Note: this log-mel matrix path reads the within/cross baseline as
~0.88/0.59, somewhat higher than iter-11's stated 0.78/0.35; the venue/front-end
differs slightly — log-mel-FFT frames here vs iter-11's path — but the GAP
structure and the lever are identical. The within/cross GAP, not the absolute, is
the quantity that closes.)

## (3) Recognition on held-out SPEAKERS (LOSO) — cross closed, so it ran

The cross gap cleared the >0.6 gate (0.80), so LOSO kNN-DTW recognition ran:
train on 5 speakers (words known), classify the held-out 6th speaker's utterances
by majority of the 3 nearest train utterances under full-resolution DTW on the
NORMALIZED matrices; compare to the unigram (most-frequent-train-word) baseline.

```
n_per_speaker = 8, held-out-speaker word-accuracy (chance 0.100, unigram 0.100):
  current(VTLN+CMVN+PR): 0.571
  deeper (ps_CMVN+PR)  : 0.785      (+0.214 over current)

per held-out speaker (n=4 run, current -> deeper):
  george   0.350 -> 0.725     lucas    0.550 -> 0.825
  jackson  0.400 -> 0.550     nicolas  0.650 -> 0.825
  theo     0.825 -> 0.800     yweweler 0.425 -> 0.750
```

The deeper normalization beats current on **5 of 6** held-out speakers (theo, the
already-easy one, ties within noise), and lifts the two worst (george, yweweler)
the most. Both crush the unigram baseline — expected for kNN-DTW — so the
load-bearing comparison is current-vs-deeper on held-out speakers, where the
per-speaker speaker-embedding removal adds +0.21 absolute.

## (4) Configuration verdict

- **Did cross-speaker invariance close?** YES. Cross-speaker full-DTW
  word-matching 0.59 → 0.80 (within 0.94), gap 0.29 → 0.14, reproducible across
  seeds and corpus sizes, shuffle-controlled at chance.
- **Did the last link become admissible?** YES. The recognition structure
  completes on held-out speakers: word-accuracy 0.571 → 0.785, the deeper
  normalization beating current on 5/6 speakers. The structure switched on for
  REAL speech.
- **The lever is precisely located:** PER-SPEAKER CMVN (speaker-embedding
  removal), estimated from the test speaker's own audio. Per-speaker VTLN is NOT
  the lever (it is subsumed by, and hurts when stacked on, the per-speaker
  envelope mean). This is the agent's `speaker_norm` "subtract the mean cancels
  the shift" science generalised from per-utterance to per-speaker and from a
  scalar shift to the whole envelope shape.
- **Residual.** Within-speaker is 0.94, cross is 0.80 — a ~0.14 gap remains. The
  residual is the speaker variation NOT captured by a first/second-moment
  (mean/std) per-band statistic: per-band higher-order envelope shape and
  phone-specific formant-bandwidth differences a global per-speaker affine cannot
  reach. jackson (cross-recognition 0.55, the weakest) marks where the affine
  speaker model is least sufficient. The next lever, if pushed, is a per-speaker
  transform with more than two moments (or a phone-conditioned one) — but the
  binding cross-speaker link is now closed.

## Controls / honesty

- **Did I tune to a number?** No. No component swept-and-kept. The four
  per-speaker variants were composed from the science and ablated; the winner
  (`ps_CMVN+PR`) is the one the diagnosis predicts, and the LOSER (per-speaker
  VTLN: hurts, subsumed) is reported, not hidden. k=3 / variance-on are the
  defaults inherited from the existing CMVN, not searched here.
- **Shuffle holds.** Word-label shuffle collapses both within and cross matching
  to chance on every seed — the gain is structure, not artifact.
- **Reproducible.** 3 seeds at n=4, plus n=8. The lever strengthens with more
  data (cross 0.70 at n=4 → 0.80 at n=8), the sign of a real invariance, not a
  small-sample fluke.
- **The gate was respected.** Cross closed (0.80 > 0.6) → recognition ran (per the
  task's instruction); recognition compared deeper-vs-current AND vs unigram.

## Status / acceptance

- **(1) deeper normalization:** built — per-speaker CMVN (speaker-embedding
  removal) in `domains/xspeaker_norm.py`, the lever; per-speaker VTLN built and
  ablated (not the lever). From the agent's `speaker_norm` / `cmvn` science.
- **(2) within/cross before→after + ablation:** current cross 0.59 → deeper 0.80
  (within 0.94), gap 0.29 → 0.14; per-method ablation isolates per-speaker CMVN as
  the lever and per-speaker VTLN as a non-lever; shuffle-controlled at chance;
  reproducible across seeds and corpus sizes. Real numbers above.
- **(3) recognition:** RAN (cross closed). LOSO held-out-speaker word-accuracy
  current 0.571 → deeper 0.785 (unigram 0.100), deeper > current on 5/6 speakers.
- **(4) verdict:** cross-speaker invariance CLOSED; the last link became
  admissible; the structure switched on for real speech. Residual ~0.14 gap =
  the speaker variation beyond a per-band affine.
- `test_stt_pipeline` + `test_perception_self_assessment` +
  `test_process_meta_assessor` + `test_gap_guidance`: **32 passed.**
- Not committed; left in the working tree + this doc.

### Reproduce

```
# fast within/cross full-DTW probe + per-method ablation + shuffle + LOSO recog
python -m scripts.iter12_xspeaker 8        # n_per_speaker (4 is faster)

# reproducibility across seeds
python -c "import scripts.iter12_xspeaker as P; \
  [print(s, P.run(4, seed=s, verbose=False)['ps_CMVN_only+PR']) for s in (1,2,3)]"

python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q   # 32 passed
```
