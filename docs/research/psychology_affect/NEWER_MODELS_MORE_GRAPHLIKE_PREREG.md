# Newer models are more graph-like — PREREG

**Block**: 306000

**Task**: The user's hypothesis, after the distillation rungs (304000 MiniLM,
305000 gemma3:4b): *"newer models should be MORE graph-like."* Test it with
real numbers by measuring the same graph-likeness metrics across models of
increasing recency:

- **gemma3:4b** (older) — dense transformer, GGUF via ollama.
- **Qwen3-1.7B** (newer) — dense transformer, local HF safetensors.
- **Qwen3.8-27B** (newest, Aug 2026) — `qwen3_5_text` HYBRID architecture
  (Mamba-SSM layers interleaved with full-attention layers via `layer_types` /
  `full_attention_interval`), UNTIED embeddings, 64 layers, vocab 248320.
  Downloaded to `/applications/data/model_graph_work/Qwen3.8-27B` (~54 GB; not
  committed to the repo).

(The user corrected an earlier mistaken "Qwen3" — Qwen3.8 is the current
release; Qwen3 is old. Qwen3-1.7B is kept as a mid-recency point.)

## 1. Hypothesis + why it might be true

A "graph-like" representation packs knowledge into DISCRETE, REUSABLE units
with CRISP relations — the opposite of a diffuse, entangled manifold. Newer
training (more data, better regularisation, cleaner tokenizers, architectural
changes like hybrid SSM/attention and untied embeddings) plausibly pushes
representations toward MORE modular, MORE separable structure. If so, newer
models should distil into a substrate graph MORE cleanly.

This is a falsifiable directional claim, tested on n=3 models — NOT a proof of
a trend, but a measured data point (stated as such in RESULTS).

## 2. Graph-likeness metrics (identical for every model)

All computed over the token-embedding matrix + FFN down-projection, read
statically from the weights (no inference), same working-vocab window, same
seed concepts, same k / bit-depths:

1. **FFN concept alignment + purity** (`ffn_concept_score`): for each seed
   concept, search layers for the FFN value neuron most aligned with the
   concept direction; report its cosine (alignment) and the fraction of its
   top promoted tokens that are themselves on-concept (purity). Higher = the
   model packs a concept into a single clean direction = more graph-like.
   (Concept-neurons localise at different depths per architecture — measured:
   gemma3 mid-stack, Qwen3 late-stack — so the read SEARCHES layers, fairly.)
2. **kNN reciprocity** (`knn_reciprocity`): fraction of directed kNN edges that
   are MUTUAL (i∈kNN(j) ⇔ j∈kNN(i)) over a random vocab sample. Crisp
   reciprocal neighbourhoods = clean graph edges; hub-dominated asymmetric
   neighbourhoods = diffuse. Higher = more graph-like.
3. **Distillation survival** (`distill_survival`): kNN recall@k retained after
   vector quantisation at 8/4/3 bits vs full precision (block-304000
   distillation-fidelity, per model). A more graph-like geometry survives
   compression better. Higher = more graph-like.

## 3. Falsifiable prediction

**Qwen3.8-27B ≥ Qwen3-1.7B ≥ gemma3:4b on the graph-likeness metrics**
(monotone with recency), or — reported honestly — which metrics follow the
order and which do not. Any inversion is reported, not hidden.

Early two-model result (recorded before the newest model landed): Qwen3-1.7B
beats gemma3:4b on ALL FOUR — ffn_alignment 0.327 vs 0.278, ffn_purity 0.975
vs 0.900, knn_reciprocity 0.654 vs 0.585, distill_survival@4-bit 0.963 vs
0.812. The registered question is whether Qwen3.8-27B extends the trend.

## 4. Anti-faking bars

- **Same everything**: identical metric code, working-vocab window, seed
  concepts, k, bit-depths, and RNG seed across models — the only variable is
  the model.
- **Per-metric reporting**: every metric reported for every model, not a
  cherry-picked aggregate; inversions surfaced.
- **Layer search is fair, not tuned**: the FFN read searches a fixed spread of
  layers per model and takes the best — it does not hand-pick a layer that
  flatters one model.
- **Static read, no inference**: metrics are over the weights; no running the
  model (that is 305000's behavioural probing, a different capability).
- **default == today**: NEW metrics in `domains/model_active_extraction.py`
  (pure numpy reads) + a script + docs; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched. The downloaded models live under `/applications`, NOT in the repo.

## 5. Honest bounds

- **n=3 is not a trend.** Three models spanning recency is a directional data
  point, not a law. Confounds (size, tokenizer, training corpus) are NOT
  controlled — a newer model is also bigger/differently-tokenised. The claim
  is "measured more graph-like," not "MORE graph-like BECAUSE newer."
- Metrics are proxies for "graph-like", chosen before measuring; other proxies
  might order the models differently.
- Static geometry only; the deep computational circuit is not measured here.
- Qwen3.8-27B is a hybrid SSM/attention model — only its full-attention/MLP
  layers carry a `down_proj`; the FFN read skips SSM layers (handled as
  missing tensors), which is itself part of the honest picture.
