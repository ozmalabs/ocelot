# Autopoietic loop — iteration 4

Turn the crank a fourth time: pursue the constraint iteration-3 LOCATED by live
measurement — **coarsen the unit grain (run-length collapse) BEFORE chunking**. The
per-frame unit stream runs ~7.5 units/word, so the TP chunker (median OR the local-min
Term iter-3 forward-built) inherits the grain and sticks near ~7 chunks/word no matter
how sharp the boundary rule is. This iteration builds the coarsening, and it WORKS
upstream (grain halved, purity up substantially) but does NOT yet cross the recognition
baseline — it relocates the loss to the decoder + cross-speaker chunk invariance, with
numbers. **All numbers below are from LIVE output, not prose or constants.**

## 1. PICK — the agent's ranker, live

The coarsen-grain finding is the constraint iter-3's measurement located *inside* the
already-picked **word-scale chunking** axis (frames/word 7.56). It is not a new
implication-shape in the order-N synthesis menu — the menu has no "coarsen-grain"
shape — so, like the LPC axis in iter-2, it is **measurement-derived**: the open axis
the agent picks is word-scale chunking, and iter-3's live measurement names the binding
sub-constraint within it.

Live ranker output (the agent's graph-resident Argmax over `effective_score`, after
replaying iter-3's recorded clustering move-on):

```
OPEN-ONLY RANK (prune=True), before any move-on:
  payoff=6 score=5999  ['unsupervised-clustering', 'cross-speaker-clustering']
  payoff=4 score=3999  ['transitional probability', 'word-scale chunking']

OPEN RANK after clustering move-on (iter-3 state):
  eff_score=3999       ['transitional probability', 'word-scale chunking']
  eff_score=-994001    ['unsupervised-clustering', 'cross-speaker-clustering'] EXHAUSTED

LIVE PICK NOW: ['transitional probability', 'word-scale chunking', 'statistical segmentation']
```

The agent's native Argmax picks **word-scale chunking** (clustering EXHAUSTED via the
iter-3 move-on signal). Coarsen-grain is the located next step *within* that axis. Pick
is honest and live.

## 2. BUILD — run-length collapse (composed vs adapter split, criterion choice)

`domains/run_length_collapse.py`. A PHONE is a stable acoustic segment spanning
multiple frames that share an articulatory configuration; the k-means codebook already
discretises each frame to a unit, so a phone is a RUN of consecutive same-unit frames.
Collapsing each run to one coarse unit drops the stream from the per-frame grid toward
the phone/syllable grid (the HuBERT-style "de-duplicate consecutive units" step).

- **Composed (graph-resident):** the collapse DECISION is a Term the agent evaluates
  natively (`substrate.evaluate`), mirroring `forward_segmentation.local_min_boundary_term`.
  Each frame is a `Frame` node carrying `unit`, `prev_unit`, `step`, `step_level`; the
  RUN-START set (frames that begin a new coarse unit) is a `Filter` Term:
  - raw-id:    `Filter(frames, f, Not(Eq(f.unit, f.prev_unit)))`
  - stability: `Filter(frames, f, Gt(f.step, f.step_level))`
  Built from `Not/Eq/Gt/Attr/Filter/NodesWhere`, all already in `term.rs` — no new Rust
  primitive needed.
- **Adapter (mechanical I/O):** Python translates frames -> `Frame` nodes (the same
  structure translation `tp`/`prev_tp` are in `forward_segmentation`) and assembles the
  merged spans the run-starts delimit. No decision in Python.

**Collapse-criterion choice (the agent's, from its science).** Two readings, both built:
- **RAW-ID** is the agent's PRIMARY pick — the direct, parameter-free reading of its own
  codebook: the unit IS the discretised stable segment, so equal-id runs ARE the phones.
- **STABILITY** is the order-1 refinement (`order_n_concepts`): per-frame quantisation
  FLICKERS, so raw-id under-merges at dither points. Merge across small acoustic steps
  (low trajectory velocity), split only at a step above the running-median step level (a
  structure-derived statistic, not a swept knob).

Synthetic validation (graph Term evaluates natively): `[5,5,5,2,2,7,7,9,7]` (9 frames)
-> raw-id coarse `[5,2,7,9,7]` (5 units). The machinery is correct.

## 3. MEASURE — live, LibriSpeech (the deliverable)

### Grain + chunking + purity (`scripts/coarsen_grain_probe.py`)

40 train utts / 20 speakers, K=48, held-out speakers, the agent's default
gammatone -> invariant transform -> k-means codebook -> [collapse] -> local-min TP
chunker -> DTW chunk->word lexicon:

```
metric                           PER-FRAME       RAW-ID    STABILITY
--------------------------------------------------------------------
units-per-word (grain)                7.58         4.76         3.80
frames-per-word                       7.58         7.58         7.58
chunks-per-word (->1-3)               6.51         4.25         3.46
total units                           7653         4802         3832
total chunks                          6566         4284         3490
total words                           1009         1009         1009
cluster purity (->1.0)               0.386        0.492        0.588
  MULTI-member purity                0.293        0.328        0.379
```

Apples-to-apples on the iter-3 60-utt set (matches iter-3's baseline exactly:
per-frame chunks/word 7.13, purity 0.287):

```
none      grain 7.96  chunks/word 7.13  purity 0.287  multi 0.237
raw_id    grain 4.94  chunks/word 4.59  purity 0.342  multi 0.264
```

**Coarsening WORKS upstream.** Grain 7.5-8 -> 4.8 (raw-id) / 3.8 (stability); chunks-
per-word 6.5-7.1 -> 4.3-4.6 (raw-id) / 3.5 (stability); purity 0.29-0.39 -> 0.34-0.59.
Stability beats raw-id on REAL invariant-transformed frames (continuous steps, where
the median level genuinely merges flicker — unlike the degenerate all-equal-step
synthetic case). HONEST: grain did NOT reach "a few per word" in the strong sense
(3.8-4.8, not ~1-2) and chunks-per-word is 3.5-4.6, not 1-3 — coarsening helped A LOT
but left a residual.

### End-to-end recognition (`scripts/continuous_speech_recognition.py`, `COLLAPSE_MODE`)

45 train / 18 held-out-speaker test utts, K=48. Apples-to-apples, same corpus, only the
collapse differs:

```
condition              chunks/word  purity  multi-purity   WER    word-acc
per-frame (iter-3)         7.47      0.369     0.300       6.609    0.008
stability collapse         3.76      0.579     0.382       4.244    0.008
                                                          unigram   0.080
```

**Recognition did NOT cross unigram.** Word accuracy stayed at 0.008 (3/363), BELOW the
unigram baseline 0.080, in both conditions. Coarsening cut WER (6.61 -> 4.24) and
roughly halved chunks-per-word and lifted purity — the upstream is much healthier — but
the word accuracy is flat. This is the honest "helped a lot AND revealed the next
constraint" outcome the brief anticipated, NOT a milestone crossing.

### Why — the precise next constraint (located by this measurement)

1. **Residual over-segmentation.** 3.76 chunks/word still > 1: the recogniser emits
   ~3.8x too many words, inflating WER (>1) by insertions. Run-length collapse on the
   per-frame codebook coarsens to ~phone scale, not word scale — a second grouping
   (syllable/word-level merge) is still needed above it.
2. **Cross-speaker chunk invariance (the clustering gap, ~0.46).** Multi-member purity
   is 0.382 even after coarsening — held-out-speaker chunk prototypes still confuse in
   the DTW chunk->word lexicon. This is the cross-speaker-clustering axis the ranker
   scored highest (payoff 6) and which iter-1/iter-2 left at purity 0.460 < 0.483; it
   re-surfaces here as the decoder's confusion. The loss has relocated from the chunker
   (now much better) to the chunk->word grounding + cross-speaker unit quality.

## 4. Interventions (named plainly)

- **New domain module (graph-resident build):** `domains/run_length_collapse.py` — the
  run-start collapse Term (composed) + frame-node translation + span assembly (adapter).
  The DECISION is the agent's Term, evaluated natively. NOT a Python `if` over graph
  state.
- **New probe script (world adapter, no agent reasoning):** `scripts/coarsen_grain_probe.py`.
- **Recogniser mode-threading:** added `COLLAPSE_MODE` / `BOUNDARY_MODE` env routing to
  `scripts/continuous_speech_recognition.py:chunk_an_utterance` (default `none`/`median`
  = iter-3 behaviour untouched). The same mechanical mode-threading role iter-3's
  `boundary_mode` plays — no decision.
- **Did I tune to a number?** No. Raw-id is parameter-free; the stability split level is
  the running median of the steps (a statistic OF the data), not swept. Both criteria
  were built and BOTH reported; the measurement, not a sweep, says stability > raw-id on
  real frames.
- **Did I advance the pick by hand?** No — the agent's native Argmax picks word-scale
  chunking; coarsen-grain is iter-3's measurement-located sub-constraint within it.
- **A peer / an LLM authoring code?** No.

## 5. Status / acceptance

- Agent PICKED word-scale chunking via its own ranker (live Argmax above); coarsen-grain
  is the iter-3-located constraint within it.
- Forward-built run-length collapse: composed run-start Term + adapter frame/span I/O;
  criterion = raw-id (primary) + stability (order-1 refinement), both built and measured.
- LIVE measurement: coarsening DROPPED the grain (7.5-8 -> 3.8-4.9), DROPPED chunks-per-
  word (6.5-7.5 -> 3.5-4.6), and LIFTED purity (0.29-0.39 -> 0.34-0.59). Real, large
  improvements. Recognition did NOT cross unigram (word-acc 0.008 vs 0.080) — it cut WER
  (6.61 -> 4.24) but the loss relocated to residual over-segmentation + cross-speaker
  chunk invariance (the clustering gap ~0.46). HONEST: helped a lot, revealed the next
  constraint — not a milestone.
- `test_stt_pipeline` + `test_perception_self_assessment`: **12 passed** (default
  `COLLAPSE_MODE=none` keeps iter-3 behaviour, so existing tests are untouched).
- Not committed; left in the working tree.

### Reproduce

```
python -m scripts.coarsen_grain_probe 40 24 48           # grain/chunks/purity table
COLLAPSE_MODE=stability python -m scripts.continuous_speech_recognition 45 18 18 48
COLLAPSE_MODE=none      python -m scripts.continuous_speech_recognition 45 18 18 48
```
