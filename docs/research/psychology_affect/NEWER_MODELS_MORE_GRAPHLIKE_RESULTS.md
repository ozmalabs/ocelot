# Newer models are more graph-like — RESULTS

**Block**: 306000. Pre-reg: `NEWER_MODELS_MORE_GRAPHLIKE_PREREG.md`.
Build/measure: `domains/model_active_extraction.py` (metrics),
`scripts/newer_models_graphlike_measure.py`.

The user's hypothesis: *"newer models should be MORE graph-like."*
**Verdict: PARTLY TRUE, then FALSIFIED at the frontier — and the failure is
the interesting part.** The naive trend holds from gemma3:4b → Qwen3-1.7B but
BREAKS at Qwen3.8-27B, for reasons that are confounds (size, untied
embeddings, outlier features), not recency.

## Measured (work_vocab=15000, seed=0, identical metrics per model)

| Metric | gemma3:4b (older, tied) | Qwen3-1.7B (mid, tied) | Qwen3.8-27B (newest, untied, 27B, hybrid) |
|---|---|---|---|
| FFN concept alignment | 0.26 | 0.30 | 0.06* |
| FFN concept purity | 0.88 | 0.88 | 0.10* |
| kNN reciprocity | 0.585 | 0.654 | 0.575 |
| distill survival @8-bit | 0.975 | 0.988 | 0.963 |
| distill survival @4-bit | 0.812 | **0.963** | **0.087** |
| distill survival @3-bit | 0.775 | 0.887 | 0.05 |

\* FFN metric for Qwen3.8-27B is CONFOUNDED (untied embeddings) — see below.

## What holds, what fails, and why (honest)

**gemma3:4b → Qwen3-1.7B: hypothesis HOLDS on all metrics.** The newer model
has crisper reciprocal neighbourhoods (0.654 vs 0.585) and its geometry
survives aggressive compression far better (4-bit 0.963 vs 0.812). Within the
same tied-embedding, similar-tokenizer regime, newer IS measurably more
graph-like.

**Qwen3.8-27B: hypothesis FALSIFIED — but the causes are confounds, not
recency:**

1. **FFN metric is not a clean cross-model comparison.** gemma3 and Qwen3-1.7B
   have TIED embeddings (input = output space), so projecting an FFN neuron
   through the input embedding names the tokens it promotes. Qwen3.8-27B has
   an UNTIED `lm_head` — the neuron writes into the space read by `lm_head`,
   NOT the input embedding. When corrected to project through `lm_head`, the
   promoted tokens DID become sensible (layer-20 neuron → dogs/dog/Dog), but
   the ALIGNMENT scalar stays low because it still measures against an
   input-embedding concept direction. So the 0.06/0.10 are a
   metric–architecture mismatch, not evidence the model lacks concept-neurons.
   Reported as confounded, not as a real deficit.

2. **The 4-bit distillation COLLAPSE (0.087) is REAL and diagnostic.**
   Qwen3.8-27B's embedding row-norms span min 0.001 to mean 0.899 with a heavy
   tail — the emergent OUTLIER-FEATURE phenomenon well-documented in large
   models. A single uniform quantiser across that range destroys the
   small-norm tokens' geometry, so naive vector quantisation collapses. This
   is a genuine property: **bigger models concentrate information in outlier
   dimensions that naive graph distillation does not survive.** It is a
   SIZE/scale effect, not a recency effect.

3. **kNN reciprocity (0.575) is also slightly lower** than both smaller models
   — the 27B geometry is higher-dimensional (5120-d) and its neighbourhoods
   are less mutually-crisp at a fixed k.

## The real finding (better than a confirmation)

"Newer = more graph-like" is **true within a controlled regime** (same
embedding-tying, similar era/tokenizer: gemma3 → Qwen3-1.7B) and **dominated
by confounds at the frontier**. The variables that actually move
graph-likeness are:
- **embedding tying** (tied → the FFN-concept read works directly; untied →
  needs the `lm_head` projection),
- **model size / outlier features** (bigger → wider norm distribution → naive
  uniform quantisation collapses; would need per-channel / outlier-aware
  quantisation to distil cleanly),
- and only THEN recency.

So the honest answer to the user: newer models CAN be more graph-like, and the
mid-size newer model clearly was — but "newer" is not the operative variable;
**tying and scale-driven outlier structure are.** A frontier model is not
automatically more naively-distillable; it needs outlier-aware distillation to
recover the geometry the smaller model gives for free.

## Anti-faking / method
- Identical metric code, working-vocab window, seed concepts, k, bit-depths,
  RNG seed across all three models — only the model varies.
- Every metric reported for every model; the Qwen3.8 FFN confound is disclosed,
  not hidden, and the geometry-only metrics (kNN reciprocity, distill survival)
  — which have NO tied/untied confound — carry the load of the verdict.
- Static reads only (no inference); numpy for the weight math.
- **default == today**: NEW metrics + script + docs; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched. Downloaded models live under `/applications/data/model_graph_work`
  (Qwen3-1.7B ~3.4 GB, Qwen3.8-27B ~51 GB) and are NOT committed to the repo.

## Honest bounds
- **n=3, confounded.** Size, tokenizer, embedding-tying, and architecture all
  vary with "recency" — this cannot isolate recency as the cause, and the
  results show the confounds dominate. A clean test would fix size + tying and
  vary only training date (not available here).
- The FFN-concept metric needs an untied-aware alignment (project the concept
  direction through `lm_head` too) for a fair frontier comparison — a named
  fix, noted not fully built.
- The 4-bit collapse says naive uniform quantisation fails on outlier-heavy
  large models; outlier-aware quantisation (a known technique) would likely
  restore survival — a named follow-on.
- Graph-likeness is measured by three chosen proxies; other proxies could
  order the models differently.
