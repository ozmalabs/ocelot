# Distilling open weights into a substrate graph — transfer — PREREG

**Block**: 304000

**Task**: The user's question — *"given this, could we distill open weights
into a graph? — at least partially."* and *"yes, do that."* — the natural test
after INTERPOLATION_IS_GRAIN (block 303000) showed interpolation is a grain on
the same field read. If a model's knowledge is graph-shaped geometry, we
should be able to distil it OUT of the open weights INTO a substrate graph and
measure how much CAPABILITY transfers — not just structure.

This registers that falsifiable transfer test.

## 1. What is distilled, and why it is honest

The model's token EMBEDDING matrix is its native word geometry — each row a
token's vector, the geometry IS its language knowledge (`domains.model_reader`
reads it straight from the safetensors file: no torch, no transformers, no
inference engine). We turn that DENSE geometry into a SPARSE, LOSSY graph
(`domains.weight_distillation`):

- for each distilled token, keep its top-`k` cosine neighbours;
- weight each edge by the cosine ROUNDED to a quantum `quant`;
- **DISCARD the dense matrix** — the `DistilledGraph` does not retain it.

The graph is therefore strictly LESS information than the matrix (sparsified +
quantised). Transfer is a real test, NOT an identity: the substrate reads the
GRAPH at test time, never the matrix.

Source for this rung: `all-MiniLM-L6-v2` (`embeddings.word_embeddings.weight`,
30522×384) — a real open-weight sentence encoder present on disk. Distilling a
larger causal LM is the same mechanism (a bigger matrix); MiniLM is what is
locally available.

## 2. The substrate's read over the distilled graph

- **kNN**: `graph_knn(token)` = the token's graph edges only.
- **Analogy** `a:b :: c:?`: `graph_analogy` = a two-hop spreading read from
  `c` (the substrate's convergent-field style) boosted by the SET direction
  `neighbours(b) − neighbours(a)` — a LOSSY structural analogue of the dense
  `b − a + c`, using graph structure, NOT a vector subtraction on the matrix.
  It is EXPECTED to be weaker than dense analogy; that gap is the measurement.

This ties directly to block 303000: the graph read is the discrete/structural
grain; a continuous field read over the same edges is the finer grain. Weaker
analogy transfer under the discrete set-structure read is the same
"discrete-commit loses the gradient" boundary, now on distilled weights.

## 3. Falsifiable claims

1. **kNN transfer above chance**: for a held-out probe set of tokens, the
   distilled graph's neighbours OVERLAP the model's own top-N cosine
   neighbours far above the chance overlap of random tokens. Report
   recall@N (graph-vs-model) and the random-baseline overlap.
2. **Analogy transfer above chance**: on a standard analogy battery
   (gender/plural/capital-style), `graph_analogy` hits the target in top-N
   above the random baseline — but (registered prediction, from the smoke
   test) MEASURABLY WEAKER than dense vector analogy, and weakest on
   COMPOSITIONAL relations (royal+gender) vs simple directional ones (gender).
3. **Graceful degradation (degree, not cliff)**: sweeping the sparsification
   `k` (fewer edges = more lossy), kNN transfer declines SMOOTHLY and
   monotonically — no catastrophic cliff. Distillation fidelity is a dial, not
   a threshold.

Each reported with its measured number; failures reported as failures.

## 4. Anti-faking bars

- **Graph-not-matrix at test time**: the `DistilledGraph` does not store the
  dense matrix; the test-time reads (`graph_knn`, `graph_analogy`,
  `materialise` + substrate reads) traverse edges only. A source/structure
  check asserts the matrix is not consulted after distillation.
- **Lossy by construction**: sparsified (top-k) + quantised (rounded cosine).
  If transfer were perfect it would mean the graph = matrix, which it is not.
- **Held-out probe set**: the analogy/kNN probes are chosen independently of
  the distillation (which distils a fixed frequency window); report which
  probes are OOV to the distilled vocabulary rather than silently dropping
  them.
- **Chance baseline**: every transfer number is reported against the overlap a
  RANDOM graph of the same degree would score, so "above chance" is measured,
  not asserted.
- **default == today**: a NEW module + script + docs; `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246` (seed+python only, numpy for the matrix
  math, no Rust). Protected CAN-internals / toolbox untouched.

## 5. What a positive / negative result means

- **kNN transfers, analogy transfers weakly, degradation graceful** → the
  associative KNOWLEDGE GEOMETRY distils cleanly weight→graph (supports "yes,
  partially"); the compositional circuit degrades under the discrete graph
  read — the honest partial the user named.
- **kNN does NOT transfer above chance** → distillation-into-a-graph does not
  preserve the model's geometry; the claim fails and is reported failed.

## 6. Scope / honesty

- MiniLM is a sentence-encoder embedding, not a full generative LM; this
  distils its WORD GEOMETRY, the piece that IS graph-shaped. The deep
  multi-layer generative circuit is NOT claimed to distil into one graph
  (block 303000's residual ceiling: graph density + reach) — stated plainly.
- numpy is used for the distillation-time cosine math (reading the open
  weights); it is not an inference engine and does not run the model.
- The distilled graph covers a frequency window (default 8000 tokens), a
  demonstration scale, not the full 30522 vocab.
