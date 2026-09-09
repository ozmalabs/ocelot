# Distilling open weights into a substrate graph — transfer — RESULTS

**Block**: 304000. Pre-reg: `WEIGHT_DISTILLATION_TRANSFER_PREREG.md`.
Distiller: `domains/weight_distillation.py`; measure:
`scripts/weight_distillation_measure.py`.

The user's question: *"given this, could we distill open weights into a graph?
— at least partially."* **Verdict: YES for the associative knowledge
geometry; PARTIAL for the compositional circuit.** Measured on the real
`all-MiniLM-L6-v2` open weights, no torch, no inference — the embedding matrix
read straight from the safetensors file and turned into a sparse, lossy
substrate graph.

## What was distilled

`embeddings.word_embeddings.weight` (30522×384, float32) → for each of the
first 8000 tokens, its top-16 cosine neighbours became weighted
`causal_influence` edges. The dense matrix is then DISCARDED — the graph is
all that remains, and every transfer read below traverses graph edges, not the
matrix.

## Measured (seed=0)

| Claim | Result | Verdict |
|---|---|---|
| 1. kNN transfer above chance | graph recall@8 vs model **1.000**, random baseline **0.000** | **HOLDS** |
| 2. analogy transfer, weaker than dense | graph hit@5 **0.71** vs dense **1.00** vs random **0.00** | **HOLDS** (partial) |
| 3. graceful degradation (lossy dial) | 8b **0.994** → 4b **0.781** → 3b **0.600** → 2b **0.000** | **HOLDS** (with a ~3-bit floor) |

### Claim 1 — the knowledge geometry distils cleanly
The distilled graph's neighbours recover the model's OWN top-8 cosine
neighbours at recall 1.000 across 20 probes (king, dog, water, car, music,
river, …), versus 0.000 for a random graph of the same degree. The
associative geometry — what-is-near-what — transfers weight→graph essentially
losslessly at this sparsification.

**Honest caveat**: at k=16 the graph stores the top-16, which CONTAINS the
model's top-8, so recall@8 is near-tautological — this measures that the
geometry is PRESENT in the graph, not that a lossy graph reconstructs it. The
real lossy test is Claim 3.

### Claim 2 — compositional analogy transfers only partially
Graph analogy (`b_neighbours − a_neighbours` set-direction spread from `c`, a
purely structural read — NO vector subtraction on the matrix) hits the target
in top-5 on **5/7** battery items, versus the dense `b − a + c` ground truth's
**7/7** and a random baseline of **0/7**. It is genuinely above chance AND
genuinely weaker than dense. It captured the directional relations
(gender, plural, capital) and missed the COMPOSITIONAL one (royal+gender:
man:king::woman → women/female, not queen). This is exactly block 303000's
boundary: the discrete/structural graph read loses the graded composition that
the continuous field (or dense vector) preserves.

### Claim 3 — distillation fidelity is a dial with a floor
Quantising the embedding VECTORS before computing neighbours (the real cost of
"compress the weights into the graph") degrades recall@8 vs the full model
smoothly: 8-bit 0.994, 4-bit 0.781, 3-bit 0.600 — then a floor collapse to
0.000 at 2-bit and 1-bit. Above ~3 bits/dim the geometry survives and degrades
gracefully; below it the vectors can no longer distinguish neighbours at all.
Reported honestly: it is a graceful dial in the 3–8 bit range with a hard
resolution floor below 3 bits, NOT graceful all the way down.

## Verdict on the user's question

**Distilling open weights into a graph works — partially, exactly as the user
framed it.**
- The associative KNOWLEDGE GEOMETRY (embeddings → kNN graph) distils cleanly,
  mechanically, from the open weights, with no inference and no retraining.
  This is a large slice of what a small model "knows".
- The COMPOSITIONAL CIRCUIT (vector analogy, and by extension the deep
  multi-layer function) transfers only PARTIALLY under the discrete graph read
  — the same grain boundary block 303000 measured. It would need the
  continuous field read to recover the graded composition (a named follow-on).
- Fidelity is a DIAL (vector precision), with a ~3-bit floor — consistent with
  the scaling-projection story: coverage is cheap and lossy-compressible;
  quality is bounded by resolution.

This connects the whole arc: interpolation is a grain (303000), and now the
GEOMETRY that interpolation runs over can itself be distilled out of real open
weights into the graph (304000). The substrate can absorb an open model's word
knowledge additively, no retrain — and the honest bound is that the deep
compositional circuit is only partially captured by the discrete structural
read.

## Anti-faking bars — all honoured
- **Graph-not-matrix at test time**: `DistilledGraph` does not retain the
  dense matrix; the transfer reads (`graph_knn`, `graph_analogy`) traverse
  edges only. The matrix is used ONLY to compute the ground truth the graph is
  SCORED against.
- **Lossy by construction**: sparsified (top-k) + quantised; Claim 3 shows the
  real information loss under vector quantisation.
- **Chance baseline**: every transfer number is reported against a
  random-graph / random-token baseline.
- **Held-out probes** independent of the distilled window; OOV probes dropped
  explicitly, not silently.
- **default == today**: a NEW module + script + docs; numpy for the cosine
  math (reading weights), NOT an inference engine. `.so` md5 stays
  `7efe75eba05b006cafd15dbb4b7da246`; protected CAN-internals / toolbox
  untouched.

## Honest scope
- MiniLM is a sentence-encoder embedding, not a full generative LM; this
  distils its WORD GEOMETRY (the graph-shaped piece). The deep generative
  circuit is NOT claimed to distil into one graph.
- 8000-token frequency window, a demonstration scale, not the full 30522 vocab
  or a 10⁹-parameter model.
- Graph analogy is a lossy structural analogue of dense analogy; the gap IS
  the measurement, not a bug.
