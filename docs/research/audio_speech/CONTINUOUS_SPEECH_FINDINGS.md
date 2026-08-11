# Continuous-speech recognition — end-to-end assembly of the agent's forward chain

**Script:** `scripts/continuous_speech_recognition.py`
**Corpus:** LibriSpeech dev-clean, speaker-independent (held-out speakers).
**Run reported:** 120 train utts / 24 speakers, 40 test utts / 6 HELD-OUT
speakers, codebook K=48, ~25 fps frames. (Tractable size — the agent's
graph-resident invariant transform costs ~5 s/utt, so the corpus is bounded by
compute, not by choice of a flattering number.)

This is the pivot off FSDD (isolated digits, saturated ~61 %, can show no
structure) onto continuous speech — the task the whole forward chain was built
for. The script is a WORLD ADAPTER: it ingests audio, drives the agent's own
graph chunker (`forward_segment`, which evaluates the boundary Term natively in
the Rust substrate) and the agent's graph-resident invariant transform
(VTLN→CMVN→predict-remove), reads the chunks back, and scores. No new agent
reasoning lives in Python; the lexicon/DTW scoring is the same measurement
pattern as the sibling accept harnesses (`invariant_units_accept`,
`forward_segmentation_demo`, the FSDD `predict_one`).

## The chain assembled (all the agent's own builds, all default)

1. perception — gammatone band trajectory, frames × 32 log-bands, ~25 fps.
2. invariance — `invariant_transform` (VTLN → CMVN → predict-remove), the
   agent's DEFAULT.
3. unit formation — k-means codebook over invariant frames (HuBERT-style),
   per-frame discrete units.
4. forward chunker — `forward_segmentation` TP-trough segmenter → CHUNKS.
5. grounding — on TRAIN, align each utterance's chunk sequence to its transcript
   words (proportional frame alignment), build a chunk-prototype → word lexicon
   (prototypes merged by DTW, each cluster → most-frequent aligned word).
6. recognise — held-out utterance → chunks → nearest chunk-prototype by DTW →
   its word → predicted word sequence. Adjacent duplicates collapsed
   (CTC-style).

## (1) Chunk → word alignment / lexicon quality — THE CRUX

| metric | value |
|---|---|
| total chunks / total words | 19 406 / 2 517 = **7.71 chunks per word** |
| chunk prototypes (DTW-merged) | 2 000 (hit the cap) |
| lexicon words covered | 523 distinct |
| train cluster purity | **0.179** |
| singleton-prototype fraction | 0.220 |
| MULTI-member purity (honest) | **0.160** (over 18 966 chunks in shared clusters) |

Reproduced identically across two independent runs.

The grounding does NOT give a usable lexicon. Two failures:

- **Over-segmentation ~8×.** The TP-trough chunker on the per-frame invariant
  unit stream cuts ~8 chunks per real word — not the near-1:1 the task brief
  hoped for. The "0.84 purity" cited for the chunker is *multi-unit chunk
  purity* on a coarser unit grid (a different metric): most chunks are short and
  fall trivially within one word, so that number can be high while the
  chunks-per-word *count* is far from 1:1. On a per-frame grid the count blows
  up.
- **Chunks of the same word do not cluster.** Cluster purity is 0.179 — a chunk
  lands in a prototype whose majority word it shares only 18 % of the time, and
  the DTW merge saturated the 2 000-prototype cap by 50 utts (almost every chunk
  became its own prototype). The invariant-feature chunks of the same word are
  not within DTW-merge range of each other.

## (2) Recognition on HELD-OUT speakers

| metric | agent chain | unigram ("the") | chance |
|---|---|---|---|
| WER (lower better) | **7.18** | 0.94 | 1.00 |
| word accuracy (higher better) | **0.014** (9/652) | 0.064 | 0.0009 |

- WER > 1 because the agent emits ~8× too many words → insertions dominate the
  edit distance. WER is therefore uninformative here (it punishes the
  over-segmentation, not the word identities). The cleaner signal is word
  accuracy.
- Word accuracy 0.014 is **above chance (0.0009, ~15×)** but **below the unigram
  baseline (0.064)**. The unigram baseline wins simply because "the" is so
  frequent in LibriSpeech that always-guessing-"the" beats the agent's noisy
  per-chunk guesses.

## (3) VERDICT — honest

**The agent's forward chain does NOT yet recognise continuous speech above the
baselines.** It is above chance but below unigram. The end-to-end pipeline runs
clean (perception → invariance → chunker → grounding → decode → WER), and the
upstream pieces work as built — but the loss is squarely in the
**grounding/lexicon/decoder**, not in perception or the chunker's boundary
logic:

1. **Over-segmentation** (7.71 chunks/word) means the unit the lexicon grounds
   is a sub-word fragment, not a word. The chunker needs to operate at a coarser
   grain (or iterate more passes / merge harder) to emit word-scale chunks
   before grounding is meaningful.
2. **Chunk prototypes don't cluster by word** (purity 0.179). The DTW over
   invariant frame-spans does not pull the same word's chunks together across
   speakers — the merge cap saturates with near-singleton prototypes. A
   word-level representation (pool/normalise the chunk, or cluster at the word
   level after better segmentation) is needed before DTW grounding can build a
   real chunk→word map.

This re-locates the loss precisely: FSDD could not measure it because isolated
digits have no segmentation and a 10-word closed lexicon. On continuous speech
the chain exposes that **the chunker→lexicon junction is where continuous-speech
recognition currently breaks** — the next capability to build is word-scale
chunk formation + word-level clustering, not more perception or invariance work
(those are upstream and intact).

## Notes / reproduction

```
python -m scripts.continuous_speech_recognition [n_train] [n_test] [n_speakers] [K]
# reported run: 120 40 30 48   (~15 min wall, single core)
```

- Held-out = held-out SPEAKERS (the real speaker-independent test).
- Acceptance tests `test_stt_pipeline` + `test_perception_self_assessment` stay
  green (this is a new world-adapter script; it touches no agent code).
- No tuning was done to manufacture a number; the over-segmentation and low
  purity are reported as measured.
- Cost note: the agent's graph-resident invariant transform builds a throwaway
  substrate per utterance (~5 s/utt), which bounds the tractable corpus size.
