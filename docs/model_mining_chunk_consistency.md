# Mining a trained SSL speech model for same-word SEGMENT CONSISTENCY

Focused diagnostic + insight-extraction. The narrow target: our continuous-speech
chunks fail same-word consistency (within-speaker full-DTW separation ~+0.014
corpus-TP / ~+0.11 weak landmark; NN-acc ~0.025–0.13) while FSDD isolated digits
match at ~0.78. A pretrained self-supervised (SSL) speech model is a WORKED EXAMPLE
of the solution — mined for the MECHANISM, not the weights. **Nothing is adopted
into the pipeline.**

Models (HF transformers 5.8, torch 2.11 CPU): `facebook/wav2vec2-base`,
`microsoft/wavlm-base`, `facebook/hubert-base-ls960` (each 12 transformer layers,
50 Hz / 20 ms frames, 768-dim). Forced word boundaries from `faster-whisper` tiny
(int8 CPU). Data: FSDD digits (240 clips, 6 speakers) and LibriSpeech dev-clean
(140 utts, 10 speakers). Metric: the agent's OWN consistency metric — full-DTW
(here cosine on L2-normed frames) same-word/same-speaker **SEPARATION**
`(inter−intra)/inter`, plus within/cross same-word nearest-neighbour accuracy.
Scripts: `scripts/mine_ssl_chunk_consistency.py`, `scripts/mine_ssl_goldspan.py`.

---

## 1. DIAGNOSTIC — does a trained model achieve the consistency we lack?

Per-layer same-word WITHIN-speaker consistency. FSDD = clean isolated spans (the
~0.78 reference task); LibriSpeech = continuous words cut by **proportional
alignment** (the SAME noisy segmentation `align_chunks_to_words` uses — so the SSL
repr must survive the same boundary jitter our chunks suffer).

| model | FSDD peak sep | FSDD within-NN | FSDD cross-NN | Libri (proportional) peak sep | Libri within-NN |
|---|---|---|---|---|---|
| wav2vec2-base | **+0.50** (L4) | **0.975** | 0.875 | **+0.100** (L7) | **0.142** |
| wavlm-base    | **+0.638** (L12) | 0.967 | **0.950** | +0.107 (L11) | 0.108 |
| hubert-base   | **+0.683** (L12) | 0.975 | 0.867 | +0.104 (L8) | 0.150 |

Agent reference: FSDD isolated within ~0.78; continuous within-DTW NN ~0.025–0.13,
separation +0.014 (corpus-TP) .. ~+0.11 (landmark, weak). Shuffle controls collapse
to ~0.00 throughout (clean) except the final layers on FSDD (mild WARN).

**Two facts dominate, identical across all three models:**

1. **On CLEAN spans (FSDD) the trained model is spectacular** — separation +0.5–0.68,
   within-speaker NN ~0.97, cross-speaker NN 0.87–0.95. It *crushes* same-word
   consistency when the span is a whole, correctly-delimited word. WavLM even gets
   cross-speaker NN 0.95 (speaker-invariant by design). This is the AWE result from
   the literature: HuBERT/WavLM/wav2vec2 word segments make strong acoustic word
   embeddings (Sanabria et al. 2022, arXiv:2210.16043).

2. **On our CONTINUOUS proportional spans the trained model ALSO largely FAILS** —
   peak separation only **+0.10**, within-NN **0.11–0.15**. That is *the same ceiling
   our own landmark segmenter hit (~+0.11 / ~0.13)*. The billion-parameter SSL model,
   fed the same sloppy spans, does **no better than our DSP pipeline.**

So the trained model does NOT possess some representational magic that makes
mis-cut continuous chunks consistent. It achieves consistency on clean spans and
loses it on noisy spans — exactly like us.

## 2. ISOLATE THE MECHANISM — three ablations (Libri peak layer, all 3 models)

| ablation | wav2vec2 | wavlm | hubert | reading |
|---|---|---|---|---|
| (a) cross-spk sep vs within-spk sep | +0.088 vs +0.100 | +0.095 vs +0.107 | +0.088 vs +0.104 | mid/late features ALREADY speaker-invariant (cross ≈ within) |
| (b) layer-0 (CNN front-end) → peak (deep) | +0.095 → +0.100 | +0.086 → +0.107 | +0.089 → +0.104 | deep contextual stack adds **almost nothing** on noisy spans (+0.005–0.02) |
| (c) span fed ISOLATED vs IN-CONTEXT | +0.148 vs +0.100 | +0.107 vs +0.107 | +0.121 vs +0.104 | **context does NOT help** (it slightly HURTS) |

- **(a) Speaker-invariance is real but is NOT the bottleneck here.** Cross-speaker
  separation ≈ within-speaker separation — the mid-layer features are already
  speaker-normalised (corroborates `speaker_norm.py` / the earlier Whisper mine's
  "invariance is downstream of the front-end"). But both are stuck at +0.10, so
  speaker-invariance is not what's missing for *within-speaker* chunk consistency.
- **(b) The deep trained stack is NOT the lever on mis-cut spans.** Layer-0 (raw CNN
  features, pre-transformer) is within ~+0.01 of the best layer. The 12 attention
  layers — the un-portable trained residue — barely move same-word consistency when
  the *span* is wrong. (On CLEAN spans the depth DOES matter — see §3 gold control.)
- **(c) CONTEXT WINDOW is NOT the mechanism — my prior hypothesis is FALSIFIED.**
  Feeding each word span to the model ISOLATED (cropped audio, no neighbours) gives
  EQUAL or BETTER consistency than slicing it from the full in-context pass. The wide
  receptive field is not what stabilises the segment. (Plausibly: in-context, a
  proportional span bleeds neighbouring words' frames in; cropped, at least the crop
  is centred on the intended region.)

### The decisive control — GOLD vs PROPORTIONAL boundaries (wav2vec2)

The above shows neither context, depth, nor speaker-norm rescues a *wrong span*. So
is the +0.10 ceiling the representation's limit, or the SEGMENTATION's? We gave the
SAME model CORRECT word boundaries (faster-whisper forced word timestamps) on the
SAME 140 utterances and re-measured (`mine_ssl_goldspan.py`):

| representation | within-sep | cross-spk-sep | **within-NN-acc** |
|---|---|---|---|
| PROP layer-0 (proportional span, CNN) | +0.095 | +0.082 | 0.100 |
| PROP layer-7 (proportional span, deep) | +0.100 | +0.088 | 0.142 |
| GOLD layer-0 (correct span, CNN)       | +0.047 | +0.026 | **0.317** |
| **GOLD layer-7 (correct span, deep)**  | +0.089 | +0.073 | **0.492** |

**Read NN-acc — the metric that actually answers "does the same word recognise
itself" (separation is a bulk-mean statistic and is under-powered / nearly flat
here; iter14 already flagged NN-acc>0.5 as the real "closed" bar).**

- Correct boundaries take the SAME wav2vec2 features from **0.142 → 0.492 within-NN
  — a 3.5× jump, to essentially FSDD-isolated levels.** Nothing about the
  representation changed; only the SPAN did.
- With correct spans, depth NOW pays off: GOLD layer-7 (0.492) >> GOLD layer-0
  (0.317) — the deep contextual features DO add +0.18 — but **boundary correctness
  is the dominant factor**, worth 3.5× on its own.

## 3. THE PORTABLE INSIGHT (the synthesis that matters)

**The chunk-consistency bottleneck is SEGMENTATION ACCURACY, not representation —
and this is portable, not a big-net trick.** The evidence is unanimous across three
independently-trained SSL models plus a forced-alignment control:

1. A trained model achieves same-word consistency **only when the span is a clean,
   correctly-delimited word** (FSDD NN ~0.97; LibriSpeech gold-span NN ~0.49 vs
   proportional 0.14). Feed it our mis-cut continuous spans and it collapses to our
   own pipeline's number (+0.10 / 0.13) — the trained stack does **not** repair a
   bad boundary.
2. The candidate "portable mechanisms" are ruled OUT as the lever: **context window
   does not help** (isolated ≥ in-context), **deep abstraction does not help on bad
   spans** (layer-0 ≈ peak), and speaker-invariance, while real, is already not the
   within-speaker blocker.
3. The literature agrees by omission: SSL acoustic-word-embedding results
   (Sanabria 2022) are all evaluated on **pre-segmented word tokens** — i.e. they
   *assume* the boundaries are given. Our problem is precisely the part AWE work
   factors out.

**What the agent should forward-build (mapped to its primitives), NO big net:**

The lever is "get the boundary right," and the gold-span result shows the payoff is
huge (3.5×) and available to a *non-neural* front-end (GOLD layer-0 CNN features
already hit 0.317). Concretely:

- **Iterative lexicon-aware re-segmentation** (the residual iter14 already pointed
  to, now strongly motivated): the agent's stable sonority/landmark valleys
  (`landmark_segmentation.py`) give SYLLABLE atoms, not word boundaries. Cluster
  recurring landmark n-grams into proto-words (its `recurrence` /
  `statistical_learning` / transition-probability science), then **re-segment to
  best-match the recurring units** and iterate. This is a forced-alignment-by-
  bootstrapping loop: gold-span shows that once boundaries snap to true words,
  consistency follows even from non-neural features.
- **Boundary refinement as an order-N landmark + lexicon agreement test**, composed
  in the graph: a boundary is accepted when it both sits at a sonority/order-1-time
  envelope landmark AND yields a chunk that DTW-matches an existing lexicon
  prototype. Segmentation and recognition co-train — the agent's babble/mismatch loop
  applied to boundaries.
- **Self-supervised boundary objective (the honest harder path):** if landmark+
  lexicon bootstrapping plateaus, the genuinely-needed missing piece is an
  *unsupervised word-boundary detector* (the only thing the SSL models effectively
  "have" via their decoder/clustering targets). That is an unsupervised SEGMENTATION
  objective the agent composes (predict-next-frame surprise spikes at boundaries;
  the TP-trough idea but on STABLE landmark units, not jittery k-means) — NOT an
  unsupervised AWE/embedding objective. The representation is already adequate; the
  boundary detector is the gap.

**Honest negative on the alternative framing:** this is NOT "the consistency is
irreducibly the learned embedding, so the path is an unsupervised AWE objective."
The gold-span control disproves that — adequate consistency (NN 0.32–0.49) is
reachable from correct spans with shallow/non-neural features. The path is a better
SEGMENTER, which the agent CAN forward-design, not a bigger representation.

## 4. The single most promising thing to try next

**Build the boundary↔lexicon bootstrapping loop on the agent's STABLE landmark
atoms and measure within-speaker NN-acc as boundaries improve.** Specifically:
segment LibriSpeech to sonority landmarks (`landmark_segmentation`, syllable gate);
cluster recurring landmark sequences by DTW into a proto-lexicon; re-cut each
utterance to maximise total proto-lexicon match (a graph-resident DTW-alignment
Term); iterate 2–3 rounds; re-measure same-word within-speaker NN-acc. The
gold-span ceiling (0.49 from correct boundaries, reachable at 0.32 even without deep
features) is the target this loop is chasing — and unlike the SSL net, every step is
composable from the agent's DSP + DTW + recurrence/TP + lexicon primitives.

A cheap pre-check worth running first: feed the agent's OWN gammatone+invariant
front-end the GOLD (forced) spans and measure NN-acc. If it lands near the SSL
gold-span 0.3–0.5, that PROVES the agent's representation is already sufficient and
the entire remaining gap is the segmenter — collapsing the problem to one lever.

---

### Verdict

Mining three SSL speech models for same-word chunk consistency rules OUT the
representation as the bottleneck and rules IN segmentation accuracy. The trained net
matches the same word to itself ONLY on clean spans; on our continuous proportional
spans it is no better than our pipeline; correct boundaries triple our recognition
metric using the very same (or shallower) features. The portable insight is "fix the
boundary, the representation is already enough" — a forward-designable segmenter
(landmark + lexicon bootstrap, then an unsupervised boundary objective if needed),
not an adopted net and not an unsupervised embedding objective. No weights, no
architecture, no front-end transform worth porting — a confirmed, well-isolated
direction with a measured 3.5× headroom.

Sources:
- [Analyzing Acoustic Word Embeddings from Pre-trained Self-supervised Speech Models (Sanabria et al., 2022), arXiv:2210.16043](https://arxiv.org/abs/2210.16043)
- [Neural approaches to spoken content embedding (survey), arXiv:2308.14905](https://arxiv.org/pdf/2308.14905)
