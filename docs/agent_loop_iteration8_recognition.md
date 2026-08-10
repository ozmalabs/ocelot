# Autopoietic loop — iteration 8 (the recognition stage: cross-speaker CHUNK clustering)

Turn the crank an eighth time, on the loop's genuine frontier (post yardstick-fix): the
**recognition stage** — the chunk->word LEXICON that iter-4 left below unigram. The
agent forward-builds cross-speaker CHUNK clustering (lift its OWN composed clusterer
from units/tokens to word-CHUNKS) so the same word's chunks from different speakers
land in one lexicon entry, then we measure end-to-end recognition vs unigram.

**The honest result is a genuine NEGATIVE / partial: the composed cross-speaker chunk
clusterer did NOT beat the iter-4 greedy DTW-merge lexicon on this corpus, and neither
crosses unigram. Recognition did NOT cross unigram for the first time. The measurement
re-locates the binding constraint precisely: it is NOT the lexicon's clustering MERGE
strategy (greedy DTW already groups better than fixed-slot Euclidean clustering); it is
(a) residual over-segmentation (~6 chunks/word) and (b) the chunk SIMILARITY METRIC —
DTW (time-warp-tolerant) beats the fixed-length trajectory embedding the agent's
composed Euclidean clusterer requires.** All numbers below are LIVE
(`scripts/iter8_lexicon_compare.py`), not prose or constants. I did NOT tune to cross
unigram; I report what crossed and what did not.

## 1. PICK — the recognition-stage loss (carried from iter-4, re-confirmed)

The loop's pick is the recognition-stage chunk->word lexicon. iter-4 located the loss:
recognition word-acc 0.014 < unigram 0.064; the chunk->word lexicon was unusable
(iter-3 greedy purity 0.179, no collapse). The brief's frontier: forward-build
cross-speaker CHUNK clustering to make the lexicon usable.

## 2. BUILD — cross-speaker CHUNK clustering (composed vs I/O split)

### The forward-design (from the agent's latent_structure + invariance science)

The agent's `domains/cross_speaker_clustering.cluster` already composes label-free
clustering as graph Term-trees (Argmin nearest-centroid assignment + Sum/Count centroid
mean — the CMVN move lifted from frames to tokens). iteration-8 lifts it ONE MORE LEVEL,
from units/tokens to word-CHUNKS, exactly the latent_structure shape the agent harvested:
"the same word's tokens across speakers form one cluster."

**The bridge (the only new code, in `scripts/continuous_speech_recognition.py`):**

- `chunk_traj_vector(block)` — the agent's composed clusterer clusters FIXED-LENGTH
  token vectors (Euclidean), but a chunk is a VARIABLE-LENGTH invariant frame matrix.
  The agent's own science supplies the bridge: a word's identity is its TRAJECTORY SHAPE
  (`spectrum_signature_traj` / the `_traj_flatten` move the cross-speaker-clustering
  probe already uses). Resample the chunk's frame matrix to a fixed number of time-slots,
  flatten, mean-centre + unit-norm. This is the SAME trajectory representation the
  agent's clusterer was validated on — one level up (chunk, not whole utterance).
- `ClusterLexicon` — pool EVERY train chunk's trajectory vector across all speakers into
  ONE cloud, run the agent's composed clusterer (`cross_speaker_clustering.cluster`, the
  graph Term-trees evaluated natively), label each cluster by its majority aligned word,
  recognise by nearest centroid. This REPLACES iter-4's greedy single-pass DTW-merge
  (order-dependent, never pooled across speakers).

**Composed vs I/O split (architecture rule):** the clustering DECISION is the agent's
composed graph Term-trees (Argmin assignment + Sum/Count mean), evaluated natively in
the substrate via `substrate.evaluate` — NOT Python arithmetic. The trajectory
embedding, the cloud pooling, the cluster-label majority vote, and nearest-centroid
recognition are the mechanical I/O boundary (the permitted world-adapter role), exactly
as the brief allows ("the codebook/DTW/lexicon assembly is the permitted I/O boundary").
No new Rust primitive was needed.

**Wiring (mode-threaded, default unchanged):** `LEXICON_MODE` env on
`continuous_speech_recognition.py` (`greedy` = iter-4 default, `cluster` = iter-8). The
default `greedy` keeps all existing results/tests untouched. A dedicated comparison
driver `scripts/iter8_lexicon_compare.py` (a world adapter, no agent reasoning) frames +
chunks the corpus ONCE and scores BOTH lexicons on the SAME chunks — true
apples-to-apples.

## 3. MEASURE — LIVE, end-to-end, held-out speakers (the deliverable)

`COLLAPSE_MODE=stability CLUSTER_ITERS=10 python -m scripts.iter8_lexicon_compare 22 10 14 48`
LibriSpeech dev-clean, K=48, held-out SPEAKERS (speaker-independent). Both lexicons built
+ scored on the identical chunk set. Corpus is small (22 train / 10 test) because the
agent's composed clusterer is native-eval-bound (~300 s for one clustering pass at this
chunk count — said plainly, this is slow).

```
mode        purity   multi  sing%  chk/wd     WER   word-acc  #clust
--------------------------------------------------------------------
greedy       0.665   0.406   0.76    6.38    6.689    0.013    2000
cluster      0.273   0.270   0.04    6.38    5.575    0.000     320
--------------------------------------------------------------------
unigram                                      0.970    0.031   (word='the')
chance                                       1.000    0.0031
```

(A smaller integrated smoke run — `LEXICON_MODE=cluster ... 20 8 12 48`, stability
collapse — gave cluster purity 0.371 / multi 0.352, chk/wd 2.97; the cluster purity is
seed/corpus-sensitive in the 0.27–0.37 band. Either way it does NOT beat greedy's
multi-member purity.)

### Reading the numbers honestly

1. **Cluster purity did NOT beat greedy.** Multi-member purity (the honest number, over
   chunks in shared clusters): greedy **0.406** vs cluster **0.270**. The caveat cuts
   the OTHER way from what the brief expected: greedy's headline 0.665 IS inflated by
   76% singletons (it hit the 2000-prototype cap, so most chunks are their own trivially-
   pure prototype) — but even discounting that, greedy's grouped-chunk purity (0.41) is
   HIGHER than the cluster's (0.27). The agent's composed clusterer groups chunks across
   speakers WORSE than the greedy DTW-merge here, not better.

2. **Why — the chunk SIMILARITY METRIC, located precisely.** The greedy lexicon compares
   chunks by **DTW** (time-warp-tolerant — it aligns the same word spoken at different
   rates). The agent's composed clusterer requires **fixed-length** vectors (Euclidean
   Lloyd's), so the chunk must be resampled to a fixed trajectory; that resampling
   DISCARDS the speaking-rate warp DTW handles. Across speakers (who differ in rate as
   well as tract), the fixed-slot embedding loses the very invariance the clustering was
   meant to recover. The binding constraint at the lexicon is the METRIC, not the merge
   strategy.

3. **Over-segmentation re-surfaces as the dominant decode loss.** chunks-per-word is
   **6.38** here (stability collapse under-collapsed on this small corpus vs iter-4's
   3.76), so the recogniser emits ~6× too many words → WER > 1 by insertions (6.7 / 5.6)
   and position-aligned word-acc collapses (the hyp is 6× too long, positions misalign →
   0–1%). This is the residual over-segmentation iter-4 already flagged, here even
   stronger.

4. **Recognition did NOT cross unigram.** word-acc: greedy 0.013, cluster 0.000, unigram
   **0.031**. WER: both ≫ unigram 0.970. **No crossing.** Honestly: this is below where
   iter-4 sat relative to its own unigram (0.014 vs 0.064), within small-corpus noise —
   not progress on the end-to-end metric.

## 4. Controls / honesty

- **Apples-to-apples:** both lexicons scored on the IDENTICAL framed + chunked corpus
  (one shared perception/invariance/codebook/chunker pass), so the only difference is the
  lexicon builder. The comparison is fair.
- **Did I tune to cross unigram?** No. cluster k = distinct train words (one cluster per
  word, the natural target, NOT swept). CLUSTER_ITERS=10 is a compute cap, not a quality
  knob. Stability collapse level is the data's running-median step (iter-4, unchanged).
  The result does not cross unigram and I report that plainly.
- **Did the controls kill a claimed gain?** There is no gain to kill — the build did not
  beat the baseline. The honest finding is the located constraint (the DTW-vs-fixed-slot
  metric mismatch), not a crossing.
- **A peer / an LLM authoring code?** No. The clusterer is the agent's own composed
  Term-trees; the bridge is the same `_traj_flatten` trajectory move it already uses.

## 5. The located next constraint (what iteration-9 should pursue)

The lexicon's binding constraint is now precise: **the agent's composed clusterer needs
a time-warp-tolerant distance** (DTW-like) to group chunks across speaking rates, but
its Lloyd's/Euclidean form requires fixed-length vectors. Two forward paths, both
graph-expressible:
- a DTW-distance Term the assignment step can use (the chunk-comparison metric the greedy
  lexicon already wins with, made graph-resident so the agent's clusterer can use it); or
- a better fixed-length chunk EMBEDDING that is itself rate-invariant (e.g. the agent's
  order-N-over-normalised-time descriptors), so Euclidean clustering recovers what DTW
  does — composed from `order_n_concepts`.
Separately, **over-segmentation** (6.38 chunks/word) is still a first-order loss on WER;
a word-level grouping ABOVE the phone-scale collapse is needed before any lexicon can
read out word-rate.

## 6. Status / acceptance

- (1) BUILD: cross-speaker CHUNK clustering composed (the agent's Argmin/Sum-Count
  clusterer lifted to chunk trajectories) + I/O split (trajectory embedding, pooling,
  label vote, nearest-centroid recognition). `LEXICON_MODE=cluster` on the recognizer +
  `scripts/iter8_lexicon_compare.py` apples-to-apples driver.
- (2) LEXICON PURITY before->after: greedy multi 0.406 vs cluster multi 0.270 — the
  cluster build did NOT raise purity over the greedy DTW-merge (the brief's 0.179 was the
  no-collapse iter-3 number; stability collapse already lifted greedy to 0.41).
- (3) word-acc / WER vs unigram: **NOT crossed** (cluster word-acc 0.000, greedy 0.013,
  unigram 0.031; WER both ≫ unigram). PARTIAL/NEGATIVE, real numbers.
- (4) Recognition did NOT cross unigram. The honest finding is the precisely-located
  constraint: the lexicon's chunk-similarity METRIC (DTW vs fixed-slot Euclidean) +
  residual over-segmentation, NOT the clustering merge strategy.
- `test_stt_pipeline` + `test_perception_self_assessment` + `test_process_meta_assessor`
  + `test_gap_guidance`: **32 passed** (default `LEXICON_MODE=greedy` / `COLLAPSE_MODE=none`
  keeps prior behaviour, so existing tests are untouched).
- Not committed; left in the working tree + this doc.

### Reproduce

```
COLLAPSE_MODE=stability CLUSTER_ITERS=10 \
  python -m scripts.iter8_lexicon_compare 22 10 14 48        # the table above
COLLAPSE_MODE=stability LEXICON_MODE=cluster \
  python -m scripts.continuous_speech_recognition 20 8 12 48 # integrated path
python -m pytest tests/test_stt_pipeline.py \
  tests/test_perception_self_assessment.py \
  tests/test_process_meta_assessor.py tests/test_gap_guidance.py -q  # 32 passed
```
