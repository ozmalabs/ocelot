# The under-determined regime, on REAL data

v2 (`docs/frame_inference_v2.md`, commit 30e8d251) showed that multi-frame
**weighted-admissibility** beats both single-frame and the dot-product control
*exactly* when a single acoustic frame under-determines — but it manufactured the
under-determination with **synthetic additive noise (SNR sweep)** and an **imposed
bigram**. This is the same claim on **real data**, where the under-determination
arises **naturally** from cross-speaker acoustic variation and the context is a
**real language model counted from real transcripts** (not imposed).

## The regime

| component | v2 (synthetic) | here (real) |
|---|---|---|
| under-determination | additive noise SNR sweep | **natural cross-speaker acoustic ambiguity** |
| context model | **imposed** bigram | **real** word n-gram counted from LibriSpeech transcripts |
| sequence | concatenated digits under the imposed bigram | **real word in a real sentence** with its real neighbours |
| held-out | held speakers | held speakers (never banked) + LM never sees audio |

- **Corpus / vocab / split.** Constrained vocabulary = the 35 Speech-Commands
  words (real isolated word audio per word, cross-speaker). The acoustic frame is
  the v1 frame-relative 1-NN recogniser over held-out speakers' SC clips; cross-
  speaker LOSO, held clips **never banked**. The real LM is the word n-gram of
  **LibriSpeech dev-clean transcripts** (2703 real utterances), counted over the
  full transcript vocabulary, restricted to the 35-word candidate set per query.
- **Real test items.** Every position in the real transcripts whose word is in the
  SC vocab (**1504 real items**), each tagged with its **real** predecessor /
  successor / skip-2 neighbours — the genuine sentence context. The acoustic is a
  held-out speaker's real clip of that word.

## Donkey audit

- The LM is **real, not imposed**: the SC-vocab targets follow the corpus's own
  skew (`on` 323, `one` 219, `no` 168, `up` 152, ... `stop` 5) — never set by us.
- The real context genuinely constrains: `P(target | real predecessor)` alone
  ranks the true word at mean **0.83 / 35** (chance 17.0), top-1 **0.656** — the
  real n-gram does real work.
- The cross-speaker acoustic genuinely under-determines: single-frame
  frame-relative recognition is **~0.13–0.18** (chance 0.029) — well above chance,
  far below resolved. Speaker variation **is** the natural under-determination.
- Frames are owned models (v1 acoustic recogniser + real n-gram counts); the
  collapse ops are v2's owned `weighted_admissibility` / `dot_product_combine`
  (no net, no fit, no gradient). The LM is counted from transcripts and never sees
  audio (no acoustic leakage). CortexLoop untouched.

## The three regimes

- **(i) single-frame** — acoustic soft-excluder argmax (no LM).
- **(ii) dot-product** — all frames as positive scores, scalar weighted sum, argmax
  (the premature scalar-collapse control).
- **(iii) weighted-admissibility** — all frames as soft excluders, vector-weighted
  **intersection** (sum of weighted log-admissibilities), kept soft, argmax.

Frames: acoustic (cross-speaker) + real-context `P(t|prev)` + future-sheaf
`P(t|next)` (1-step) and `P(t|next2)` (2-step). Sweep: LM weight × sheaf depth.

## Result (n=1800 real cross-speaker items, 34 held-out speakers, 35-word vocab)

Captured: `/tmp/under_det_real.log` (marker `UNDER_DETERMINED_REAL_COMPLETED`).
Single-frame is flat at **0.131** (chance 0.029) — the cross-speaker acoustic
genuinely under-determines.

| lm_w | sheaf | single (i) | dot-product (ii) | wadm (iii) | iii − i | iii − ii |
|---|---|---|---|---|---|---|
| 0.5 | 1 | 0.131 | 0.477 | 0.621 | +0.490 | +0.144 |
| 1.0 | 1 | 0.131 | 0.677 | 0.727 | +0.596 | +0.051 |
| 2.0 | 1 | 0.131 | 0.691 | 0.737 | +0.606 | +0.047 |
| 4.0 | 1 | 0.131 | 0.687 | 0.733 | +0.602 | +0.046 |
| 0.5 | 2 | 0.131 | 0.640 | 0.707 | +0.576 | +0.067 |
| **1.0** | **2** | **0.131** | **0.722** | **0.769** | **+0.638** | **+0.047** |
| 2.0 | 2 | 0.131 | 0.703 | 0.767 | +0.636 | +0.063 |
| 4.0 | 2 | 0.131 | 0.694 | 0.759 | +0.628 | +0.065 |
| 1.0 | 2+ctx2 | 0.131 | 0.772 | 0.826 | +0.694 | +0.054 |

**VERDICT (principled cell lm_w=1.0, sheaf=2): CONFIRMED.** On the real
under-determined cross-speaker regime, weighted-admissibility beats **both**:
- **single-frame by +0.638** (0.131 → 0.769) — the real LM over-determines what
  the cross-speaker acoustic alone cannot resolve. (Real LM helps cross-speaker:
  *not* the KILL.)
- **dot-product by +0.047** (0.722 → 0.769), past the 0.02 bar at **every** cell
  (range +0.046 … +0.144). Soft intersection beats the premature scalar sum: where
  a wrong-but-confident acoustic must be **vetoed** by the LM, the scalar dot-
  product can let a high acoustic score out-sum the LM's exclusion, while the
  weighted-admissibility intersection carves it away. (Soft-vs-scalar holds on real
  data: *not* the KILL.)

Both the v2 SNR/imposed-bigram claims reproduce on **real data with a real,
counted n-gram** — the under-determination natural (cross-speaker), the context
real (LibriSpeech transcripts), the speakers held out.
