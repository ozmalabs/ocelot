# Autopoietic loop — iteration 9 (recognition: word-scale chunking + cross-speaker lexicon)

Turn the crank a ninth time on the recognition frontier, now on the **upgraded
machinery** (the parallel-stream native-shape-edge harvest replaced the
text-pattern shape harvest). Two jobs: (1) report whether the upgrade gives
cleaner gap-synthesis; (2) forward-build the two recognition constraints iter-8
located — (a) the cross-speaker chunk-similarity metric / embedding, and (b)
word-scale chunking (over-segmentation) — and measure recognition vs unigram LIVE.

**Honest headline.** The upgrade SHARPENED the gap-synthesis dramatically (firing
breadth median 175→0; 73 noisy cross-domain axes → 2 axes, BOTH the recognition
frontier). Constraint **(b) over-segmentation is SOLVED** (chunks/word 3.23→1.30,
WER 4.13→1.52). Constraint **(a) the cross-speaker lexicon is NOT** — under a
position-free content-word-recall control, the lexicon retrieves words at the
frequency-prior level (recall 0.09–0.11 vs a frequency-matched random baseline
0.11–0.12), so it adds no cross-speaker discriminative signal on held-out speakers
at this corpus scale. **Recognition did NOT cross unigram.** The session's real
deliverable is the solved over-segmentation + a control that precisely re-locates
the remaining loss to cross-speaker word grounding. I did NOT tune to cross; the
freq-matched control kills the apparent "beats unigram recall" gain.

## 1. STEP 1 — the upgraded machinery's gap-synthesis (cleaner gaps?)

`scripts/_harvest_precision_measure 400` and `scripts/iter5_frontier 400` (live),
upgraded machinery vs the iter-5 text-pattern era:

| measure | iter-5 (text-pattern) | iter-9 (native shape edges) |
|---|---|---|
| shape firing breadth (median / max) | **175 / 2861** | **0 / 319** |
| shapes firing on >5% of corpus | many | **1** |
| distinct OPEN axes surviving | 73 | **2** |
| artifact axes (single-shape) | 96% (70/73) | the 2 are single-shape |
| what the axes ARE | cross-domain noise (comet, red_giant, pypy…) | **both the recognition frontier** |

The native-shape-edge harvest collapsed the noise floor: instead of 73 promiscuous
cross-domain artifact axes, **only 2 axes survive and BOTH are recognition** —
(a) `unsupervised-clustering / cross-speaker-clustering` (payoff 24, the PICK) and
(b) `transitional-probability / word-scale-chunking` (payoff 15, runner-up). These
are EXACTLY the two constraints iter-8 located by measurement. The guided loop's
Argmax picks the cross-speaker-clustering axis; the runner-up is word-scale
chunking. So the upgrade's gap-synthesis is much cleaner in **signal-to-noise**
(which axes survive) and the surviving axes ARE the genuine frontier.

**Honest caveat on the upgrade.** The two surviving axes are still **single-shape**
(one `latent_structure` shape firing across 24 postulates, one canned consequence
text); corroboration count is still 0 (no axis has ≥2 corroborating shapes). The
promiscuity gate is now a no-op (nothing is promiscuous enough to trip it). So the
improvement is "the noise is gone and the survivors are the right axes", NOT "the
gaps are now multi-shape-corroborated". The signal is in WHICH axes survived.

## 2. STEP 2 — forward-built the two constraints

### (b) Word-scale chunking — over-segmentation (the dominant decode loss). SOLVED.

The agent's chunker (`domains/forward_segmentation`) reads word boundaries off
TP troughs (Saffran statistical_learning). The recognizer chunked each utterance
**independently** (`forward_segment([one_utterance], n_passes=1)`) — but a single
short utterance has almost no recurrence, so per-utterance TP troughs are noise and
the chunker over-segments (~3.2 chunks/word). **The agent's own science says the
fix:** statistical_learning reads recurrence ACROSS the corpus, not within one
utterance. Forward fix = estimate TP ONCE over the whole train corpus, then chunk
each utterance against that SHARED corpus-scale TP via the SAME graph-resident
`local_min` boundary Term.

- **Composed (agent's, unchanged):** the boundary DECISION — the `local_min` TP-trough
  Term evaluated natively via `find_boundaries_via_graph`. No new Term.
- **I/O (world adapter, new):** `coarse_stream_of` + `chunk_with_corpus_tp` in
  `continuous_speech_recognition.py` — build all coarse-unit streams, `estimate_tp`
  over all of them once, chunk each utterance with the shared TP. Gated by `CORPUS_TP=1`
  (default 0 = per-utterance, iter-4 behaviour; tests/results untouched).

Measured (`scripts/iter9_chunkscale_probe 22 14 48`, live):

```
config                                chk/word   mean_len   recur
per-utt TP, local_min, passes=1          3.23       1.21     0.85
per-utt TP, local_min, passes=4          3.10       1.19     0.85   (n_passes barely helps)
CORPUS  TP, local_min, passes=1          1.39       2.82     0.23   <- word scale
```

Corpus-scale TP collapses over-segmentation 3.23→1.39 (the chunker self-terminates
at word scale — pass 2 sees degenerate TP and stops; n_passes>1 is a no-op). This
is the agent's own `forward_segment` mechanism, simply fed corpus-scale sequences.

### (a) Cross-speaker chunk-similarity — rate-invariant embedding. BUILT, did NOT beat baseline.

iter-8 located: the agent's Euclidean clusterer needs fixed-length vectors, and the
resample discards the speaking-rate TIME-WARP DTW tolerated. Forward fix from the
agent's `order_n_concepts`: a rate-invariant fixed-length embedding — describe the
chunk by the SHAPE of its trajectory over NORMALISED time (order-0 path + order-1
velocity between fixed slots). Order-N differences over normalised time describe the
path, not the clock, so the same word at different rates embeds to the same point.

- **Composed (agent's):** the order_n (order-0 + order-1 over normalised-time slots).
- **I/O:** `chunk_traj_vector(embed="rate_inv")`. Gated by `CHUNK_EMBED=rate_inv`
  (default `traj` = iter-8).

It did NOT lift cluster purity above greedy (below).

## 3. MEASURE — LIVE, end-to-end, held-out speakers

`continuous_speech_recognition.py`, LibriSpeech dev-clean, held-out SPEAKERS,
stability collapse. Baseline = per-utterance chunking (iter-4/8); iter-9 = `CORPUS_TP=1`.

### 22 train / 10 test, K=48 (greedy lexicon):

```
                       chk/wd   WER    word-acc   content-recall   freq-rand-recall
baseline (per-utt TP)   3.23   4.125    0.000          —                 —
iter-9   (corpus  TP)   1.30   1.518    0.006        0.111             0.116
unigram                  —     0.970    0.031        0.028 (set)         —
```

### 60 train / 20 test, K=48 (greedy lexicon, larger):

```
                       chk/wd   WER    word-acc   content-recall   freq-rand-recall
iter-9   (corpus  TP)   1.36   1.662    0.010        0.090             0.115
unigram                  —     0.943    0.042        0.032 (set)         —
chance                   —     1.000    0.0014        —                 —
```

### 22/10, CLUSTER lexicon + rate_inv embedding (the agent's PICKED frontier):

```
                       chk/wd   WER    word-acc   content-recall   freq-rand-recall   multi-purity
cluster + rate_inv      1.30   1.492    0.006        0.083             0.109              0.329
greedy   (same chunks)  1.30   1.518    0.006        0.111             0.116              0.500
```

### Reading the numbers honestly

1. **(b) Over-segmentation is solved.** chunks/word 3.23→1.30 (word scale, target
   1–2). WER fell 4.13→1.52 — the insertion mass from ~3× too many words is gone.
   This was the dominant decode loss iter-4/8 flagged. Real, reproducible.

2. **WER did NOT cross unigram** (1.52 vs 0.97). With chunks at word scale, WER is no
   longer dominated by insertions — it re-locates to the LEXICON (wrong-word
   substitutions), which is constraint (a).

3. **The content-recall control is decisive for (a).** word-acc is position-aligned,
   which the unigram baseline games (always-'the' scores every 'the' position) and a
   length-off-by-30% chunker cannot win even with the right words. The position-free
   content-word-recall isolates LEXICON retrieval. The agent's recall (0.09–0.11)
   **beats the unigram set (0.03)** but does **NOT beat a frequency-matched random
   baseline (0.11–0.12)** (same #distinct words as the hyp, drawn by train frequency,
   averaged over 20 draws). **So the lexicon retrieves words at the frequency-prior
   level — no cross-speaker discriminative signal on held-out speakers.** Constraint
   (a) is genuinely unsolved.

4. **The rate-invariant embedding did not help.** cluster+rate_inv content-recall
   0.083 < greedy 0.111, and cluster multi-purity 0.329 < greedy 0.500. The embedding
   was the right idea from the science but the binding limit is upstream of the
   metric: at 22–60 held-out utts there is too little cross-speaker word REPETITION
   for ANY lexicon to learn a speaker-invariant chunk→word map (multi-member purity
   is computed over only 4–19 chunks). The corpus is the wall, not (only) the metric.

5. **Recognition crosses CHANCE (word-acc 7× chance on 60-utt) but not unigram.** No
   crossing. Honest.

## 4. Controls / honesty

- **Apples-to-apples:** `iter8_lexicon_compare` frames+chunks ONCE and scores both
  lexicons + both embeddings on the IDENTICAL word-scale chunks. Only the lexicon
  builder / embedding differs.
- **The freq-matched control killed the apparent gain.** Agent content-recall beats
  the unigram SET, which alone would read as "above baseline" — but the
  frequency-matched random draw (the honest control: a guess of the same size drawn
  by the train frequency prior) recalls MORE. The control is averaged over 20 draws
  so it is a stable expectation, not one sample. I report the negative plainly.
- **Did I tune to cross?** No. CORPUS_TP uses the running-median trough level (the
  data's own statistic, unchanged). cluster k = distinct train words. CHUNK_EMBED is
  an architecture choice, not a swept knob. No threshold was searched to pass a metric.
- **Deterministic numbers reproduce:** chunks/word 1.30, WER 1.518, word-acc 0.006
  reproduce exactly across re-runs (seed-fixed perception/chunker). Content-recall is
  corpus-slice-dependent (0.09–0.11) but is below the freq baseline in every run.
- **native-eval-bound:** the cluster lexicon is ~60–300 s/clustering pass, so cluster
  runs are 22/10; greedy scales to 60/20. Said plainly.

## 5. The located next constraint (iteration-10)

The recognition wall is now precisely: **cross-speaker word grounding is
corpus-starved** — at the tractable held-out-speaker corpus scale there is too
little repeated-word-across-speakers data for the chunk→word lexicon to exceed the
frequency prior. Two forward paths, both the agent's:
- **More cross-speaker repetition without more compute:** the lexicon should ground
  on a corpus where the SAME words recur across many speakers (a closed small
  vocabulary, or the agent's persona_speech_world where it controls the speakers and
  can repeat a word across voices) — the babble-loop grounding, not a bigger blind
  LibriSpeech sample. This is the agent's own persona/self-speech world applied to the
  lexicon, not a metric tweak.
- **A faster native clusterer** so cluster scales to the corpus where (a) could show:
  the native per-token Argmin assignment is the bottleneck (~300 s/pass); a batched
  assignment Term would let the cross-speaker clusterer run on 10× the chunks.

Over-segmentation is no longer the binding constraint; the lexicon's cross-speaker
generalisation is.

## 6. Status / acceptance

- **(1) upgraded-machinery gap-synthesis:** verified cleaner — firing breadth median
  175→0, 73 noisy axes → 2, both the recognition frontier; the PICK = cross-speaker
  clustering, runner-up = word-scale chunking (iter-8's two constraints). Honest
  caveat: survivors still single-shape (corroboration count 0).
- **(2) builds:** (b) corpus-scale TP word-scale chunking (composed boundary Term
  unchanged + I/O `coarse_stream_of`/`chunk_with_corpus_tp`, `CORPUS_TP=1`); (a)
  rate-invariant order_n embedding (composed order-0+order-1 + I/O `chunk_traj_vector
  embed=rate_inv`, `CHUNK_EMBED=rate_inv`). Plus a position-free content-recall
  control + freq-matched baseline in the recognizer.
- **(3) recognition vs unigram:** chunks/word 3.23→1.30 and WER 4.13→1.52 (real,
  reproducible) — but word-acc 0.006–0.010 < unigram 0.031–0.042, and content-recall
  0.09–0.11 < freq-matched random 0.11–0.12. **PARTIAL on (b), NEGATIVE on (a).**
- **(4) crossing:** **did NOT cross unigram.** Real partial: over-segmentation solved
  (the dominant loss), recognition above CHANCE but at the frequency prior, not above
  it. Next constraint: cross-speaker word grounding is corpus-starved.
- `test_stt_pipeline` + `test_perception_self_assessment` + `test_process_meta_assessor`
  + `test_gap_guidance`: **32 passed** (all new behaviour env-gated; defaults
  CORPUS_TP=0 / CHUNK_EMBED=traj / LEXICON_MODE=greedy / COLLAPSE_MODE=none unchanged).
- Not committed; left in the working tree + this doc.

### Reproduce

```
# machinery delta (cleaner gaps + the pick)
python -m scripts._harvest_precision_measure 400        # firing breadth 0, 2 axes
python -m scripts.iter5_frontier 400                    # PICK = cross-speaker clustering

# constraint (b): word-scale chunking
python -m scripts.iter9_chunkscale_probe 22 14 48       # corpus-TP -> 1.39 chk/word

# end-to-end recognition (the table)
CORPUS_TP=1 COLLAPSE_MODE=stability \
  python -m scripts.continuous_speech_recognition 22 10 14 48     # greedy, 1.30 chk/wd
CORPUS_TP=1 COLLAPSE_MODE=stability \
  python -m scripts.continuous_speech_recognition 60 20 24 48     # larger, content-recall control
CORPUS_TP=1 COLLAPSE_MODE=stability LEXICON_MODE=cluster CHUNK_EMBED=rate_inv \
  CLUSTER_ITERS=12 python -m scripts.continuous_speech_recognition 22 10 14 48

# apples-to-apples lexicon/embedding compare on the SAME word-scale chunks
CORPUS_TP=1 COLLAPSE_MODE=stability CHUNK_EMBED=rate_inv CLUSTER_ITERS=10 \
  python -m scripts.iter8_lexicon_compare 22 10 14 48

python -m pytest tests/test_stt_pipeline.py tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q     # 32 passed
```
