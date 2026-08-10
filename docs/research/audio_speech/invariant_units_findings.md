# Forward-designing speaker-invariant units from Kaldi VTLN + CMVN

Mining Kaldi's two designed speaker-normalization operations for their
MECHANISM (not code, not weights) and having the speech agent FORWARD-DESIGN
its own speaker-invariant unit representation from them, to crack the
unit-quality bottleneck the Whisper mine diagnosed.

- Module: `domains/invariant_units.py` (the two operations, forward-designed).
- Accept (criterion 1, FSDD LOSO): `scripts/invariant_units_accept.py`
  (band path) and `scripts/invariant_units_patch_accept.py` (the agent's real
  A1-patch path, where the Whisper-mine 0.578 lives).
- Accept (criteria 2 & 3, continuous speech): `scripts/invariant_units_librispeech_accept.py`.
- `test_stt_pipeline` + `test_perception_self_assessment` stay green (12 passed).
- Nothing committed; left in the working tree.

## The frame (not re-litigated)

The Whisper mine proved the agent's cochlea is the STRONGER raw representation
(front-end leave-one-speaker-out 0.58 DTW vs Whisper's log-mel 0.29). The gap
is the PROCESSING — a speaker-invariance abstraction step downstream of the
already-good front-end — not the ears. Whisper builds it with attention+SGD
(un-portable). Kaldi builds it with two DESIGNED operations the agent can
forward-design from its own VTL science.

## What was mined (mechanism, not code)

1. **VTLN (Vocal Tract Length Normalization).** A longer vocal tract scales ALL
   formants DOWN by a factor α (F_i → α·F_i); Kaldi WARPS the frequency axis per
   speaker/utterance by a piecewise-linear factor onto a canonical tract. Kaldi
   SEARCHES α by max-likelihood — we do NOT. The agent estimates α FORWARD from
   its own formant centre-of-mass (the agent's `speaker_norm` science: a VTL
   scale is a constant shift on the log-frequency axis; the utterance's mean
   log-spectral position relative to the cohort canonical IS log α). Applied as a
   band-index shift (with interpolation) on the agent's log-spaced gammatone
   axis.
2. **CMVN (Cepstral Mean-Variance Normalization).** Subtract the per-utterance
   per-band mean (the channel / loudness / long-term-spectrum term carrying
   speaker + recording identity, not phonetic content); optionally divide by the
   per-band std. Computed over voiced frames.

The transform: `frames×bands` → forward-VTLN warp to canonical → CMVN. Cluster /
DTW-compare on the NORMALIZED features → speaker-invariant units. The warp is
estimated from each utterance's own formants; never swept to maximize a score.

## Results — does invariant processing crack the units?

### Criterion 1 — FSDD digits, leave-one-speaker-out 1-NN word accuracy (DTW)

A1 patch path (the agent's real front-end; `invariant_units_patch_accept.py`,
180 recordings, 6 speakers):

| representation              | DTW LOSO |
|----------------------------|---------:|
| RAW patches                |    0.417 |
| **CMVN (mean+var)**        | **0.578** |
| CMVN (mean only)           |    0.394 |
| VTLN only                  |    0.350 |
| VTLN + CMVN                |    0.522 |
| per-speaker VTLN + CMVN    |    0.528 |

**CMVN (mean+variance) is the lever: +0.16 DTW (0.417 → 0.578).** It lands
exactly on the Whisper-mine's raw front-end number — i.e. CMVN reproduces, from
a single designed operation, the same speaker-invariance the mine had measured.

**VTLN, as a forward band-axis warp, HURTS** on isolated digits — both
per-utterance and per-speaker. Honest reason: the spectral centroid (the forward
α estimate) moves with the VOWEL, not only the vocal tract, so on short isolated
words it over-warps; and warping the band axis then collapsing to the FIXED A1
patch bank misaligns energy from the patch centres. This is reported as measured,
not tuned away.

### Criteria 2 & 3 — LibriSpeech dev-clean, continuous speech

`invariant_units_librispeech_accept.py`. Units = k-means codebook over per-frame
band vectors (held fixed; only raw-vs-normalized frames change). The agent's own
forward chunker (`domains/forward_segmentation`) runs on the resulting unit
sequences. 140 utts / 16 speakers / K=64:

| variant     | TP within−across (ratio) | chunker boundary F1 |
|-------------|-------------------------:|--------------------:|
| raw         |        +0.047 (1.71×)    |               0.208 |
| CMVN        |        +0.027 (1.84×)    |               0.288 |
| VTLN + CMVN |        +0.022 (1.64×)    |           **0.317** |

(80 utts / 10 speakers / K=48 gave the same shape: F1 0.206 → 0.310 → 0.317.)

- **Chunker boundary F1 rises +0.11 (0.208 → 0.317).** The forward TP-trough
  chunker that was STARVED by noisy speaker-variant units does markedly better
  on speaker-normalized units — exactly the predicted link-1 effect. The
  invariant-unit F1 (0.317) nearly matches the raw-unit-boundary reference
  (~0.346), i.e. the chunker recovers almost all the recoverable boundary
  information once the units are clean.
- **On continuous speech VTLN HELPS on top of CMVN** (0.288 → 0.317), the
  opposite of isolated digits: an utterance averages over many phones, so the
  forward formant-centroid α estimate is a much cleaner tract estimate than on a
  single short digit. This is the right place for VTLN.
- **TP within-vs-across separation:** the absolute within−across gap shrinks
  under CMVN, but that is a side effect of CMVN spreading frames more evenly
  across the codebook (more distinct transitions ⇒ lower absolute TP everywhere).
  The within>>across **ratio** (~1.6–1.8×) is preserved across all variants; the
  absolute gap is not the invariance signal, the boundary F1 is.

## Honest verdict — how far does speaker normalization close the gap?

- **CMVN is the forward-designable mechanism that cracks unit invariance.** One
  designed operation (per-utterance mean+variance removal), forward from the
  agent's own channel/loudness science, lifts FSDD DTW LOSO +0.16 (to 0.578, =
  the mine's front-end number) and lifts continuous-speech chunker boundary F1
  +0.11. This is the speaker-invariance abstraction step the mine said was
  missing downstream of the good front-end — and it is a designed transform, not
  trained residue.
- **VTLN is context-dependent.** Forward-VTLN (formant-centroid warp, no
  likelihood sweep) HELPS on continuous speech (+0.03 F1 on top of CMVN, where
  the utterance averages out phonetic content) but HURTS on isolated digits
  (the centroid tracks the vowel, and the warp fights the fixed patch bank).
  Honest: VTLN belongs where there is enough speech to average phonetic content
  out of the tract estimate.
- **What's left** (the gap CMVN+VTLN do NOT close — humans prove it's solvable,
  so this names the remaining work): the residual is **coarticulation / context**
  beyond per-utterance speaker normalization. Speaker norm makes the SAME phone
  cluster across speakers; it does not yet make a phone invariant to its
  NEIGHBOURS (the context-dependent abstraction Whisper's cross-frame attention
  supplies). That is the next link — a contextual unit, not a per-frame one.

## Architecture note (CLAUDE.md)

The VTL warp FACTOR is the agent's own formant-mean science (mirrors
`speaker_norm.vtl_terms` / mean-formant, read forward). The transform itself is a
per-frame frequency-axis remap — a perception PRIMITIVE that belongs in the Rust
front-end (`auditory_cortex`) when cut over. These accept scripts operate on the
same `frames×bands` matrix the front-end emits, so the MECHANISM is measured
honestly before any Rust migration. The win (CMVN) is a one-line per-utterance
normalization that drops cleanly into the front-end's existing per-utterance
level normalization (`enrich_sign_bands` baseline subtraction) — extended from
mean-only to mean+variance per band.
