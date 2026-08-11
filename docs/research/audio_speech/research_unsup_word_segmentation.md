# Research scan: unsupervised word segmentation + acoustic word embeddings

Focused literature scan (2022-2026) on the binding blocker: in **continuous** speech,
the same word must segment to a **consistent** representation so it can be matched/clustered.
Two coupled sub-problems:
- **(a) Unsupervised word segmentation** — placing word boundaries in untranscribed
  continuous speech consistently (same word -> same span each time).
- **(b) Acoustic word embeddings (AWE)** — mapping a variable-length segment to a vector
  where same-word-across-instances/contexts/**speakers** lands close.

Our measured status: TP-trough chunking + energy-envelope-valley (syllable-nucleus)
landmarks give only weak, fragile same-word self-similarity (intra/inter separation ~+0.11,
shuffle-clean but ~11% closer). Isolated-word recognition is solved; continuous chunks
don't match even within one speaker.

**Applicability filter:** we forward-design from primitives — DSP (FFT/filterbank), DTW,
graph Term-trees, finite-difference (order_n) features, analogical transfer,
statistical-learning (TP/recurrence), a small lexicon; **no big pretrained NN** (must run
MCU-class, ~210 KB, no GPU). For each method below the goal is the *algorithmic
mechanism*, not the big-model recipe.

---

## 1. Most relevant recent works/methods

1. **Prominence-based boundary detection on SSL features** — Malan, van Niekerk, Kamper,
   "Unsupervised Word Discovery: Boundary Detection with Clustering vs. Dynamic Programming"
   (2024) and follow-up "Should Top-Down Clustering Affect Boundaries in Unsupervised Word
   Discovery?" (2025). **Core idea:** compute cosine *dissimilarity between adjacent frames*
   of an SSL feature stream, smooth it, place boundaries at **prominence peaks** of that
   dissimilarity curve ("frames within a word are close; frames at boundaries are far").
   Cluster segment-mean embeddings (PCA->K-means/FAISS) to build a lexicon. **Result:**
   matches DP state-of-the-art on 5-language ZeroSpeech while ~5x faster; the simple
   bottom-up boundary method is "good enough" vs top-down clustering feedback.
   2024-2025. (arxiv.org/abs/2409.14486, arxiv.org/html/2507.19204)

2. **DP-Parse** — Algayres et al., TACL (2022). **Core idea:** word segmentation as
   dynamic programming over an **instance lexicon** of word *tokens* (not word *types*),
   avoiding clustering errors; scores spans with a non-parametric-Bayesian-style objective.
   **Result:** new segmentation SOTA on Zero Resource Speech 2017 across 5 languages,
   beating competitors by >=5 points boundary + token F1. 2022.
   (arxiv.org/abs/2206.11332)

3. **DPDP — Duration-Penalized Dynamic Programming** — Kamper; "Revisiting speech
   segmentation and lexicon learning with better features" (2024). **Core idea:** two-stage
   DP that minimizes per-segment reconstruction/centroid distance **plus an explicit
   duration penalty** `-lambda*(b_n - a_n)` to control segment length (lambda=2 phones,
   lambda=5 words). Stage 1 -> phone-like units, stage 2 -> word-like units. **Result:**
   best lexicons (NED) across all 5 ZeroSpeech languages; gains came mostly from better
   features, not the algorithm. 2024 (algorithm older). (arxiv.org/html/2401.17902)

4. **VG-HuBERT — visually-grounded word discovery** — Peng & Harwath, Interspeech (2022).
   **Core idea:** train speech<->image contrastive model; a CLS token's **self-attention
   concentrates on word segments**, yielding boundaries with no text. **Result:** on-par/
   better than prior on Buckeye segmentation + ZeroSpeech term discovery. **Big-model
   dependent** (needs the visually-grounded transformer + paired image data). 2022.
   (arxiv.org/abs/2203.15081)

5. **thetaOscillator — pre-linguistic syllable segmentation** — Rasanen, Doyle & Frank,
   *Cognition* 171:130-150 (2018), maintained/used through 2023-24. **Core idea:** pure DSP
   + a damped **theta-band (4-8 Hz) oscillator entrained to the speech amplitude envelope**;
   syllable nuclei/boundaries fall out of oscillator phase. Pipeline: gammatone filterbank
   -> per-band envelope -> sum across bands (sonority) -> drive oscillator -> read boundaries
   from phase. Language-independent, **no training, no NN**. Strong baseline for syllable
   units; words are built from syllables. (github.com/orasanen/thetaOscillator;
   sciencedirect.com/science/article/abs/pii/S0010027717302901)

6. **SylBoost + LossPred / SyllableLM** — Baade et al., "SyllableLM" (2024); SD-HuBERT
   (Cho et al., 2024). **Core idea:** syllable-like units are a more robust, lower-rate,
   more **speaker-stable** intermediate than phones or raw words; LossPred reads the SSL
   loss curve to seed syllable boundaries, SylBoost refines via self-distillation. SD-HuBERT
   adds explicit **speaker disentanglement** so syllable clusters are speaker-invariant.
   **Result:** SOTA syllabic segmentation/units. Big-model dependent, but the *insight* —
   segment at the **syllable** scale and make units speaker-invariant — is portable. 2024.
   (arxiv.org/html/2410.04029, arxiv.org/pdf/2409.10103)

7. **Correspondence autoencoders / contrastive AWE** — CAE-RNN, MCVAE (Peng et al., 2020),
   ContrastiveRNN (Kamper et al., 2021), Correspondence Transformer Encoder (2023).
   **Core idea:** the AWE objective for same-word-across-speaker invariance: take pairs of
   **different instances of the same word** (from a term-discovery system), and train the
   encoder so their embeddings agree — reconstruct/predict instance B's frames from instance
   A (correspondence loss), or pull same-word pairs together and push different-word pairs
   apart (contrastive/triplet/InfoNCE, tau=0.1). Speaker invariance is **not an explicit
   loss term** — it *emerges* from forcing different realizations of the same word to agree.
   2020-2023. (arxiv.org/abs/2012.02221, ar5iv.org/html/2103.10731)

8. **Reference-vector / Laplacian-eigenmaps AWE** — Levin et al. (2013), foundational and
   still the **model-free** AWE template. **Core idea:** keep a reference set of distinct
   segments; embed any segment as the vector of its **DTW costs to each reference segment**
   (a fixed-length vector). Optionally pass through Laplacian eigenmaps (graph embedding) for
   a smooth low-dim space; that variant matched raw DTW on word discrimination.
   **Fully reproducible with DTW + a graph — no NN.** (pages.stat.wisc.edu/~kdlevin/pubs/)

9. **Park & Glass segmental DTW spoken-term discovery** — (2008), still the backbone of
   unsupervised term discovery. **Core idea:** find recurring word/phrase patterns by
   searching for near-diagonal low-cost paths (matching sub-sequences) in the **DTW
   self-similarity matrix** between/within utterances; cluster the matched fragments into
   pseudo-word types. **No NN.** This is how you *bootstrap* the same-word pairs that the
   AWE objective in (7) needs. (sls.csail.mit.edu/publications/2005/Park_ASRU.pdf)

---

## 2. Portable insights for a forward-designed DSP+DTW+graph pipeline
Ranked by promise for our specific blocker (same-word consistency):

1. **Boundary = prominence peak in a frame-to-frame dissimilarity curve** (from #1). This is
   the single most transferable mechanism and it is exactly an **order_n / contrast**
   operation: the local rate-of-change of the representation across time. It directly
   replaces ad hoc TP-troughs and energy valleys with a principled "representation changes
   fastest at boundaries" cue. We compute it on *our own* feature stream (filterbank/cochlear
   band vector per frame), not HuBERT.

2. **Correspondence/contrastive objective for same-word-across-speaker invariance** (#7).
   The key principle: invariance is not a feature you hand-design, it is **what survives when
   you force different instances of the same word to agree**. Even without an NN we can
   realize the *spirit*: build the lexicon entry as the DTW-**aligned average** of multiple
   discovered instances (template averaging), then the entry is by construction the
   speaker/instance-invariant part. Same-word pairs come from #9.

3. **Self-similarity-matrix / segmental DTW to bootstrap same-word pairs** (#9, #8). Our
   chunks don't match because we never *mine* matches. Segmental DTW over the running feature
   stream finds recurring fragments directly — these become both the candidate lexicon and
   the positive pairs feeding insight #2. This maps cleanly onto our DTW primitive + graph
   (recurrence is already a statistical-learning concept we have).

4. **Segment at the SYLLABLE scale, then compose words from syllables** (#5, #6). Syllable
   nuclei are far more robust/consistent than direct word boundaries (vowel-centered, high
   energy, low variance). The theta-oscillator (#5) is **pure DSP we can build from our
   gammatone/filterbank + a 4-8 Hz oscillator** and needs no training. Consistent syllable
   anchors give a stable coordinate frame; word spans = integer numbers of syllables, which
   sharply constrains the boundary search.

5. **Explicit duration penalty in the segmentation search** (#3). A single hyperparameter
   `-lambda*length` term turns "where are boundaries" into a clean DP objective that prefers
   word-scale spans and resists shattering. Trivial to add to a DTW/DP segmenter; no model.

6. **Reference-vector embedding via DTW-to-a-reference-set** (#8). A fixed-length, NN-free
   AWE: embed each segment as its DTW distances to a small fixed reference set of segments.
   This gives us a vector space (for clustering/matching) built **only from DTW**, and a
   graph (Laplacian-eigenmap) smoothing step is native to our substrate.

7. **Decouple boundaries from clustering** (#1, 2025). Reassuring negative result: top-down
   lexicon feedback barely helps boundary placement. So we can fix the bottom-up boundary
   cue first (insight #1) without waiting on a good lexicon — they are separable problems.

---

## 3. Single most promising lever to try next

**Replace TP-troughs/energy-valleys with a prominence-peak boundary detector on a
frame-to-frame dissimilarity curve computed over our own filterbank feature vectors —
anchored to theta-oscillator syllable nuclei, and with same-word lexicon entries formed by
DTW-aligned averaging of mined recurring fragments.**

Why it beats TP-troughs / energy valleys:
- **TP-troughs** are a *symbolic/statistical* cue over discretized units — they need a clean
  unit stream we don't reliably have, and they fire on within-word phone transitions as
  often as on word boundaries. **Energy valleys** mark syllable rhythm, not lexical
  boundaries (multi-syllable words have internal valleys). Neither uses *how much the
  spectral content changes*. The prominence-of-dissimilarity cue is the field's current
  SOTA boundary signal and is grounded in the right invariant: **a boundary is where the
  representation changes fastest**, which is precisely a finite-difference (order_n) feature
  we already compute. It is a *continuous* cue robust to missing/merged units.
- Anchoring to **syllable nuclei** (theta oscillator) stabilizes the spans (vowel-centered,
  low-variance) so the *same word maps to the same number of syllable anchors each time* —
  attacking consistency at its root rather than tuning a threshold.
- The +0.11 weak separation is a **lexicon-entry** problem too: a single noisy instance is a
  bad template. **DTW-aligned averaging** of multiple mined instances builds the
  speaker/instance-invariant entry (the model-free shadow of the correspondence objective),
  which is what makes same-word land close.

Mapping onto the agent's primitives:
- *Feature stream:* existing gammatone/filterbank band vector per frame.
- *Dissimilarity curve:* cosine (or our distance) between adjacent frame vectors = a
  first-order finite difference -> **order_n feature** over time, Term-tree native.
- *Prominence peak picking:* local-max with a prominence threshold -> graph/DSL ops we have
  (NodesWhere / ArgMax / neighbour comparisons).
- *Syllable anchors:* gammatone -> per-band envelope -> sum (sonority) -> 4-8 Hz oscillator;
  all DSP from FFT/filterbank primitives.
- *Pair mining:* **segmental DTW** over the stream (DTW primitive) -> recurring fragments
  (recurrence = a statistical-learning concept we have).
- *Lexicon entry:* DTW-align instances of a fragment, average -> invariant template.
- *Embedding/matching:* DTW-to-reference-set vector (NN-free AWE) for clustering, optional
  Laplacian-eigenmap smoothing in the graph.
- *Duration prior:* `-lambda*length` penalty in the span DP — one scalar.

This composes entirely from FFT/filterbank + DTW + finite-difference + graph + a small
lexicon. No pretrained net.

---

## 4. Honesty: what needs a big model, and is segmentation "solved"?

**Fundamentally big-model-dependent (NOT directly adoptable):**
- The headline 2024-25 numbers (Buckeye boundary F ~0.84, ZeroSpeech SOTA) all run the
  dissimilarity cue on **HuBERT/wav2vec2 layer-9/12 features**, not raw DSP. The *algorithm*
  (prominence of adjacent-frame distance) is portable; the *feature space* that makes it
  work that well is a large self-supervised transformer trained on hundreds/thousands of
  hours. Our raw-cochlear features will give a noisier dissimilarity curve — the mechanism
  transfers, the absolute scores will not.
- **VG-HuBERT** word discovery (attention-based) is intrinsically a big visually-grounded
  transformer + paired image-speech data. Not adoptable.
- **SD-HuBERT / SyllableLM / SylBoost** speaker-disentangled syllable units depend on the
  SSL backbone + self-distillation. Only the *insights* (syllable scale, speaker-invariant
  units) are portable.
- Correspondence/contrastive **AWE encoders** are NNs. The *objective/principle* is portable
  (force same-word instances to agree); our NN-free surrogate is DTW-aligned template
  averaging + reference-vector embedding, which historically (Levin 2013) is **competitive
  but below** the learned encoders.

**Is unsupervised word segmentation solved? No.** It is an **active, unsolved** problem.
Even with big SSL features, token F1 on ZeroSpeech English remains low (~24%) and NED is
high (~33%); the community explicitly states **clustering/lexicon quality and discriminative
word representations are the limiting factors** and calls them open. The honest expectation
for us: a forward-designed DSP+DTW+graph pipeline can realistically (a) get *more consistent*
boundaries than TP-troughs/energy valleys via the prominence-of-dissimilarity cue, and (b)
get *tighter same-word clustering* via mined-pair template averaging — but it will **not**
reach transformer-feature SOTA in absolute F1. The right success metric mirrors our prior
practice: **improved same-word vs different-word separation that survives shuffle controls,
and within-speaker-then-cross-speaker consistency**, not chasing the ZeroSpeech leaderboard.

---

## Sources
- Malan, van Niekerk, Kamper — Unsupervised Word Discovery: Boundary Detection with
  Clustering vs. Dynamic Programming (2024). https://arxiv.org/abs/2409.14486
- Malan, van Niekerk, Kamper — Should Top-Down Clustering Affect Boundaries in Unsupervised
  Word Discovery? (2025). https://arxiv.org/html/2507.19204
- Algayres et al. — DP-Parse: Finding Word Boundaries from Raw Speech with an Instance
  Lexicon, TACL (2022). https://arxiv.org/abs/2206.11332
- Kamper — Revisiting speech segmentation and lexicon learning with better features (2024)
  [DPDP]. https://arxiv.org/html/2401.17902
- Peng & Harwath — Word Discovery in Visually Grounded, Self-Supervised Speech Models
  [VG-HuBERT], Interspeech (2022). https://arxiv.org/abs/2203.15081
- Rasanen, Doyle & Frank — Pre-linguistic segmentation of speech into syllable-like units,
  Cognition 171 (2018). https://www.sciencedirect.com/science/article/abs/pii/S0010027717302901 ;
  code: https://github.com/orasanen/thetaOscillator
- Baade et al. — SyllableLM: Learning Coarse Semantic Units for Speech Language Models
  (2024). https://arxiv.org/html/2410.04029
- Cho et al. — Self-Supervised Syllable Discovery Based on Speaker-Disentangled HuBERT
  [SD-HuBERT] (2024). https://arxiv.org/pdf/2409.10103
- Peng, Kamper, Livescu — A Correspondence Variational Autoencoder for Unsupervised Acoustic
  Word Embeddings (2020). https://arxiv.org/abs/2012.02221
- Kamper et al. — Acoustic word embeddings for zero-resource languages using self-supervised
  contrastive learning and multilingual adaptation (2021).
  https://ar5iv.labs.arxiv.org/html/2103.10731
- Levin et al. — Fixed-dimensional acoustic embeddings of variable-length segments
  (reference-vector / Laplacian eigenmaps) (2013).
  https://pages.stat.wisc.edu/~kdlevin/pubs/LJV_ICASSP2015.pdf
- Park & Glass — Towards Unsupervised Pattern Discovery in Speech [segmental DTW] (2005/2008).
  https://sls.csail.mit.edu/publications/2005/Park_ASRU.pdf
