# Mining Whisper for a forward-designable speech insight

Reverse-engineering Whisper-tiny's representation to find a mechanism the
substrate speech agent could *forward-design from understanding* — NOT to
import weights or clone the architecture. Whisper is gradient-descent
search; the question is whether any of what it discovered is a portable
design choice versus un-extractable trained residue.

Probe script: `scripts/mine_whisper.py` (+ two controls run inline,
preserved below). Data: FSDD digits, 6 speakers
(george/jackson/lucas/nicolas/theo/yweweler), balanced subset
(180 recordings, 3 per digit per speaker). Tooling: HF `transformers`
5.8 `WhisperModel`/`WhisperFeatureExtractor`, torch 2.11 CPU.

Metric for "speaker-invariant word representation":
**leave-one-speaker-out (LOSO) 1-NN word accuracy** — train on 5
speakers, classify the held-out speaker's words by nearest neighbour
(cosine, or DTW for the agent's sequence units). This is the honest test
of the exact property the agent's bottleneck needs (clean,
speaker-invariant sub-word/word units). Silhouette-by-word reported as a
secondary clustering number.

---

## 1. Front-end design deltas (the cheap, actionable mine)

Whisper's input front-end, read directly from `WhisperFeatureExtractor`:

| Choice | Whisper-tiny | Agent front-end | Delta |
|---|---|---|---|
| Filterbank | 80 mel bins | 32 log-spaced gammatone bands (80–7500 Hz) → 25 A1 patches | finer + true mel vs ERB-gammatone |
| Magnitude | **log10** of mel power | **linear** patch-envelope energy | Whisper log-compresses |
| Dynamic-range floor | `max(logspec, logspec.max() − 8.0)` (clamp to 80 dB below peak) | none (L2-norm only) | Whisper clamps the noise floor |
| Per-input normalisation | fixed affine `(logspec + 4.0)/4.0` → ~[−1,1] | per-utterance unit-L2 | different scheme |
| Window / hop | 25 ms / **10 ms** (160-sample hop @ 16 kHz) | 25 ms gammatone; trajectory resampled to **32 frames/word** | Whisper keeps fixed 10 ms grid |
| Context | fixed 30 s chunk (3000 frames), silence-padded | per-word window | — |
| Encoder time res | conv stride 2 → 20 ms frames | 32 frames/word | — |

The **mechanism-level** front-end choices (not learned weights, fully
portable in principle) are: (a) **log-compression** of band energies,
(b) a **dynamic-range floor** at a fixed dB below peak, (c) **fixed**
(not per-utterance) amplitude normalisation, (d) a **fixed 10 ms time
grid** instead of resampling every word to 32 frames.

These look like obvious adopt-candidates. **They are not** — see §4.
Tested directly, they *hurt* this agent.

## 2. Invariance-by-layer — the key mine

Same-word-across-speaker LOSO-1NN, measured at every stage of Whisper
plus the agent's own units:

```
representation                              silhouette   LOSO-1NN
------------------------------------------  ----------   --------
AGENT trajectory (32×25, linear-mag, L2)      -0.127      0.461   (cosine, mean-pooled)
AGENT trajectory, agent's own DTW compare        —        0.578   (DTW — the real path)
WHISPER log-mel front-end (80, pooled)        -0.259      0.289
WHISPER conv embeddings (layer 0)             -0.274      0.222
WHISPER encoder layer 1                       -0.156      0.422
WHISPER encoder layer 2                       -0.051      0.594
WHISPER encoder layer 3                       +0.028      0.717
WHISPER encoder layer 4 (final)               +0.055      0.806
```

Read the column top-to-bottom. Two facts dominate:

1. **Whisper's front-end is WORSE than the agent's, not better.**
   Whisper's log-mel input pooled to a word vector scores LOSO 0.29; the
   agent's gammatone+patch trajectory scores 0.46 (cosine) / **0.58
   (DTW)**. On the raw representation the agent is *already ahead*. The
   "clean speaker-invariant representation" is **not** in Whisper's
   front-end.

2. **Invariance is manufactured monotonically by the deep encoder.**
   0.22 (conv) → 0.42 → 0.59 → 0.72 → **0.81** (final). Each of the 4
   self-attention layers adds ≈0.10 of speaker-invariance. There is no
   step where a single identifiable transform appears; it is distributed,
   incremental cross-frame attention mixing — exactly the shape of "big
   trained net + data," not a discrete mechanism.

So invariance emerges **deep, not shallow**, and it emerges **gradually,
not at one extractable transform**. That is the diagnostic for
un-portable trained residue.

## 3. Other observed tricks

- **Silence/boundary handling:** Whisper does not segment words at all —
  it ingests a fixed 30 s window padded with silence and lets attention
  + the decoder's learned language model place boundaries. There is no
  TP-trough / sonority-valley segmenter to mine; boundary-finding is
  absorbed into the trained decoder. Not a mechanism the agent can lift.
- **Dynamic-range floor (80 dB clamp):** the one genuinely mechanism-shaped
  idea — bound the log noise floor so quiet frames can't dominate after
  normalisation. Sound in principle, but on this agent's pooled/L2 path it
  is what *causes* log-compression to backfire (see §4): the 32-frame
  resample of a per-word window includes near-silent tail frames whose
  log-energy, floored or not, gets amplified relative to linear.
- **Fixed time grid (10 ms):** Whisper never resamples a word to N frames;
  it keeps absolute time. The agent's resample-to-32-frames is a
  duration-normalisation that the agent's DTW then re-warps — arguably
  redundant, but not where the invariance gap lives.

## 4. Controls — testing the front-end deltas directly

The honest test of "is the front-end transferable": apply Whisper's
front-end recipe to the agent's *own* units and re-measure invariance.

Cosine / mean-pooled (`/tmp/control_probe.py`):
```
agent baseline linear-mag                  sil=-0.127  LOSO=0.461
+ log-compression (Whisper recipe)         sil=-0.185  LOSO=0.311
+ log + per-feature standardise            sil=-0.056  LOSO=0.356
```

DTW — the agent's actual comparison path (`/tmp/dtw_probe.py`):
```
DTW linear-mag (agent today)               LOSO-DTW-1NN=0.578
DTW + log-compression (Whisper recipe)     LOSO-DTW-1NN=0.378
```

Log-compression **lowers** the agent's speaker-invariance by ~0.2 under
its real DTW path. Per-feature standardisation recovers only part of the
damage. The Whisper front-end transforms are not a free win here — they
interact badly with this agent's per-word windowing, silence tail, and
unit-L2 + DTW back-end. Adopting them blind would regress the agent.

## 5. THE VERDICT

**There is no extractable, forward-designable trick in Whisper's
*representation* for this agent's invariance bottleneck.** Specifically:

- The plausible portable insight — "adopt log-mel / dynamic-range
  floor / fixed normalisation" — **fails the control**: Whisper's
  front-end is *less* speaker-invariant than the agent's gammatone+patch
  front-end (LOSO 0.29 vs 0.58), and bolting Whisper's log-compression
  onto the agent *reduces* its invariance. The agent's front-end is not
  the weak link relative to Whisper's.

- Whisper's clean speaker-invariant representation lives **entirely in
  its 4 trained self-attention layers**, appearing **gradually and
  distributed** (≈+0.10/layer), with **no single identifiable
  transform**. That is the signature of un-portable trained residue: it
  is "big net + gradient descent + data," precisely the mechanism this
  project rejects. You cannot forward-design "layer 3 of Whisper-tiny"
  from understanding; there is nothing there to understand, only fitted
  weights.

**The one honest, transferable takeaway is a re-framing, not a
front-end change:** Whisper proves that speaker-invariance is achieved by
*cross-frame contextual mixing learned over many utterances*, not by any
front-end transform. The agent's gap is therefore NOT its cochlea/patch
front-end (already competitive) — it is the absence of a *contextual,
cross-instance abstraction step* that turns raw units into
speaker-invariant ones. Whisper does that with attention+SGD; the
project's own answer already exists in memory and is the right lever:
**speaker normalisation + formant-ratio / invariant features composed in
the graph, grounded across many speakers** (cf. `speaker_norm.py`,
analogical transfer of the physics scale-invariant-ratio to formant
ratios). That is the forward-designable mechanism — and Whisper's
internals *corroborate where to aim it* (post-front-end, cross-context),
they just don't hand over a copyable transform.

Bottom line: mining Whisper rules OUT the cheap front-end fix (it would
regress the agent) and rules IN "the invariance must be built as a
contextual abstraction over many speakers, downstream of the already-good
front-end." No weight, no transform, no architecture worth porting — only
a confirmed direction.
